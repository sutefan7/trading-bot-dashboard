#!/usr/bin/env python3
"""
Database Layer for Trading Bot Dashboard
SQLite database for structured data storage and queries
"""
import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database for trading data"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity_requested REAL,
                    quantity_filled REAL,
                    price REAL,
                    status TEXT,
                    pnl REAL,
                    model_id TEXT,
                    model_ver TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for trades table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
            
            # Portfolio snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    total_balance REAL NOT NULL,
                    available_balance REAL,
                    total_pnl REAL,
                    realized_pnl REAL,
                    unrealized_pnl REAL,
                    open_positions INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for portfolio_snapshots table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_snapshots(timestamp)')
            
            # Equity curve table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equity_curve (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL UNIQUE,
                    balance REAL NOT NULL,
                    pnl REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for equity_curve table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_curve(timestamp)')
            
            # Trading performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.0,
                    avg_win REAL DEFAULT 0.0,
                    avg_loss REAL DEFAULT 0.0,
                    profit_factor REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    sharpe_ratio REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for trading_metrics table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON trading_metrics(timestamp)')
            
            # Sync status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    files_synced INTEGER,
                    sync_duration_ms REAL,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for sync_status table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_timestamp ON sync_status(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_status(status)')
            
            logger.info(f"✅ Database initialized: {self.db_path}")
    
    def import_from_csv(self, csv_dir: Path) -> Dict[str, int]:
        """
        Import data from CSV files into database
        Returns: Dictionary with counts of imported records per table
        """
        imported = {}
        
        try:
            # Import trades
            trades_file = csv_dir / 'portfolio.csv'
            if trades_file.exists():
                df = pd.read_csv(trades_file)
                imported['trades'] = self._import_trades(df)
            
            # Import equity curve
            equity_file = csv_dir / 'equity.csv'
            if equity_file.exists():
                df = pd.read_csv(equity_file)
                imported['equity_curve'] = self._import_equity(df)
            
            # Import trading metrics
            metrics_file = csv_dir / 'trades_summary.csv'
            if metrics_file.exists():
                df = pd.read_csv(metrics_file)
                imported['trading_metrics'] = self._import_metrics(df)
            
            logger.info(f"📊 CSV import complete: {imported}")
            return imported
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {e}")
            return imported
    
    def _import_trades(self, df: pd.DataFrame) -> int:
        """Import trades from DataFrame"""
        count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO trades 
                        (timestamp, symbol, side, quantity_requested, quantity_filled, 
                         status, pnl, model_id, model_ver)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('timestamp'),
                        row.get('symbol'),
                        row.get('side'),
                        row.get('qty_req'),
                        row.get('qty_filled'),
                        row.get('status'),
                        row.get('pnl_after'),
                        row.get('model_id'),
                        row.get('model_ver')
                    ))
                    count += cursor.rowcount
                except Exception as e:
                    logger.warning(f"Error importing trade row: {e}")
        
        return count
    
    def _import_equity(self, df: pd.DataFrame) -> int:
        """Import equity curve from DataFrame"""
        count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO equity_curve 
                        (timestamp, balance, pnl, total_trades, winning_trades, 
                         losing_trades, win_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('timestamp'),
                        row.get('balance'),
                        row.get('pnl'),
                        row.get('total_trades'),
                        row.get('winning_trades'),
                        row.get('losing_trades'),
                        row.get('win_rate')
                    ))
                    count += cursor.rowcount
                except Exception as e:
                    logger.warning(f"Error importing equity row: {e}")
        
        return count
    
    def _import_metrics(self, df: pd.DataFrame) -> int:
        """Import trading metrics from DataFrame"""
        count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT INTO trading_metrics 
                        (timestamp, total_trades, winning_trades, losing_trades, win_rate)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('timestamp'),
                        row.get('total_trades', 0),
                        row.get('winning_trades', 0),
                        row.get('losing_trades', 0),
                        row.get('win_rate', 0.0)
                    ))
                    count += cursor.rowcount
                except Exception as e:
                    logger.warning(f"Error importing metrics row: {e}")
        
        return count
    
    def get_latest_equity(self) -> Optional[Dict[str, Any]]:
        """Get latest equity data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM equity_curve 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_equity_curve(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get equity curve data for specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            since = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT timestamp, balance, pnl 
                FROM equity_curve 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (since.isoformat(),))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trading_performance(self) -> Optional[Dict[str, Any]]:
        """Get latest trading performance metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trading_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trades 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get latest portfolio snapshot
            cursor.execute('''
                SELECT * FROM portfolio_snapshots 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            snapshot = cursor.fetchone()
            
            # Get open positions count
            cursor.execute('''
                SELECT COUNT(*) as count FROM trades 
                WHERE status = 'open'
            ''')
            open_positions = cursor.fetchone()['count']
            
            # Get total trades
            cursor.execute('SELECT COUNT(*) as count FROM trades')
            total_trades = cursor.fetchone()['count']
            
            if snapshot:
                return {
                    **dict(snapshot),
                    'open_positions': open_positions,
                    'total_trades': total_trades
                }
            else:
                return {
                    'total_balance': 0.0,
                    'available_balance': 0.0,
                    'total_pnl': 0.0,
                    'open_positions': open_positions,
                    'total_trades': total_trades,
                    'timestamp': None
                }
    
    def record_sync_status(self, status: str, files_synced: int = 0, 
                          duration_ms: float = 0, error: Optional[str] = None):
        """Record sync status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sync_status 
                (timestamp, status, files_synced, sync_duration_ms, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), status, files_synced, duration_ms, error))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['trades', 'equity_curve', 'portfolio_snapshots', 
                     'trading_metrics', 'sync_status']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()['count']
            
            # Database file size
            stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            stats['database_path'] = str(self.db_path)
            
            return stats
    
    def vacuum(self):
        """Optimize database (reclaim space)"""
        with self.get_connection() as conn:
            conn.execute('VACUUM')
        logger.info("Database optimized (VACUUM)")
    
    def backup(self, backup_path: Path) -> bool:
        """Create database backup"""
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()
            logger.info(f"✅ Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            return False

