#!/usr/bin/env python3
"""
Trading Bot Dashboard - Backup Scheduler
Automated backup scheduling and management
"""
import time
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
from backup_system import BackupManager
from audit_logger import audit_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def backup_job():
    """Scheduled backup job"""
    try:
        logger.info("🔄 Starting scheduled backup...")
        
        data_dir = Path(__file__).parent / "data"
        backup_manager = BackupManager(data_dir)
        
        # Create backup
        backup_name = backup_manager.create_backup()
        
        if backup_name:
            logger.info(f"✅ Scheduled backup completed: {backup_name}")
            audit_logger.log_backup_activity('SCHEDULED_CREATE', backup_name, True)
        else:
            logger.error("❌ Scheduled backup failed")
            audit_logger.log_backup_activity('SCHEDULED_CREATE', None, False, "Backup creation failed")
            
    except Exception as e:
        logger.error(f"💥 Error in scheduled backup: {e}")
        audit_logger.log_backup_activity('SCHEDULED_CREATE', None, False, str(e))


def cleanup_job():
    """Scheduled cleanup job"""
    try:
        logger.info("🧹 Starting scheduled cleanup...")
        
        data_dir = Path(__file__).parent / "data"
        backup_manager = BackupManager(data_dir)
        
        # Cleanup old backups
        removed_count = backup_manager.cleanup_old_backups()
        
        if removed_count > 0:
            logger.info(f"✅ Cleaned up {removed_count} old backups")
            audit_logger.log_backup_activity('CLEANUP', f"{removed_count} backups removed", True)
        else:
            logger.info("ℹ️ No old backups to clean up")
            
    except Exception as e:
        logger.error(f"💥 Error in scheduled cleanup: {e}")
        audit_logger.log_backup_activity('CLEANUP', None, False, str(e))


def compression_job():
    """Scheduled compression job for old backups"""
    try:
        logger.info("🗜️ Starting scheduled compression...")
        
        data_dir = Path(__file__).parent / "data"
        backup_manager = BackupManager(data_dir)
        
        # Get backups older than 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        backups = backup_manager.list_backups()
        
        compressed_count = 0
        for backup in backups:
            try:
                created_at = datetime.fromisoformat(backup['created_at'])
                if created_at < cutoff_date and not backup['backup_name'].endswith('.tar.gz'):
                    if backup_manager.compress_backup(backup['backup_name']):
                        compressed_count += 1
            except Exception as e:
                logger.error(f"Error compressing backup {backup['backup_name']}: {e}")
        
        if compressed_count > 0:
            logger.info(f"✅ Compressed {compressed_count} old backups")
            audit_logger.log_backup_activity('COMPRESSION', f"{compressed_count} backups compressed", True)
        else:
            logger.info("ℹ️ No backups to compress")
            
    except Exception as e:
        logger.error(f"💥 Error in scheduled compression: {e}")
        audit_logger.log_backup_activity('COMPRESSION', None, False, str(e))


def main():
    """Main backup scheduler service"""
    logger.info("🚀 Starting Trading Bot Dashboard Backup Scheduler")
    
    # Schedule backup jobs
    schedule.every().day.at("02:00").do(backup_job)  # Daily backup at 2 AM
    schedule.every().sunday.at("03:00").do(cleanup_job)  # Weekly cleanup on Sunday at 3 AM
    schedule.every().monday.at("04:00").do(compression_job)  # Weekly compression on Monday at 4 AM
    
    logger.info("📅 Backup schedule configured:")
    logger.info("   • Daily backup: 02:00")
    logger.info("   • Weekly cleanup: Sunday 03:00")
    logger.info("   • Weekly compression: Monday 04:00")
    
    # Run initial backup
    logger.info("🔄 Running initial backup...")
    backup_job()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Backup scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Backup scheduler error: {e}")


if __name__ == "__main__":
    main()
