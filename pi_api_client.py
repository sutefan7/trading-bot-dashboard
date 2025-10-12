#!/usr/bin/env python3
"""
Updated Pi API Client for Trading Bot Dashboard
Handles communication with the Pi's trading bot within /srv/trading-bot-pi/app/
"""
import os
import subprocess
import json
import time
import logging
import shlex
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

from config import Config

# Setup logging
logger = logging.getLogger(__name__)


class PiAPIClient:
    """Client for communicating with Pi trading bot within /srv/trading-bot-pi/app/"""
    
    def __init__(self):
        self.pi_host = Config.PI_HOST
        self.pi_app_path = Config.PI_APP_PATH
        self.local_mode = Config.PI_LOCAL_MODE
        self.local_app_path = Config.LOCAL_PI_APP_PATH
        self.timeout = Config.PI_API_TIMEOUT
        self.last_sync = None
        self.sync_status = "unknown"
        self.success_count = 0
        self.failure_count = 0
        self.last_success = None
        self.last_failure = None
    
    def check_pi_connectivity(self) -> bool:
        """Check if Pi is reachable"""
        try:
            if self.local_mode and self.local_app_path.exists():
                logger.info("🔍 Local Pi mode enabled - using local files")
                return True
            pi_ip = self.pi_host.split('@')[1] if '@' in self.pi_host else self.pi_host
            
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "5", pi_ip],
                capture_output=True, 
                timeout=10,
                text=True
            )
            is_online = result.returncode == 0
            logger.info(f"🔍 Pi connectivity check: {'✅ Online' if is_online else '❌ Offline'}")
            return is_online
        except Exception as e:
            logger.error(f"💥 Pi connectivity check failed: {e}")
            return False
    
    def execute_ssh_command(self, command: str) -> tuple[bool, str, str]:
        """Execute SSH command on Pi"""
        try:
            if self.local_mode and self.local_app_path.exists():
                def _resolve_local_path(raw_path: str) -> Path:
                    cleaned = raw_path.strip().strip("'\"")
                    path = Path(cleaned)
                    if path.is_absolute():
                        try:
                            rel = path.relative_to(Path(self.pi_app_path))
                            return self.local_app_path / rel
                        except ValueError:
                            return path
                    return self.local_app_path / path

                try:
                    if command.startswith('cat '):
                        target = command.split('cat ', 1)[1].strip()
                        path = _resolve_local_path(target)
                        if path.exists():
                            return True, path.read_text(encoding='utf-8', errors='ignore'), ''
                        return False, '', 'file not found'
                    if command.startswith('tail'):
                        parts = shlex.split(command)
                        # Default to tail -10 behaviour similar to command line
                        n = 10
                        filep = None
                        for idx, part in enumerate(parts[1:], start=1):
                            if part.startswith('-') and part[1:].isdigit():
                                n = int(part[1:])
                            elif part in {'-n', '--lines'} and idx + 1 < len(parts):
                                try:
                                    n = int(parts[idx + 1])
                                except ValueError:
                                    pass
                            else:
                                filep = part
                        if not filep and parts:
                            filep = parts[-1]
                        if filep:
                            path = _resolve_local_path(filep)
                            if path.exists():
                                lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
                                return True, '\n'.join(lines[-n:]), ''
                            return False, '', 'file not found'
                    return False, '', 'local mode: command not supported'
                except Exception as e:
                    return False, '', str(e)
            full_command = f"ssh -o ConnectTimeout={self.timeout} -o StrictHostKeyChecking=yes {self.pi_host} '{command}'"
            
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                timeout=self.timeout,
                text=True
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"💥 SSH command timeout: {command}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"💥 SSH command error: {e}")
            return False, "", str(e)
    
    def _read_snapshot(self, relative_path: str) -> tuple[bool, dict]:
        """Read a small JSON snapshot from Pi or local copy"""
        try:
            if self.local_mode and self.local_app_path.exists():
                path = self.local_app_path / relative_path
                if path.exists():
                    return True, json.loads(path.read_text(encoding='utf-8', errors='ignore'))
                return False, {}
            success, stdout, stderr = self.execute_ssh_command(f"cat {self.pi_app_path}/{relative_path}")
            if success and stdout.strip():
                return True, json.loads(stdout)
            return False, {}
        except Exception:
            return False, {}

    def _read_jsonl_tail(self, relative_path: str, n: int = 100) -> list[dict]:
        """Read last N JSONL entries from Pi or local copy"""
        try:
            if self.local_mode and self.local_app_path.exists():
                path = self.local_app_path / relative_path
                if not path.exists():
                    return []
                lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()[-n:]
                out = []
                for ln in lines:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        continue
                return out
            success, stdout, stderr = self.execute_ssh_command(f"tail -{n} {self.pi_app_path}/{relative_path}")
            if success and stdout.strip():
                out = []
                for ln in stdout.splitlines():
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        continue
                return out
            return []
        except Exception:
            return []

    def _load_trading_performance_artifact(self) -> Optional[Dict[str, Any]]:
        """Load trading performance metrics from artifacts/logs."""

        def _normalise_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
            trading_metrics = (
                raw.get("estimated_trading_metrics")
                or raw.get("trading_metrics")
                or {}
            )
            risk_metrics = raw.get("risk_metrics", {})
            model_metrics = raw.get("model_metrics", {})

            def _safe_float(value: Any) -> float:
                try:
                    if value is None:
                        return 0.0
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0

            def _safe_int(value: Any) -> int:
                try:
                    if value is None:
                        return 0
                    return int(value)
                except (TypeError, ValueError):
                    return 0

            payload: Dict[str, Any] = {
                "win_rate": _safe_float(
                    trading_metrics.get("win_rate")
                    or trading_metrics.get("winRate")
                    or raw.get("win_rate")
                ),
                "sharpe_ratio": _safe_float(
                    trading_metrics.get("sharpe_ratio")
                    or trading_metrics.get("sharpe")
                    or raw.get("sharpe")
                ),
                "max_drawdown": _safe_float(
                    trading_metrics.get("max_drawdown")
                    or risk_metrics.get("max_drawdown")
                    or raw.get("max_drawdown")
                ),
                "profit_factor": _safe_float(
                    trading_metrics.get("profit_factor")
                    or raw.get("profit_factor")
                ),
                "total_trades": _safe_int(
                    trading_metrics.get("total_trades")
                    or raw.get("total_trades")
                ),
                "data_source": "pi_artifacts",
                "timestamp": raw.get("created_at") or raw.get("timestamp"),
            }

            if model_metrics:
                payload["model_metrics"] = model_metrics
            if trading_metrics:
                payload["trading_metrics"] = trading_metrics
            if risk_metrics:
                payload["risk_metrics"] = risk_metrics
            if raw.get("confidence_level") is not None:
                payload["confidence_level"] = raw.get("confidence_level")

            return payload

        try:
            if self.local_mode and self.local_app_path.exists():
                artifacts_root = self.local_app_path / "storage" / "artifacts"
                if artifacts_root.exists():
                    candidates = sorted(
                        artifacts_root.rglob("trading_performance.json"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    for candidate in candidates:
                        try:
                            raw = json.loads(candidate.read_text(encoding='utf-8', errors='ignore'))
                            if isinstance(raw, dict):
                                return _normalise_payload(raw)
                        except Exception:
                            continue
            else:
                find_cmd = (
                    f"find {self.pi_app_path}/storage/artifacts -name 'trading_performance.json' "
                    "-type f | head -1"
                )
                success, stdout, stderr = self.execute_ssh_command(find_cmd)
                if success and stdout.strip():
                    json_path = stdout.strip()
                    read_cmd = f"cat {json_path}"
                    success, stdout, stderr = self.execute_ssh_command(read_cmd)
                    if success and stdout.strip():
                        try:
                            raw = json.loads(stdout)
                            if isinstance(raw, dict):
                                return _normalise_payload(raw)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON in trading performance artifact")
        except Exception as exc:
            logger.warning(f"Trading performance artifact load failed: {exc}")

        return None

    def get_trading_performance_data(self) -> Dict[str, Any]:
        """Get trading performance data from Pi logs and system"""
        try:
            # Prefer snapshot first
            ok, snap = self._read_snapshot('storage/reports/snapshots/performance_summary.json')
            if ok and snap:
                return {
                    "win_rate": float(snap.get('win_rate', 0.0)),
                    "sharpe_ratio": float(snap.get('sharpe', snap.get('sharpe_ratio', 0.0))),
                    "max_drawdown": float(snap.get('max_drawdown', 0.0)),
                    "profit_factor": float(snap.get('profit_factor', 0.0)),
                    "total_trades": int(snap.get('total_trades', 0)),
                    "data_source": "pi_snapshot",
                    "timestamp": snap.get('ts')
                }

            artifact_payload = self._load_trading_performance_artifact()
            if artifact_payload:
                logger.info("Using artifact-based trading performance metrics")
                return artifact_payload

            return {
                "error": "Trading performance snapshot unavailable",
                "data_source": "pi_snapshot"
            }

        except Exception as e:
            logger.error(f"💥 Trading performance error: {e}")
            return {"error": str(e), "data_source": "pi_snapshot"}
    
    def get_ml_model_data(self) -> Dict[str, Any]:
        """Get ML model data from Pi artifacts"""
        try:
            # Get export summary
            export_cmd = f"cat {self.pi_app_path}/storage/artifacts/export_summary.json" if not self.local_mode else f"cat storage/artifacts/export_summary.json"
            success, stdout, stderr = self.execute_ssh_command(export_cmd)
            
            export_data = {}
            if success:
                try:
                    export_data = json.loads(stdout)
                except json.JSONDecodeError:
                    pass
            
            # Get latest model
            latest_cmd = f"cat {self.pi_app_path}/storage/artifacts/latest.txt" if not self.local_mode else f"cat storage/artifacts/latest.txt"
            success, stdout, stderr = self.execute_ssh_command(latest_cmd)
            latest_model = stdout.strip() if success else "unknown"
            
            # Get index.yaml for all symbols
            index_cmd = f"cat {self.pi_app_path}/storage/artifacts/index.yaml" if not self.local_mode else f"cat storage/artifacts/index.yaml"
            success, stdout, stderr = self.execute_ssh_command(index_cmd)
            symbols = []
            if success:
                # Parse YAML-like content to extract symbols
                for line in stdout.strip().split('\n'):
                    if ':' in line and not line.strip().startswith('models:'):
                        symbol = line.split(':')[0].strip()
                        if symbol:
                            symbols.append(symbol)
            
            # Get latest model metadata
            latest_metadata = {}
            if latest_model != "unknown":
                metadata_cmd = f"cat {self.pi_app_path}/storage/artifacts/{latest_model}/metadata.json" if not self.local_mode else f"cat storage/artifacts/{latest_model}/metadata.json"
                success, stdout, stderr = self.execute_ssh_command(metadata_cmd)
                if success:
                    try:
                        latest_metadata = json.loads(stdout)
                    except json.JSONDecodeError:
                        pass
            
            return {
                "model_version": latest_model,
                "symbols": symbols,
                "train_window": "unknown",  # Not available in current artifacts
                "metrics": {
                    "total_models": export_data.get("total_models", 0),
                    "feature_count": export_data.get("feature_count", 0)
                },
                "verified": True,  # Models are exported, so considered verified
                "created_at": export_data.get("export_timestamp", ""),
                "feature_count": export_data.get("feature_count", 0),
                "schema_version": "1.0",
                "model_type": latest_metadata.get("model_type", "unknown"),
                "coin": latest_metadata.get("coin", "unknown"),
                "format": export_data.get("format", "unknown"),
                "data_source": "pi_artifacts"
            }
                
        except Exception as e:
            logger.error(f"💥 ML model data error: {e}")
            return {"error": str(e)}
    
    def get_bot_status_data(self) -> Dict[str, Any]:
        """Get bot status from Pi logs and processes"""
        try:
            ok, snap = self._read_snapshot('storage/reports/snapshots/bot_status.json')
            if ok and snap:
                return {
                    "pi_online": bool(snap.get('pi_online', True)),
                    "bot_running": bool(snap.get('bot_running', False)),
                    "service_mode": snap.get('service_mode'),
                    "uptime": snap.get('uptime'),
                    "last_decision_at": snap.get('last_decision_at'),
                    "recent_logs": snap.get('recent_logs', []),
                    "last_sync": snap.get('ts'),
                    "data_source": "pi_snapshot",
                    "timestamp": snap.get('ts')
                }
            
            # Check if trading bot process is running
            process_cmd = "ps aux | grep -E 'main_v2_with_ml|trading.*bot' | grep -v grep"
            success, stdout, stderr = self.execute_ssh_command(process_cmd)
            
            processes = []
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 11:
                            processes.append({
                                "pid": parts[1],
                                "cpu": parts[2],
                                "mem": parts[3],
                                "command": " ".join(parts[10:])
                            })
            
            # Get recent log entries
            log_cmd = f"tail -10 {self.pi_app_path}/logs/trading_bot.log"
            success, stdout, stderr = self.execute_ssh_command(log_cmd)
            
            recent_logs = []
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if line:
                        recent_logs.append(line)
            
            # Get system info
            system_cmd = "uptime && free -h && df -h /"
            success, stdout, stderr = self.execute_ssh_command(system_cmd)
            
            system_info = {}
            if success and stdout:
                lines = stdout.strip().split('\n')
                if lines:
                    system_info["uptime"] = lines[0]
                if len(lines) > 1:
                    system_info["memory"] = lines[1]
                if len(lines) > 2:
                    system_info["disk"] = lines[2]
            
            return {
                "pi_online": True,
                "bot_running": len(processes) > 0,
                "processes": processes,
                "recent_logs": recent_logs,
                "system_info": system_info,
                "data_source": "pi_logs"
            }
            
        except Exception as e:
            logger.error(f"💥 Bot status error: {e}")
            return {"error": str(e)}
    
    def get_signals_data(self) -> Dict[str, Any]:
        """Get signals data from Pi logs"""
        try:
            # Read signals log
            signals_cmd = f"tail -20 {self.pi_app_path}/logs/signals.log"
            success, stdout, stderr = self.execute_ssh_command(signals_cmd)
            
            signals = []
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if line:
                        signals.append(line)
            
            # Count signal types
            signal_counts = {
                "total": len(signals),
                "regime_filter": len([s for s in signals if "Regime filter" in s]),
                "trade_logger": len([s for s in signals if "Trade logger" in s]),
                "received_signal": len([s for s in signals if "Received signal" in s])
            }
            
            return {
                "signals": signals,
                "signal_counts": signal_counts,
                "data_source": "pi_signals_log"
            }
            
        except Exception as e:
            logger.error(f"💥 Signals data error: {e}")
            return {"error": str(e)}
    
    def get_errors_data(self) -> Dict[str, Any]:
        """Get errors data from Pi logs"""
        try:
            # Read errors log
            errors_cmd = f"tail -20 {self.pi_app_path}/logs/errors.log"
            success, stdout, stderr = self.execute_ssh_command(errors_cmd)
            
            errors = []
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if line:
                        errors.append(line)
            
            # Count error types
            error_counts = {
                "total": len(errors),
                "data_manager": len([e for e in errors if "data_manager" in e]),
                "scheduler": len([e for e in errors if "scheduler" in e]),
                "historical_data": len([e for e in errors if "historische data" in e])
            }
            
            return {
                "errors": errors,
                "error_counts": error_counts,
                "data_source": "pi_errors_log"
            }
            
        except Exception as e:
            logger.error(f"💥 Errors data error: {e}")
            return {"error": str(e)}
    
    def get_pi_health(self) -> Dict[str, Any]:
        """Get comprehensive Pi health information"""
        try:
            ok_h, health = self._read_snapshot('storage/reports/snapshots/health.json')
            ok_b, bot = self._read_snapshot('storage/reports/snapshots/bot_status.json')
            status = 'healthy'
            if ok_h and isinstance(health, dict):
                if float(health.get('mem_pct', 0)) > 90 or float(health.get('disk_pct', 0)) > 95:
                    status = 'warning'
            return {
                "status": status,
                "pi_online": True,
                "bot_status": bot if ok_b else {},
                "system_performance": health if ok_h else {},
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"💥 Pi health error: {e}")
            return {
                "status": "error",
                "pi_online": False,
                "error": str(e)
            }

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Read portfolio snapshot if available"""
        ok, snap = self._read_snapshot('storage/reports/snapshots/portfolio.json')
        if ok and snap:
            return snap
        return {"error": "no_portfolio_snapshot"}

    def get_equity_24h_snapshot(self) -> Dict[str, Any]:
        """Read equity_24h snapshot if available"""
        ok, snap = self._read_snapshot('storage/reports/snapshots/equity_24h.json')
        if ok and snap:
            return snap
        return {"error": "no_equity_snapshot"}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information"""
        return {
            "status": self.sync_status,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / (self.success_count + self.failure_count) if (self.success_count + self.failure_count) > 0 else 0,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None
        }
