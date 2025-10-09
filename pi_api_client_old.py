#!/usr/bin/env python3
"""
Pi API Client for Trading Bot Dashboard
Handles communication with the Pi's trading bot API and database
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
import sqlite3
from contextlib import contextmanager

from config import Config

# Setup logging
logger = logging.getLogger(__name__)


class PiAPIClient:
    """Client for communicating with Pi trading bot API and database"""
    
    def __init__(self):
        self.pi_host = Config.PI_HOST
        self.pi_app_path = Config.PI_APP_PATH
        self.pi_database_path = Config.PI_DATABASE_PATH
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
                text=True,
                timeout=self.timeout + 5
            )
            
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ SSH command timeout: {command}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"💥 SSH command failed: {e}")
            return False, "", str(e)
    
    def get_pi_database_info(self) -> Dict[str, Any]:
        """Get Pi database information"""
        try:
            # Check if database exists
            db_check_cmd = f"test -f {self.pi_database_path}/trading_bot.db && echo 'exists' || echo 'not_found'"
            success, stdout, stderr = self.execute_ssh_command(db_check_cmd)
            
            if not success:
                return {"error": f"Database check failed: {stderr}"}
            
            if "not_found" in stdout:
                return {"error": "Database not found on Pi"}
            
            # Get database size and table info
            db_info_cmd = f"""
            sqlite3 {self.pi_database_path}/trading_bot.db "
            SELECT 
                name as table_name,
                (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
            FROM sqlite_master m 
            WHERE type='table' AND name NOT LIKE 'sqlite_%';
            "
            """
            
            success, stdout, stderr = self.execute_ssh_command(db_info_cmd)
            
            if not success:
                return {"error": f"Database query failed: {stderr}"}
            
            tables = {}
            for line in stdout.strip().split('\n'):
                if line and '|' in line:
                    table_name, row_count = line.split('|')
                    tables[table_name] = int(row_count) if row_count.isdigit() else 0
            
            return {
                "database_exists": True,
                "tables": tables,
                "total_tables": len(tables)
            }
            
        except Exception as e:
            logger.error(f"💥 Database info error: {e}")
            return {"error": str(e)}
    
    def sync_trading_data(self) -> Dict[str, Any]:
        """Sync trading data from Pi database"""
        try:
            logger.info("🔄 Starting Pi database sync...")
            
            if not self.check_pi_connectivity():
                self.sync_status = "pi_offline"
                self.failure_count += 1
                self.last_failure = datetime.now()
                return {"error": "Pi is offline"}
            
            # Get recent trading data
            trading_data = self.get_recent_trades()
            portfolio_data = self.get_portfolio_data()
            equity_data = self.get_equity_data()
            
            if trading_data.get("error") or portfolio_data.get("error") or equity_data.get("error"):
                self.sync_status = "failed"
                self.failure_count += 1
                self.last_failure = datetime.now()
                return {"error": "Data sync failed"}
            
            # Save data locally
            self.save_local_data(trading_data, portfolio_data, equity_data)
            
            self.last_sync = datetime.now()
            self.sync_status = "success"
            self.success_count += 1
            self.last_success = datetime.now()
            
            logger.info("✅ Pi database sync successful")
            return {
                "status": "success",
                "trading_records": len(trading_data.get("data", [])),
                "portfolio_records": len(portfolio_data.get("data", [])),
                "equity_records": len(equity_data.get("data", []))
            }
            
        except Exception as e:
            logger.error(f"💥 Sync error: {e}")
            self.sync_status = "failed"
            self.failure_count += 1
            self.last_failure = datetime.now()
            return {"error": str(e)}
    
    def get_recent_trades(self) -> Dict[str, Any]:
        """Get recent trading data from Pi"""
        try:
            # Query for recent trades (last 24 hours)
            query = f"""
            SELECT 
                timestamp,
                symbol,
                side,
                quantity,
                price,
                pnl,
                status,
                model_id
            FROM trades 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 1000;
            """
            
            success, stdout, stderr = self.execute_ssh_command(
                f"sqlite3 {self.pi_database_path}/trading_bot.db \"{query}\""
            )
            
            if not success:
                return {"error": f"Query failed: {stderr}"}
            
            # Parse CSV-like output
            data = []
            for line in stdout.strip().split('\n'):
                if line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 7:
                        data.append({
                            "timestamp": parts[0],
                            "symbol": parts[1],
                            "side": parts[2],
                            "quantity": float(parts[3]) if parts[3] else 0,
                            "price": float(parts[4]) if parts[4] else 0,
                            "pnl": float(parts[5]) if parts[5] else 0,
                            "status": parts[6],
                            "model_id": parts[7] if len(parts) > 7 else None
                        })
            
            return {"data": data, "count": len(data)}
            
        except Exception as e:
            logger.error(f"💥 Recent trades error: {e}")
            return {"error": str(e)}
    
    def get_portfolio_data(self) -> Dict[str, Any]:
        """Get portfolio data from Pi"""
        try:
            # Query for current portfolio state
            query = f"""
            SELECT 
                timestamp,
                total_balance,
                available_balance,
                total_pnl,
                open_positions,
                winning_trades,
                losing_trades,
                win_rate
            FROM portfolio 
            ORDER BY timestamp DESC
            LIMIT 100;
            """
            
            success, stdout, stderr = self.execute_ssh_command(
                f"sqlite3 {self.pi_database_path}/trading_bot.db \"{query}\""
            )
            
            if not success:
                return {"error": f"Query failed: {stderr}"}
            
            # Parse CSV-like output
            data = []
            for line in stdout.strip().split('\n'):
                if line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        data.append({
                            "timestamp": parts[0],
                            "total_balance": float(parts[1]) if parts[1] else 0,
                            "available_balance": float(parts[2]) if parts[2] else 0,
                            "total_pnl": float(parts[3]) if parts[3] else 0,
                            "open_positions": int(parts[4]) if parts[4] else 0,
                            "winning_trades": int(parts[5]) if len(parts) > 5 and parts[5] else 0,
                            "losing_trades": int(parts[6]) if len(parts) > 6 and parts[6] else 0,
                            "win_rate": float(parts[7]) if len(parts) > 7 and parts[7] else 0
                        })
            
            return {"data": data, "count": len(data)}
            
        except Exception as e:
            logger.error(f"💥 Portfolio data error: {e}")
            return {"error": str(e)}
    
    def get_equity_data(self) -> Dict[str, Any]:
        """Get equity curve data from Pi"""
        try:
            # Query for equity curve (last 7 days)
            query = f"""
            SELECT 
                timestamp,
                balance,
                pnl,
                total_trades
            FROM equity_curve 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp ASC;
            """
            
            success, stdout, stderr = self.execute_ssh_command(
                f"sqlite3 {self.pi_database_path}/trading_bot.db \"{query}\""
            )
            
            if not success:
                return {"error": f"Query failed: {stderr}"}
            
            # Parse CSV-like output
            data = []
            for line in stdout.strip().split('\n'):
                if line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        data.append({
                            "timestamp": parts[0],
                            "balance": float(parts[1]) if parts[1] else 0,
                            "pnl": float(parts[2]) if parts[2] else 0,
                            "total_trades": int(parts[3]) if len(parts) > 3 and parts[3] else 0
                        })
            
            return {"data": data, "count": len(data)}
            
        except Exception as e:
            logger.error(f"💥 Equity data error: {e}")
            return {"error": str(e)}
    
    def save_local_data(self, trading_data: Dict, portfolio_data: Dict, equity_data: Dict):
        """Save synced data to local CSV files"""
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Save trading data
            if trading_data.get("data"):
                df_trades = pd.DataFrame(trading_data["data"])
                df_trades.to_csv(data_dir / "trades_summary.csv", index=False)
                logger.info(f"💾 Saved {len(df_trades)} trading records")
            
            # Save portfolio data
            if portfolio_data.get("data"):
                df_portfolio = pd.DataFrame(portfolio_data["data"])
                df_portfolio.to_csv(data_dir / "portfolio.csv", index=False)
                logger.info(f"💾 Saved {len(df_portfolio)} portfolio records")
            
            # Save equity data
            if equity_data.get("data"):
                df_equity = pd.DataFrame(equity_data["data"])
                df_equity.to_csv(data_dir / "equity.csv", index=False)
                logger.info(f"💾 Saved {len(df_equity)} equity records")
                
        except Exception as e:
            logger.error(f"💥 Save local data error: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information"""
        return {
            "status": self.sync_status,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "pi_online": self.check_pi_connectivity(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / (self.success_count + self.failure_count) if (self.success_count + self.failure_count) > 0 else 0,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "pi_host": self.pi_host,
            "pi_app_path": self.pi_app_path
        }
    
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
            
            # Database info
            db_info = self.get_pi_database_info()
            
            # Process info
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
            
            # System info
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
                "status": "healthy" if pi_online and not db_info.get("error") else "degraded",
                "pi_online": pi_online,
                "database": db_info,
                "processes": processes,
                "system": system_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 Pi health check error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
