#!/usr/bin/env python3
"""
Trading Bot Dashboard - Data Sync System
Syncs CSV data from Raspberry Pi to local Mac
"""
import os
import subprocess
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional

# Configuration
PI_HOST = "stephang@192.168.1.104"
PI_PATH = "/home/stephang/trading-bot-v4/storage/reports"
LOCAL_DATA_DIR = Path(__file__).parent / "data"
SYNC_INTERVAL_MINUTES = 5

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataSyncManager:
    """Manages data synchronization from Pi to Mac"""
    
    def __init__(self):
        self.local_data_dir = LOCAL_DATA_DIR
        self.local_data_dir.mkdir(exist_ok=True)
        self.last_sync = None
        self.sync_status = "unknown"
        self.success_count = 0
        self.failure_count = 0
        self.last_success = None
        self.last_failure = None
    
    def check_pi_connectivity(self) -> bool:
        """Check if Pi is reachable before attempting sync"""
        try:
            # Extract IP from PI_HOST (e.g., "stephang@192.168.1.104" -> "192.168.1.104")
            pi_ip = PI_HOST.split('@')[1] if '@' in PI_HOST else PI_HOST
            
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
    
    def sync_data_from_pi(self) -> bool:
        """
        Sync CSV files from Pi to local Mac using SCP
        
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            logger.info("🔄 Starting data sync from Pi...")
            
            # Check Pi connectivity first
            if not self.check_pi_connectivity():
                self.sync_status = "pi_offline"
                self.failure_count += 1
                self.last_failure = datetime.now()
                logger.warning("⚠️ Pi is offline, skipping sync")
                return False
            
            # Create SCP command with improved security
            scp_command = [
                "scp",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=yes",
                "-o", "UserKnownHostsFile=~/.ssh/known_hosts",
                "-o", "LogLevel=ERROR",
                f"{PI_HOST}:{PI_PATH}/*.csv",
                str(self.local_data_dir)
            ]
            
            # Execute SCP command
            result = subprocess.run(
                scp_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.last_sync = datetime.now()
                self.sync_status = "success"
                self.success_count += 1
                self.last_success = datetime.now()
                logger.info("✅ Data sync successful")
                
                # Process and validate synced files
                self._process_synced_files()
                return True
            else:
                self.sync_status = "failed"
                self.failure_count += 1
                self.last_failure = datetime.now()
                logger.error(f"❌ SCP failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.sync_status = "timeout"
            self.failure_count += 1
            self.last_failure = datetime.now()
            logger.error("⏰ SCP timeout - Pi may be offline")
            return False
        except Exception as e:
            self.sync_status = "error"
            self.failure_count += 1
            self.last_failure = datetime.now()
            logger.error(f"💥 Sync error: {e}")
            return False
    
    def _process_synced_files(self):
        """Process and validate synced CSV files"""
        try:
            csv_files = list(self.local_data_dir.glob("*.csv"))
            logger.info(f"📁 Found {len(csv_files)} CSV files")
            
            for csv_file in csv_files:
                try:
                    # Validate CSV data using new validation function
                    is_valid, df = self.validate_csv_data(csv_file)
                    
                    if is_valid and df is not None:
                        logger.info(f"✅ {csv_file.name}: {len(df)} rows, {len(df.columns)} columns")
                        
                        # Create summary metadata
                        self._create_file_metadata(csv_file, df)
                    else:
                        logger.warning(f"⚠️ Skipping invalid file: {csv_file.name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {csv_file.name}: {e}")
                    
        except Exception as e:
            logger.error(f"💥 Error processing files: {e}")
    
    def _create_file_metadata(self, csv_file: Path, df: pd.DataFrame):
        """Create metadata file for CSV"""
        try:
            metadata = {
                "filename": csv_file.name,
                "last_updated": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "file_size": csv_file.stat().st_size,
                "data_types": df.dtypes.to_dict()
            }
            
            metadata_file = csv_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"❌ Error creating metadata for {csv_file.name}: {e}")
    
    def get_sync_status(self) -> Dict:
        """Get current sync status with enhanced monitoring"""
        total_attempts = self.success_count + self.failure_count
        success_rate = (self.success_count / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "status": self.sync_status,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "local_files": len(list(self.local_data_dir.glob("*.csv"))),
            "data_dir": str(self.local_data_dir),
            "pi_online": self.check_pi_connectivity(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(success_rate, 2),
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None
        }
    
    def get_available_data_files(self) -> List[Dict]:
        """Get list of available data files"""
        files = []
        for csv_file in self.local_data_dir.glob("*.csv"):
            try:
                stat = csv_file.stat()
                files.append({
                    "name": csv_file.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                })
            except Exception as e:
                logger.error(f"❌ Error reading {csv_file.name}: {e}")
                
        return files
    
    def validate_csv_data(self, file_path: Path) -> tuple[bool, Optional[pd.DataFrame]]:
        """Validate CSV data integrity"""
        try:
            df = pd.read_csv(file_path)
            
            # Basic validation
            if df.empty:
                logger.warning(f"⚠️ Empty CSV file: {file_path.name}")
                return False, None
            
            # Check for required columns (flexible based on file type)
            required_columns = {
                'trades_summary.csv': ['timestamp', 'total_trades'],
                'portfolio.csv': ['timestamp', 'symbol'],
                'equity.csv': ['timestamp', 'balance']
            }
            
            file_name = file_path.name
            if file_name in required_columns:
                missing_cols = set(required_columns[file_name]) - set(df.columns)
                if missing_cols:
                    logger.error(f"❌ Missing required columns in {file_name}: {missing_cols}")
                    return False, None
            
            # Check data types
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e:
                    logger.error(f"❌ Invalid timestamp format in {file_name}: {e}")
                    return False, None
            
            logger.info(f"✅ CSV validation passed for {file_name}: {len(df)} rows")
            return True, df
            
        except Exception as e:
            logger.error(f"❌ CSV validation failed for {file_path.name}: {e}")
            return False, None


def main():
    """Main sync function"""
    sync_manager = DataSyncManager()
    
    # Initial sync
    logger.info("🚀 Starting Trading Bot Dashboard Data Sync")
    logger.info(f"📡 Pi: {PI_HOST}:{PI_PATH}")
    logger.info(f"💾 Local: {LOCAL_DATA_DIR}")
    logger.info(f"⏰ Sync interval: {SYNC_INTERVAL_MINUTES} minutes")
    
    # Test initial sync
    if sync_manager.sync_data_from_pi():
        logger.info("✅ Initial sync successful")
    else:
        logger.warning("⚠️ Initial sync failed - Pi may be offline")
    
    # Show status
    status = sync_manager.get_sync_status()
    logger.info(f"📊 Sync status: {status}")


if __name__ == "__main__":
    main()
