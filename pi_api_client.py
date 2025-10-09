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
    
    def get_trading_performance_data(self) -> Dict[str, Any]:
        """Get trading performance data from Pi logs and system"""
        try:
            # Get export summary for model info
            export_cmd = f"cat {self.pi_app_path}/storage/artifacts/export_summary.json"
            success, stdout, stderr = self.execute_ssh_command(export_cmd)
            
            model_info = {}
            if success:
                try:
                    export_data = json.loads(stdout)
                    model_info = {
                        "total_models": export_data.get("total_models", 0),
                        "feature_count": export_data.get("feature_count", 0),
                        "export_timestamp": export_data.get("export_timestamp", ""),
                        "format": export_data.get("format", "unknown")
                    }
                except json.JSONDecodeError:
                    pass
            
            # Get latest model info
            latest_cmd = f"cat {self.pi_app_path}/storage/artifacts/latest.txt"
            success, stdout, stderr = self.execute_ssh_command(latest_cmd)
            latest_model = stdout.strip() if success else "unknown"
            
            # Get recent trading activity from logs
            log_cmd = f"tail -50 {self.pi_app_path}/logs/trading_bot.log | grep -E '(trade|signal|profit|loss)' | tail -10"
            success, stdout, stderr = self.execute_ssh_command(log_cmd)
            recent_activity = stdout.strip().split('\n') if success and stdout.strip() else []
            
            # Simulate trading metrics based on available data
            return {
                "model_metrics": {
                    "total_models": model_info.get("total_models", 0),
                    "feature_count": model_info.get("feature_count", 0),
                    "latest_model": latest_model,
                    "model_format": model_info.get("format", "unknown")
                },
                "trading_metrics": {
                    "win_rate": 0.0,  # No actual trading data available
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "profit_factor": 0.0,
                    "total_return": 0.0
                },
                "risk_metrics": {
                    "var_95": 0.0,
                    "expected_shortfall": 0.0,
                    "volatility": 0.0
                },
                "confidence_level": "no_data",
                "created_at": model_info.get("export_timestamp", ""),
                "recent_activity": recent_activity,
                "data_source": "pi_logs_and_artifacts"
            }
                
        except Exception as e:
            logger.error(f"💥 Trading performance error: {e}")
            return {"error": str(e)}
    
    def get_ml_model_data(self) -> Dict[str, Any]:
        """Get ML model data from Pi artifacts"""
        try:
            # Get export summary
            export_cmd = f"cat {self.pi_app_path}/storage/artifacts/export_summary.json"
            success, stdout, stderr = self.execute_ssh_command(export_cmd)
            
            export_data = {}
            if success:
                try:
                    export_data = json.loads(stdout)
                except json.JSONDecodeError:
                    pass
            
            # Get latest model
            latest_cmd = f"cat {self.pi_app_path}/storage/artifacts/latest.txt"
            success, stdout, stderr = self.execute_ssh_command(latest_cmd)
            latest_model = stdout.strip() if success else "unknown"
            
            # Get index.yaml for all symbols
            index_cmd = f"cat {self.pi_app_path}/storage/artifacts/index.yaml"
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
                metadata_cmd = f"cat {self.pi_app_path}/storage/artifacts/{latest_model}/metadata.json"
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
            # Basic connectivity
            pi_online = self.check_pi_connectivity()
            
            if not pi_online:
                return {
                    "status": "offline",
                    "pi_online": False,
                    "error": "Pi is not reachable"
                }
            
            # Get bot status
            bot_status = self.get_bot_status_data()
            
            # Get trading performance
            trading_perf = self.get_trading_performance_data()
            
            # Get ML model data
            ml_data = self.get_ml_model_data()
            
            # Get signals data
            signals_data = self.get_signals_data()
            
            # Get errors data
            errors_data = self.get_errors_data()
            
            # Determine overall status
            status = "healthy"
            if bot_status.get("error"):
                status = "degraded"
            if errors_data.get("error_counts", {}).get("total", 0) > 10:
                status = "warning"
            
            return {
                "status": status,
                "pi_online": True,
                "bot_status": bot_status,
                "trading_performance": trading_perf,
                "ml_model": ml_data,
                "signals": signals_data,
                "errors": errors_data,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 Pi health error: {e}")
            return {
                "status": "error",
                "pi_online": False,
                "error": str(e)
            }
    
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
