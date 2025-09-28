#!/usr/bin/env python3
"""
Trading Bot Dashboard - Backup & Recovery System
Automatic backups and disaster recovery
"""
import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupManager:
    """Manages automatic backups and recovery"""
    
    def __init__(self, data_dir: Path, backup_dir: Path = None):
        self.data_dir = data_dir
        self.backup_dir = backup_dir or Path(__file__).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.retention_days = 30  # Keep backups for 30 days
        
    def create_backup(self, backup_name: str = None) -> str:
        """Create a new backup"""
        try:
            if not backup_name:
                backup_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"🔄 Creating backup: {backup_name}")
            
            # Backup data directory
            if self.data_dir.exists():
                shutil.copytree(self.data_dir, backup_path / 'data')
                logger.info(f"✅ Data directory backed up")
            
            # Backup configuration files
            config_files = ['web_server.py', 'data_sync.py', 'auto_sync.py']
            for config_file in config_files:
                src = Path(__file__).parent / config_file
                if src.exists():
                    shutil.copy2(src, backup_path / config_file)
            
            # Create backup metadata
            metadata = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'data_files': len(list(self.data_dir.glob('*.csv'))) if self.data_dir.exists() else 0,
                'backup_size': self._get_directory_size(backup_path),
                'version': '1.0'
            }
            
            with open(backup_path / 'backup_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Backup created successfully: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return None
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup"""
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                logger.error(f"❌ Backup not found: {backup_name}")
                return False
            
            logger.info(f"🔄 Restoring backup: {backup_name}")
            
            # Create current backup before restore
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if not current_backup:
                logger.warning("⚠️ Could not create pre-restore backup")
            
            # Restore data directory
            backup_data_dir = backup_path / 'data'
            if backup_data_dir.exists():
                if self.data_dir.exists():
                    shutil.rmtree(self.data_dir)
                shutil.copytree(backup_data_dir, self.data_dir)
                logger.info("✅ Data directory restored")
            
            # Restore configuration files
            config_files = ['web_server.py', 'data_sync.py', 'auto_sync.py']
            for config_file in config_files:
                backup_config = backup_path / config_file
                if backup_config.exists():
                    shutil.copy2(backup_config, Path(__file__).parent / config_file)
            
            logger.info(f"✅ Backup restored successfully: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'backup_metadata.json'
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        logger.error(f"❌ Error reading metadata for {backup_dir.name}: {e}")
                else:
                    # Legacy backup without metadata
                    backups.append({
                        'backup_name': backup_dir.name,
                        'created_at': datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                        'data_files': len(list((backup_dir / 'data').glob('*.csv'))) if (backup_dir / 'data').exists() else 0,
                        'backup_size': self._get_directory_size(backup_dir),
                        'version': 'legacy'
                    })
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    # Get creation date from metadata or directory timestamp
                    metadata_file = backup_dir / 'backup_metadata.json'
                    
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            created_at = datetime.fromisoformat(metadata['created_at'])
                        except:
                            created_at = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                    else:
                        created_at = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                    
                    if created_at < cutoff_date:
                        logger.info(f"🗑️ Removing old backup: {backup_dir.name}")
                        shutil.rmtree(backup_dir)
                        removed_count += 1
            
            if removed_count > 0:
                logger.info(f"✅ Cleaned up {removed_count} old backups")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")
            return 0
    
    def compress_backup(self, backup_name: str) -> bool:
        """Compress a backup to save space"""
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                logger.error(f"❌ Backup not found: {backup_name}")
                return False
            
            logger.info(f"🗜️ Compressing backup: {backup_name}")
            
            # Create compressed archive
            compressed_path = self.backup_dir / f"{backup_name}.tar.gz"
            
            # Use tar to create compressed archive
            import tarfile
            with tarfile.open(compressed_path, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_name)
            
            # Remove original directory
            shutil.rmtree(backup_path)
            
            logger.info(f"✅ Backup compressed: {compressed_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup compression failed: {e}")
            return False
    
    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"❌ Error calculating directory size: {e}")
        return total_size
    
    def get_backup_status(self) -> Dict:
        """Get backup system status"""
        backups = self.list_backups()
        total_size = sum(backup.get('backup_size', 0) for backup in backups)
        
        return {
            'total_backups': len(backups),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'retention_days': self.retention_days,
            'backup_dir': str(self.backup_dir),
            'latest_backup': backups[0]['backup_name'] if backups else None,
            'oldest_backup': backups[-1]['backup_name'] if backups else None
        }


def main():
    """Main backup function"""
    data_dir = Path(__file__).parent / "data"
    backup_manager = BackupManager(data_dir)
    
    logger.info("🚀 Starting Trading Bot Dashboard Backup System")
    
    # Create daily backup
    backup_name = backup_manager.create_backup()
    if backup_name:
        logger.info(f"✅ Daily backup created: {backup_name}")
    else:
        logger.error("❌ Daily backup failed")
    
    # Cleanup old backups
    removed = backup_manager.cleanup_old_backups()
    if removed > 0:
        logger.info(f"✅ Cleaned up {removed} old backups")
    
    # Show status
    status = backup_manager.get_backup_status()
    logger.info(f"📊 Backup status: {status}")


if __name__ == "__main__":
    main()
