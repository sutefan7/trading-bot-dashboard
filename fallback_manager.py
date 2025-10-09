#!/usr/bin/env python3
"""
Fallback Manager for Trading Bot Dashboard
Provides intelligent fallback mechanisms when Pi is unavailable
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sqlite3
from contextlib import contextmanager

from config import Config

logger = logging.getLogger(__name__)


class FallbackManager:
    """Manages fallback data when Pi is unavailable"""
    
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self.database_path = Config.DATABASE_PATH
        self.fallback_data = {}
        self.last_fallback_update = None
        self.fallback_enabled = True
        
    def is_fallback_needed(self, pi_online: bool, data_age_hours: int = 2) -> bool:
        """Determine if fallback data should be used"""
        if not self.fallback_enabled:
            return False
            
        if pi_online:
            return False
            
        # Check if local data is too old
        if data_age_hours > 0:
            local_files = list(self.data_dir.glob("*.csv"))
            if not local_files:
                return True
                
            newest_file = max(local_files, key=lambda f: f.stat().st_mtime)
            file_age = datetime.now() - datetime.fromtimestamp(newest_file.stat().st_mtime)
            
            if file_age > timedelta(hours=data_age_hours):
                return True
                
        return True
    
    def get_fallback_trading_performance(self) -> Dict[str, Any]:
        """Get fallback trading performance data"""
        try:
            # Try to get data from local CSV files first
            csv_data = self._get_csv_fallback_data()
            if csv_data:
                return csv_data
            
            # Try to get data from local database
            db_data = self._get_database_fallback_data()
            if db_data:
                return db_data
            
            # Use cached fallback data
            if self.fallback_data.get('trading_performance'):
                logger.info("📊 Using cached fallback trading performance data")
                return self.fallback_data['trading_performance']
            
            # Generate demo data as last resort
            return self._generate_demo_trading_data()
            
        except Exception as e:
            logger.error(f"💥 Fallback trading performance error: {e}")
            return self._generate_demo_trading_data()
    
    def get_fallback_portfolio_data(self) -> Dict[str, Any]:
        """Get fallback portfolio data"""
        try:
            # Try to get data from local CSV files first
            csv_data = self._get_csv_portfolio_data()
            if csv_data:
                return csv_data
            
            # Try to get data from local database
            db_data = self._get_database_portfolio_data()
            if db_data:
                return db_data
            
            # Use cached fallback data
            if self.fallback_data.get('portfolio'):
                logger.info("📊 Using cached fallback portfolio data")
                return self.fallback_data['portfolio']
            
            # Generate demo data as last resort
            return self._generate_demo_portfolio_data()
            
        except Exception as e:
            logger.error(f"💥 Fallback portfolio data error: {e}")
            return self._generate_demo_portfolio_data()
    
    def get_fallback_equity_data(self) -> Dict[str, Any]:
        """Get fallback equity curve data"""
        try:
            # Try to get data from local CSV files first
            csv_data = self._get_csv_equity_data()
            if csv_data:
                return csv_data
            
            # Try to get data from local database
            db_data = self._get_database_equity_data()
            if db_data:
                return db_data
            
            # Use cached fallback data
            if self.fallback_data.get('equity'):
                logger.info("📊 Using cached fallback equity data")
                return self.fallback_data['equity']
            
            # Generate demo data as last resort
            return self._generate_demo_equity_data()
            
        except Exception as e:
            logger.error(f"💥 Fallback equity data error: {e}")
            return self._generate_demo_equity_data()
    
    def _get_csv_fallback_data(self) -> Optional[Dict[str, Any]]:
        """Get fallback data from local CSV files"""
        try:
            trades_file = self.data_dir / "trades_summary.csv"
            if not trades_file.exists():
                return None
            
            df = pd.read_csv(trades_file)
            if df.empty:
                return None
            
            # Calculate performance metrics
            total_trades = df.get('total_trades', pd.Series([0])).iloc[-1] if len(df) > 0 else 0
            winning_trades = df.get('winning_trades', pd.Series([0])).iloc[-1] if len(df) > 0 else 0
            losing_trades = df.get('losing_trades', pd.Series([0])).iloc[-1] if len(df) > 0 else 0
            win_rate = df.get('win_rate', pd.Series([0])).iloc[-1] if len(df) > 0 else 0
            
            return {
                "total_trades": int(total_trades),
                "winning_trades": int(winning_trades),
                "losing_trades": int(losing_trades),
                "win_rate": float(win_rate),
                "total_pnl": 0.0,  # Will be calculated from equity data
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "data_source": "csv_fallback",
                "last_updated": datetime.fromtimestamp(trades_file.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 CSV fallback data error: {e}")
            return None
    
    def _get_csv_portfolio_data(self) -> Optional[Dict[str, Any]]:
        """Get portfolio data from local CSV files"""
        try:
            portfolio_file = self.data_dir / "portfolio.csv"
            if not portfolio_file.exists():
                return None
            
            df = pd.read_csv(portfolio_file)
            if df.empty:
                return None
            
            # Get latest portfolio state
            latest = df.iloc[-1]
            
            return {
                "total_balance": float(latest.get('total_balance', 0)),
                "available_balance": float(latest.get('available_balance', 0)),
                "total_pnl": float(latest.get('total_pnl', 0)),
                "open_positions": int(latest.get('open_positions', 0)),
                "data_source": "csv_fallback",
                "last_updated": datetime.fromtimestamp(portfolio_file.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 CSV portfolio fallback error: {e}")
            return None
    
    def _get_csv_equity_data(self) -> Optional[Dict[str, Any]]:
        """Get equity data from local CSV files"""
        try:
            equity_file = self.data_dir / "equity.csv"
            if not equity_file.exists():
                return None
            
            df = pd.read_csv(equity_file)
            if df.empty:
                return None
            
            # Convert to chart format
            equity_curve = []
            for _, row in df.iterrows():
                equity_curve.append({
                    "timestamp": row.get('timestamp', ''),
                    "balance": float(row.get('balance', 0)),
                    "pnl": float(row.get('pnl', 0))
                })
            
            return {
                "equity_curve": equity_curve,
                "data_source": "csv_fallback",
                "last_updated": datetime.fromtimestamp(equity_file.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 CSV equity fallback error: {e}")
            return None
    
    def _get_database_fallback_data(self) -> Optional[Dict[str, Any]]:
        """Get fallback data from local database"""
        try:
            if not self.database_path.exists():
                return None
            
            with sqlite3.connect(self.database_path) as conn:
                # Get latest trading performance
                cursor = conn.execute("""
                    SELECT 
                        total_trades, winning_trades, losing_trades, 
                        win_rate, total_pnl, avg_win, avg_loss, profit_factor
                    FROM trading_performance 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "total_trades": row[0] or 0,
                        "winning_trades": row[1] or 0,
                        "losing_trades": row[2] or 0,
                        "win_rate": row[3] or 0.0,
                        "total_pnl": row[4] or 0.0,
                        "avg_win": row[5] or 0.0,
                        "avg_loss": row[6] or 0.0,
                        "profit_factor": row[7] or 0.0,
                        "data_source": "database_fallback",
                        "last_updated": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Database fallback error: {e}")
            return None
    
    def _get_database_portfolio_data(self) -> Optional[Dict[str, Any]]:
        """Get portfolio data from local database"""
        try:
            if not self.database_path.exists():
                return None
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        total_balance, available_balance, total_pnl, open_positions
                    FROM portfolio 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "total_balance": row[0] or 0.0,
                        "available_balance": row[1] or 0.0,
                        "total_pnl": row[2] or 0.0,
                        "open_positions": row[3] or 0,
                        "data_source": "database_fallback",
                        "last_updated": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Database portfolio fallback error: {e}")
            return None
    
    def _get_database_equity_data(self) -> Optional[Dict[str, Any]]:
        """Get equity data from local database"""
        try:
            if not self.database_path.exists():
                return None
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, balance, pnl
                    FROM equity_curve 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """)
                
                rows = cursor.fetchall()
                if rows:
                    equity_curve = []
                    for row in rows:
                        equity_curve.append({
                            "timestamp": row[0],
                            "balance": row[1] or 0.0,
                            "pnl": row[2] or 0.0
                        })
                    
                    return {
                        "equity_curve": equity_curve,
                        "data_source": "database_fallback",
                        "last_updated": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"💥 Database equity fallback error: {e}")
            return None
    
    def _generate_demo_trading_data(self) -> Dict[str, Any]:
        """Generate demo trading data as last resort"""
        logger.warning("⚠️ Generating demo trading data - Pi unavailable and no local data")
        
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "data_source": "demo_data",
            "last_updated": datetime.now().isoformat(),
            "warning": "Demo data - Pi unavailable"
        }
    
    def _generate_demo_portfolio_data(self) -> Dict[str, Any]:
        """Generate demo portfolio data as last resort"""
        logger.warning("⚠️ Generating demo portfolio data - Pi unavailable and no local data")
        
        return {
            "total_balance": 1000.0,
            "available_balance": 1000.0,
            "total_pnl": 0.0,
            "open_positions": 0,
            "data_source": "demo_data",
            "last_updated": datetime.now().isoformat(),
            "warning": "Demo data - Pi unavailable"
        }
    
    def _generate_demo_equity_data(self) -> Dict[str, Any]:
        """Generate demo equity data as last resort"""
        logger.warning("⚠️ Generating demo equity data - Pi unavailable and no local data")
        
        # Generate a simple equity curve
        equity_curve = []
        base_balance = 1000.0
        current_time = datetime.now()
        
        for i in range(24):  # Last 24 hours
            timestamp = (current_time - timedelta(hours=i)).isoformat()
            balance = base_balance + (i * 5)  # Slight upward trend
            pnl = balance - base_balance
            
            equity_curve.append({
                "timestamp": timestamp,
                "balance": balance,
                "pnl": pnl
            })
        
        return {
            "equity_curve": equity_curve,
            "data_source": "demo_data",
            "last_updated": datetime.now().isoformat(),
            "warning": "Demo data - Pi unavailable"
        }
    
    def update_fallback_cache(self, data: Dict[str, Any]):
        """Update fallback data cache"""
        try:
            self.fallback_data.update(data)
            self.last_fallback_update = datetime.now()
            logger.info("💾 Fallback data cache updated")
        except Exception as e:
            logger.error(f"💥 Fallback cache update error: {e}")
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """Get fallback system status"""
        return {
            "fallback_enabled": self.fallback_enabled,
            "last_fallback_update": self.last_fallback_update.isoformat() if self.last_fallback_update else None,
            "cached_data_types": list(self.fallback_data.keys()),
            "local_files_available": len(list(self.data_dir.glob("*.csv"))),
            "database_available": self.database_path.exists()
        }
    
    def enable_fallback(self):
        """Enable fallback system"""
        self.fallback_enabled = True
        logger.info("✅ Fallback system enabled")
    
    def disable_fallback(self):
        """Disable fallback system"""
        self.fallback_enabled = False
        logger.info("❌ Fallback system disabled")
