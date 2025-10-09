#!/usr/bin/env python3
"""
Configuration Management for Trading Bot Dashboard
Centralized configuration with environment variable support
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import ipaddress

# Load .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)


class Config:
    """Application configuration"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    SSL_DIR = BASE_DIR / "ssl"
    BACKUPS_DIR = BASE_DIR / "backups"
    
    # Server configuration
    HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    PORT = int(os.getenv('DASHBOARD_PORT', '5001'))
    DEBUG = os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true'
    THREADED = True
    
    # Security configuration
    SECRET_KEY = os.getenv('DASHBOARD_SECRET_KEY', os.urandom(32).hex())
    AUTH_ENABLED = os.getenv('DASHBOARD_AUTH_ENABLED', 'True').lower() == 'true'
    AUTH_USERNAME = os.getenv('DASHBOARD_USERNAME', 'admin')
    AUTH_PASSWORD_HASH = os.getenv('DASHBOARD_PASSWORD_HASH', '')
    
    # SSL/HTTPS configuration
    SSL_CERT_FILE = SSL_DIR / 'dashboard.crt'
    SSL_KEY_FILE = SSL_DIR / 'dashboard.key'
    HTTPS_ENABLED = False  # Set at runtime
    
    # CORS configuration
    ALLOWED_ORIGINS = [
        o.strip() 
        for o in os.getenv(
            'DASHBOARD_ALLOWED_ORIGINS', 
            'http://localhost:5001,http://127.0.0.1:5001,https://localhost:5001,https://127.0.0.1:5001'
        ).split(',') 
        if o.strip()
    ]
    
    # Rate limiting
    RATE_LIMIT_DEFAULT = os.getenv('DASHBOARD_RATE_LIMIT_DEFAULT', '1000 per hour')
    RATE_LIMIT_API = os.getenv('DASHBOARD_RATE_LIMIT_API', '100 per minute')
    RATE_LIMIT_AUTH = os.getenv('DASHBOARD_RATE_LIMIT_AUTH', '10 per minute')
    
    # File size limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LOG_SIZE = 50 * 1024 * 1024   # 50MB
    
    # Data sync configuration
    PI_HOST = os.getenv('PI_HOST', 'stephang@192.168.1.104')
    PI_PATH = os.getenv('PI_PATH', '/srv/trading-bot-pi/app/storage/reports')
    PI_APP_PATH = os.getenv('PI_APP_PATH', '/srv/trading-bot-pi/app')
    PI_DATABASE_PATH = os.getenv('PI_DATABASE_PATH', '/srv/trading-bot-pi/app/data')
    SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', '5'))
    SYNC_TIMEOUT_SECONDS = int(os.getenv('SYNC_TIMEOUT_SECONDS', '30'))
    
    # New Pi API configuration
    PI_API_ENABLED = os.getenv('PI_API_ENABLED', 'True').lower() == 'true'
    PI_API_PORT = int(os.getenv('PI_API_PORT', '8080'))
    PI_API_TIMEOUT = int(os.getenv('PI_API_TIMEOUT', '10'))
    
    # Cache configuration
    CACHE_TIMEOUT_SECONDS = int(os.getenv('CACHE_TIMEOUT_SECONDS', '60'))
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    
    # Database configuration
    DATABASE_PATH = DATA_DIR / 'trading_bot.db'
    DATABASE_BACKUP_PATH = BACKUPS_DIR / 'db_backups'
    
    # Backup configuration
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
    MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', '50'))
    AUTO_BACKUP_ENABLED = os.getenv('AUTO_BACKUP_ENABLED', 'True').lower() == 'true'
    AUTO_BACKUP_INTERVAL_HOURS = int(os.getenv('AUTO_BACKUP_INTERVAL_HOURS', '24'))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Validation patterns for CSV data
    ALLOWED_CSV_COLUMNS = {
        'trades_summary.csv': [
            'timestamp', 'total_trades', 'unique_requests', 
            'chain_integrity', 'verified_records', 'total_records'
        ],
        'portfolio.csv': [
            'timestamp', 'symbol', 'side', 'qty_req', 'qty_filled', 
            'status', 'pnl_after', 'balance_after', 'model_id', 'model_ver'
        ],
        'equity.csv': [
            'timestamp', 'balance', 'pnl', 'total_trades', 
            'winning_trades', 'losing_trades', 'win_rate'
        ]
    }
    
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.SSL_DIR, 
                         cls.BACKUPS_DIR, cls.DATABASE_BACKUP_PATH]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_private_ip(cls, ip: str) -> bool:
        """
        Check if IP address is private/local
        More robust than hardcoded string matching
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            return False
    
    @classmethod
    def validate_config(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration
        Returns: (is_valid, error_messages)
        """
        errors = []
        
        if cls.AUTH_ENABLED and not cls.AUTH_PASSWORD_HASH:
            errors.append("Authentication enabled but no password hash configured")
        
        if cls.PORT < 1024 and os.geteuid() != 0:
            errors.append(f"Port {cls.PORT} requires root privileges")
        
        if not cls.PI_HOST:
            errors.append("PI_HOST not configured")
        
        if not cls.PI_PATH:
            errors.append("PI_PATH not configured")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get configuration summary for debugging"""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'auth_enabled': cls.AUTH_ENABLED,
            'https_enabled': cls.HTTPS_ENABLED,
            'cache_enabled': cls.CACHE_ENABLED,
            'pi_host': cls.PI_HOST,
            'sync_interval': cls.SYNC_INTERVAL_MINUTES,
            'database_path': str(cls.DATABASE_PATH),
        }


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    AUTH_ENABLED = False  # Disable auth in development
    CACHE_ENABLED = False  # Disable cache in development


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    AUTH_ENABLED = True
    CACHE_ENABLED = True


class TestConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    DEBUG = True
    AUTH_ENABLED = False
    DATABASE_PATH = Path(__file__).parent / 'test_data' / 'test.db'


def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration based on environment
    
    Args:
        env: Environment name ('development', 'production', 'testing')
             If None, uses DASHBOARD_ENV environment variable
    
    Returns:
        Config object for the specified environment
    """
    if env is None:
        env = os.getenv('DASHBOARD_ENV', 'production')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestConfig,
    }
    
    return config_map.get(env.lower(), ProductionConfig)

