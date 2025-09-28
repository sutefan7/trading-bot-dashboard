#!/usr/bin/env python3
"""
Development Watcher - Auto-restart the dashboard server on file changes
- Monitors Python, HTML, CSS, and JS files in key directories
- Gracefully restarts the Flask server process when changes are detected
- Uses only Python standard library (no extra dependencies)

Usage:
  python3 dev_watch.py

Notes:
- HTTPS is enabled automatically if ssl/dashboard.crt and ssl/dashboard.key exist.
- Logs directory is ignored to prevent restart loops.
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict

ROOT = Path(__file__).parent
SSL_CERT = ROOT / 'ssl' / 'dashboard.crt'
SSL_KEY = ROOT / 'ssl' / 'dashboard.key'

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
]
IGNORED_DIRS = {'logs', 'backups', '.git', '__pycache__'}
EXTENSIONS = {'.py', '.html', '.js', '.css'}


def log(msg: str) -> None:
    now = datetime.now().strftime('%H:%M:%S')
    print(f"[{now}] {msg}", flush=True)


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


def start_server() -> subprocess.Popen:
    use_https = SSL_CERT.exists() and SSL_KEY.exists()
    cmd = [sys.executable, str(ROOT / 'web_server.py'), '--host', '0.0.0.0', '--port', '5001']
    if use_https:
        cmd.append('--https')
    env = os.environ.copy()
    # Respect existing DEBUG env or default to False
    env.setdefault('DASHBOARD_DEBUG', 'False')
    log(f"Starting server ({'HTTPS' if use_https else 'HTTP'})...")
    proc = subprocess.Popen(cmd)
    return proc


def stop_server(proc: subprocess.Popen) -> None:
    if proc and proc.poll() is None:
        log('Stopping server...')
        try:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                log('Force killing server...')
                proc.kill()
        except Exception:
            pass


def main():
    # Optional: kill any stray web_server.py processes
    try:
        if sys.platform != 'win32':
            subprocess.run(['pkill', '-f', 'web_server.py'], capture_output=True)
    except Exception:
        pass

    prev = snapshot()
    proc = start_server()
    last_restart = time.time()

    try:
        while True:
            time.sleep(1.0)
            curr = snapshot()
            if has_changes(prev, curr):
                # Debounce rapid changes
                if time.time() - last_restart < 0.8:
                    prev = curr
                    continue
                changed_files = [str(p) for p in curr.keys() ^ prev.keys()]
                if not changed_files:
                    changed_files = [str(p) for p in curr.keys() if prev.get(p) != curr.get(p)]
                log(f"Changes detected. Restarting server...")
                stop_server(proc)
                proc = start_server()
                prev = curr
                last_restart = time.time()
            # If server crashed, attempt restart
            if proc.poll() is not None:
                log('Server stopped unexpectedly. Restarting...')
                proc = start_server()
                last_restart = time.time()
    except KeyboardInterrupt:
        log('Exiting watcher...')
    finally:
        stop_server(proc)


if __name__ == '__main__':
    main()
