#!/usr/bin/env python3
"""
Development Watcher - Auto-restart the dashboard server on file changes
- Monitors Python, HTML, CSS, and JS files in key directories
- Gracefully restarts the Flask server process when changes are detected
- Uses only Python standard library (no extra dependencies)
- PID file management for clean process handling

Usage:
  python3 dev_watch.py

Notes:
- HTTPS is enabled automatically if ssl/dashboard.crt and ssl/dashboard.key exist.
- Logs directory is ignored to prevent restart loops.
- Server process PID is stored for safe cleanup.
"""
import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

ROOT = Path(__file__).parent
SSL_CERT = ROOT / 'ssl' / 'dashboard.crt'
SSL_KEY = ROOT / 'ssl' / 'dashboard.key'
PID_FILE = ROOT / '.dev_watch.pid'
LOG_FILE = ROOT / 'logs' / 'dev_watch.log'

WATCH_DIRS = [
    ROOT / 'templates',
    ROOT / 'static' / 'js',
    ROOT / 'static' / 'css',
]
WATCH_FILES = [
    ROOT / 'web_server.py',
    ROOT / 'data_sync.py',
    ROOT / 'auto_sync.py',
    ROOT / 'backup_system.py',
    ROOT / 'audit_logger.py',
    ROOT / 'config.py',
]
IGNORED_DIRS = {'logs', 'backups', '.git', '__pycache__', 'data', '.venv', 'venv'}
EXTENSIONS = {'.py', '.html', '.js', '.css'}

# Setup logging
LOG_FILE.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def iter_watch_paths():
    for f in WATCH_FILES:
        if f.exists():
            yield f
    for d in WATCH_DIRS:
        if d.exists():
            for p in d.rglob('*'):
                try:
                    if not p.is_file():
                        continue
                    if any(part in IGNORED_DIRS for part in p.parts):
                        continue
                    if p.suffix.lower() in EXTENSIONS:
                        yield p
                except Exception:
                    continue


def snapshot() -> Dict[Path, float]:
    snap: Dict[Path, float] = {}
    for p in iter_watch_paths():
        try:
            snap[p] = p.stat().st_mtime
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return snap


def has_changes(prev: Dict[Path, float], curr: Dict[Path, float]) -> bool:
    if prev.keys() != curr.keys():
        return True
    for p, mtime in curr.items():
        if prev.get(p) != mtime:
            return True
    return False


def kill_existing_server() -> None:
    """Kill any existing server process using PID file"""
    if not PID_FILE.exists():
        return
    
    try:
        pid = int(PID_FILE.read_text().strip())
        logger.info(f"Found existing server process (PID: {pid})")
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid}")
            time.sleep(1)
            # Check if process is still alive
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                logger.warning(f"Process {pid} still alive, sending SIGKILL")
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                logger.info(f"Process {pid} terminated successfully")
        except ProcessLookupError:
            logger.info(f"Process {pid} already terminated")
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"Invalid PID file: {e}")
    finally:
        PID_FILE.unlink(missing_ok=True)


def start_server() -> subprocess.Popen:
    """Start the Flask server process"""
    use_https = SSL_CERT.exists() and SSL_KEY.exists()
    cmd = [sys.executable, str(ROOT / 'web_server.py'), '--host', '0.0.0.0', '--port', '5001']
    if use_https:
        cmd.append('--https')
    
    env = os.environ.copy()
    # Set dev mode environment variables
    if 'DASHBOARD_DEBUG' not in env:
        env['DASHBOARD_DEBUG'] = 'True'  # Dev mode should have debug enabled
    if 'DASHBOARD_ENV' not in env:
        env['DASHBOARD_ENV'] = 'development'
    
    logger.info(f"Starting server ({'HTTPS' if use_https else 'HTTP'})...")
    proc = subprocess.Popen(cmd, env=env)
    
    # Store PID for later cleanup
    PID_FILE.write_text(str(proc.pid))
    logger.info(f"Server started with PID {proc.pid}")
    
    return proc


def stop_server(proc: Optional[subprocess.Popen]) -> None:
    """Stop the server process gracefully"""
    if proc and proc.poll() is None:
        logger.info('Stopping server...')
        try:
            proc.terminate()
            try:
                proc.wait(timeout=8)
                logger.info('Server stopped gracefully')
            except subprocess.TimeoutExpired:
                logger.warning('Server did not stop in time, force killing...')
                proc.kill()
                proc.wait(timeout=2)
                logger.info('Server force killed')
        except Exception as e:
            logger.error(f'Error stopping server: {e}')
    
    # Clean up PID file
    PID_FILE.unlink(missing_ok=True)


def main():
    """Main watcher loop"""
    logger.info("="*60)
    logger.info("🔍 Development Watcher Starting")
    logger.info("="*60)
    logger.info(f"📁 Root: {ROOT}")
    logger.info(f"👀 Watching {len(WATCH_DIRS)} directories and {len(WATCH_FILES)} files")
    logger.info(f"📝 Logs: {LOG_FILE}")
    logger.info(f"🔧 PID File: {PID_FILE}")
    logger.info("="*60)
    
    # Kill any existing server from previous runs
    kill_existing_server()
    
    prev = snapshot()
    proc = start_server()
    last_restart = time.time()
    restart_count = 0

    try:
        logger.info("✅ Watcher active - monitoring for changes (Ctrl+C to stop)")
        while True:
            time.sleep(1.0)
            curr = snapshot()
            
            if has_changes(prev, curr):
                # Debounce rapid changes
                if time.time() - last_restart < 1.5:
                    logger.debug("Change detected but within debounce period, skipping...")
                    prev = curr
                    continue
                
                # Log changed files
                changed_files = [str(p.relative_to(ROOT)) for p in curr.keys() ^ prev.keys()]
                if not changed_files:
                    changed_files = [
                        str(p.relative_to(ROOT)) 
                        for p in curr.keys() 
                        if prev.get(p) != curr.get(p)
                    ]
                
                logger.info(f"📝 Changes detected in {len(changed_files)} file(s):")
                for f in changed_files[:5]:  # Show max 5 files
                    logger.info(f"   • {f}")
                if len(changed_files) > 5:
                    logger.info(f"   ... and {len(changed_files) - 5} more")
                
                logger.info("🔄 Restarting server...")
                stop_server(proc)
                
                # Small delay to ensure port is released
                time.sleep(0.5)
                
                proc = start_server()
                prev = curr
                last_restart = time.time()
                restart_count += 1
                logger.info(f"✅ Server restarted (restart #{restart_count})")
            
            # If server crashed, attempt restart
            if proc.poll() is not None:
                exit_code = proc.poll()
                logger.error(f"❌ Server stopped unexpectedly (exit code: {exit_code})")
                logger.info("🔄 Attempting restart...")
                
                # Small delay before restart
                time.sleep(1.0)
                
                proc = start_server()
                last_restart = time.time()
                restart_count += 1
                
    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*60)
        logger.info("⏹️  Shutdown requested")
        logger.info(f"📊 Total restarts: {restart_count}")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"💥 Fatal error in watcher: {e}", exc_info=True)
    finally:
        logger.info("🛑 Stopping server...")
        stop_server(proc)
        logger.info("✅ Dev watcher stopped")


if __name__ == '__main__':
    main()
