#!/usr/bin/env python3
"""
Trading Bot Dashboard - Auto Sync Service
Runs in background to automatically sync data from Pi
"""
import time
import schedule
import logging
from datetime import datetime
from data_sync import DataSyncManager
from audit_logger import log_sync_activity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sync_job():
    """Scheduled sync job"""
    try:
        logger.info("🔄 Starting scheduled sync...")
        sync_manager = DataSyncManager()
        success = sync_manager.sync_data_from_pi()
        
        # Log sync activity for audit
        files_synced = sync_manager.get_sync_status().get('local_files', 0)
        log_sync_activity('SCHEDULED_SYNC', success, files_synced=files_synced)
        
        if success:
            logger.info("✅ Scheduled sync completed successfully")
        else:
            logger.warning("⚠️ Scheduled sync failed - Pi may be offline")
            
    except Exception as e:
        log_sync_activity('SCHEDULED_SYNC', False, str(e))
        logger.error(f"💥 Error in scheduled sync: {e}")


def main():
    """Main auto sync service"""
    logger.info("🚀 Starting Trading Bot Dashboard Auto Sync Service")
    logger.info("⏰ Sync interval: Every 5 minutes")
    
    # Schedule sync job every 5 minutes
    schedule.every(5).minutes.do(sync_job)
    
    # Run initial sync
    logger.info("🔄 Running initial sync...")
    sync_job()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        logger.info("🛑 Auto sync service stopped by user")
    except Exception as e:
        logger.error(f"💥 Auto sync service error: {e}")


if __name__ == "__main__":
    main()
