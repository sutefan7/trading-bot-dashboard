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
        """Get trading performance data from Pi artifacts"""
        try:
            # Look for the latest trading performance JSON
            find_cmd = f"find {self.pi_app_path}/storage/artifacts -name 'trading_performance.json' -type f | head -1"
            success, stdout, stderr = self.execute_ssh_command(find_cmd)
            
            if not success or not stdout.strip():
                return {"error": "No trading performance data found"}
            
            json_path = stdout.strip()
            
            # Read the JSON file
            read_cmd = f"cat {json_path}"
            success, stdout, stderr = self.execute_ssh_command(read_cmd)
            
            if not success:
                return {"error": f"Failed to read trading performance: {stderr}"}
            
            try:
                data = json.loads(stdout)
                return {
                    "model_metrics": data.get("model_metrics", {}),
                    "trading_metrics": data.get("estimated_trading_metrics", {}),
                    "risk_metrics": data.get("risk_metrics", {}),
                    "confidence_level": data.get("confidence_level", "unknown"),
                    "created_at": data.get("created_at", ""),
                    "data_source": "pi_artifacts"
                }
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON in trading performance: {e}"}
                
        except Exception as e:
            logger.error(f"💥 Trading performance error: {e}")
            return {"error": str(e)}
    
    def get_ml_model_data(self) -> Dict[str, Any]:
        """Get ML model data from Pi artifacts"""
        try:
            # Look for the latest metadata JSON
            find_cmd = f"find {self.pi_app_path}/storage/artifacts -name 'metadata.json' -type f | head -1"
            success, stdout, stderr = self.execute_ssh_command(find_cmd)
            
            if not success or not stdout.strip():
                return {"error": "No ML model data found"}
            
            json_path = stdout.strip()
            
            # Read the JSON file
            read_cmd = f"cat {json_path}"
            success, stdout, stderr = self.execute_ssh_command(read_cmd)
            
            if not success:
                return {"error": f"Failed to read ML model data: {stderr}"}
            
            try:
                data = json.loads(stdout)
                return {
                    "model_version": data.get("model_version", "unknown"),
                    "symbols": data.get("symbols", []),
                    "train_window": data.get("train_window", ""),
                    "metrics": data.get("metrics", {}),
                    "verified": data.get("verified", False),
                    "created_at": data.get("created_at", ""),
                    "feature_count": data.get("feature_count", 0),
                    "schema_version": data.get("schema_version", "unknown"),
                    "data_source": "pi_artifacts"
                }
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON in ML model data: {e}"}
                
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
