#!/usr/bin/env python3
"""
Health Monitor for Trading Bot Dashboard
Comprehensive system health monitoring and alerting
"""
import os
import psutil
import time
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
import subprocess
from dataclasses import dataclass
from enum import Enum

from config import Config

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    value: Any = None
    threshold: Any = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self):
        self.config = Config
        self.health_history = []
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 5000.0,  # 5 seconds
            "error_rate": 10.0,  # 10%
            "data_age_hours": 2.0
        }
        self.last_health_check = None
        self.health_status = HealthStatus.UNKNOWN
        
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        start_time = datetime.now()
        checks = []
        
        try:
            # System health checks
            checks.extend(self._check_system_resources())
            checks.extend(self._check_database_health())
            checks.extend(self._check_pi_connectivity())
            checks.extend(self._check_data_freshness())
            checks.extend(self._check_log_files())
            checks.extend(self._check_ssl_certificates())
            checks.extend(self._check_backup_system())
            
            # Calculate overall health status
            overall_status = self._calculate_overall_status(checks)
            
            # Store health history
            health_result = {
                "timestamp": start_time.isoformat(),
                "overall_status": overall_status.value,
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status.value,
                        "message": check.message,
                        "value": check.value,
                        "threshold": check.threshold
                    }
                    for check in checks
                ],
                "summary": self._generate_health_summary(checks),
                "recommendations": self._generate_recommendations(checks)
            }
            
            self.health_history.append(health_result)
            self.last_health_check = start_time
            self.health_status = overall_status
            
            # Keep only last 100 health checks
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            logger.info(f"🏥 Health check completed: {overall_status.value}")
            return health_result
            
        except Exception as e:
            logger.error(f"💥 Health check error: {e}")
            return {
                "timestamp": start_time.isoformat(),
                "overall_status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "checks": []
            }
    
    def _check_system_resources(self) -> List[HealthCheck]:
        """Check system resource usage"""
        checks = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = HealthStatus.HEALTHY
            if cpu_percent > self.alert_thresholds["cpu_usage"]:
                cpu_status = HealthStatus.CRITICAL
            elif cpu_percent > self.alert_thresholds["cpu_usage"] * 0.8:
                cpu_status = HealthStatus.WARNING
            
            checks.append(HealthCheck(
                name="cpu_usage",
                status=cpu_status,
                message=f"CPU usage: {cpu_percent:.1f}%",
                value=cpu_percent,
                threshold=self.alert_thresholds["cpu_usage"]
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_status = HealthStatus.HEALTHY
            if memory_percent > self.alert_thresholds["memory_usage"]:
                memory_status = HealthStatus.CRITICAL
            elif memory_percent > self.alert_thresholds["memory_usage"] * 0.8:
                memory_status = HealthStatus.WARNING
            
            checks.append(HealthCheck(
                name="memory_usage",
                status=memory_status,
                message=f"Memory usage: {memory_percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)",
                value=memory_percent,
                threshold=self.alert_thresholds["memory_usage"]
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = HealthStatus.HEALTHY
            if disk_percent > self.alert_thresholds["disk_usage"]:
                disk_status = HealthStatus.CRITICAL
            elif disk_percent > self.alert_thresholds["disk_usage"] * 0.8:
                disk_status = HealthStatus.WARNING
            
            checks.append(HealthCheck(
                name="disk_usage",
                status=disk_status,
                message=f"Disk usage: {disk_percent:.1f}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)",
                value=disk_percent,
                threshold=self.alert_thresholds["disk_usage"]
            ))
            
            # Load average (Unix systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()[0]
                cpu_count = psutil.cpu_count()
                load_percent = (load_avg / cpu_count) * 100
                
                load_status = HealthStatus.HEALTHY
                if load_percent > 100:
                    load_status = HealthStatus.CRITICAL
                elif load_percent > 80:
                    load_status = HealthStatus.WARNING
                
                checks.append(HealthCheck(
                    name="load_average",
                    status=load_status,
                    message=f"Load average: {load_avg:.2f} ({load_percent:.1f}% of {cpu_count} cores)",
                    value=load_avg,
                    threshold=cpu_count
                ))
            
        except Exception as e:
            checks.append(HealthCheck(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"System resource check failed: {e}"
            ))
        
        return checks
    
    def _check_database_health(self) -> List[HealthCheck]:
        """Check database health"""
        checks = []
        
        try:
            db_path = self.config.DATABASE_PATH
            
            # Check if database exists
            if not db_path.exists():
                checks.append(HealthCheck(
                    name="database_exists",
                    status=HealthStatus.CRITICAL,
                    message="Database file does not exist"
                ))
                return checks
            
            # Check database size
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
            checks.append(HealthCheck(
                name="database_size",
                status=HealthStatus.HEALTHY,
                message=f"Database size: {db_size_mb:.1f}MB",
                value=db_size_mb
            ))
            
            # Check database connectivity and integrity
            with sqlite3.connect(db_path) as conn:
                # Test basic query
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                checks.append(HealthCheck(
                    name="database_connectivity",
                    status=HealthStatus.HEALTHY,
                    message=f"Database connected, {table_count} tables",
                    value=table_count
                ))
                
                # Check for recent data
                try:
                    cursor = conn.execute("""
                        SELECT MAX(timestamp) FROM trading_performance 
                        WHERE timestamp IS NOT NULL
                    """)
                    last_update = cursor.fetchone()[0]
                    
                    if last_update:
                        last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        hours_ago = (datetime.now() - last_update_dt).total_seconds() / 3600
                        
                        data_status = HealthStatus.HEALTHY
                        if hours_ago > self.alert_thresholds["data_age_hours"]:
                            data_status = HealthStatus.WARNING
                        if hours_ago > self.alert_thresholds["data_age_hours"] * 2:
                            data_status = HealthStatus.CRITICAL
                        
                        checks.append(HealthCheck(
                            name="database_data_freshness",
                            status=data_status,
                            message=f"Last data update: {hours_ago:.1f} hours ago",
                            value=hours_ago,
                            threshold=self.alert_thresholds["data_age_hours"]
                        ))
                except Exception as e:
                    checks.append(HealthCheck(
                        name="database_data_freshness",
                        status=HealthStatus.WARNING,
                        message=f"Could not check data freshness: {e}"
                    ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="database_health",
                status=HealthStatus.CRITICAL,
                message=f"Database health check failed: {e}"
            ))
        
        return checks
    
    def _check_pi_connectivity(self) -> List[HealthCheck]:
        """Check Pi connectivity and health"""
        checks = []
        
        try:
            # Import here to avoid circular imports
            from pi_api_client import PiAPIClient
            
            pi_client = PiAPIClient()
            
            # Check basic connectivity
            pi_online = pi_client.check_pi_connectivity()
            
            if pi_online:
                checks.append(HealthCheck(
                    name="pi_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="Pi is online and reachable"
                ))
                
                # Check Pi health
                try:
                    pi_health = pi_client.get_pi_health()
                    
                    if pi_health.get("status") == "healthy":
                        checks.append(HealthCheck(
                            name="pi_health",
                            status=HealthStatus.HEALTHY,
                            message="Pi system is healthy"
                        ))
                    elif pi_health.get("status") == "degraded":
                        checks.append(HealthCheck(
                            name="pi_health",
                            status=HealthStatus.WARNING,
                            message="Pi system is degraded"
                        ))
                    else:
                        checks.append(HealthCheck(
                            name="pi_health",
                            status=HealthStatus.CRITICAL,
                            message=f"Pi system status: {pi_health.get('status', 'unknown')}"
                        ))
                        
                except Exception as e:
                    checks.append(HealthCheck(
                        name="pi_health",
                        status=HealthStatus.WARNING,
                        message=f"Could not check Pi health: {e}"
                    ))
            else:
                checks.append(HealthCheck(
                    name="pi_connectivity",
                    status=HealthStatus.CRITICAL,
                    message="Pi is offline or unreachable"
                ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="pi_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Pi connectivity check failed: {e}"
            ))
        
        return checks
    
    def _check_data_freshness(self) -> List[HealthCheck]:
        """Check data freshness"""
        checks = []
        
        try:
            data_dir = self.config.DATA_DIR
            
            if not data_dir.exists():
                checks.append(HealthCheck(
                    name="data_directory",
                    status=HealthStatus.CRITICAL,
                    message="Data directory does not exist"
                ))
                return checks
            
            # Check CSV files
            csv_files = list(data_dir.glob("*.csv"))
            
            if not csv_files:
                checks.append(HealthCheck(
                    name="data_files",
                    status=HealthStatus.WARNING,
                    message="No CSV data files found"
                ))
                return checks
            
            # Check file ages
            newest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            file_age_hours = (datetime.now() - datetime.fromtimestamp(newest_file.stat().st_mtime)).total_seconds() / 3600
            
            data_status = HealthStatus.HEALTHY
            if file_age_hours > self.alert_thresholds["data_age_hours"]:
                data_status = HealthStatus.WARNING
            if file_age_hours > self.alert_thresholds["data_age_hours"] * 2:
                data_status = HealthStatus.CRITICAL
            
            checks.append(HealthCheck(
                name="data_freshness",
                status=data_status,
                message=f"Newest data file: {newest_file.name} ({file_age_hours:.1f} hours old)",
                value=file_age_hours,
                threshold=self.alert_thresholds["data_age_hours"]
            ))
            
            # Check file sizes
            total_size = sum(f.stat().st_size for f in csv_files)
            if total_size == 0:
                checks.append(HealthCheck(
                    name="data_size",
                    status=HealthStatus.WARNING,
                    message="All data files are empty"
                ))
            else:
                checks.append(HealthCheck(
                    name="data_size",
                    status=HealthStatus.HEALTHY,
                    message=f"Total data size: {total_size / 1024:.1f}KB"
                ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="data_freshness",
                status=HealthStatus.CRITICAL,
                message=f"Data freshness check failed: {e}"
            ))
        
        return checks
    
    def _check_log_files(self) -> List[HealthCheck]:
        """Check log file health"""
        checks = []
        
        try:
            logs_dir = self.config.LOGS_DIR
            
            if not logs_dir.exists():
                checks.append(HealthCheck(
                    name="logs_directory",
                    status=HealthStatus.WARNING,
                    message="Logs directory does not exist"
                ))
                return checks
            
            # Check log file sizes
            log_files = list(logs_dir.glob("*.log"))
            
            if not log_files:
                checks.append(HealthCheck(
                    name="log_files",
                    status=HealthStatus.WARNING,
                    message="No log files found"
                ))
                return checks            
            
            # Check for large log files
            large_logs = [f for f in log_files if f.stat().st_size > 50 * 1024 * 1024]  # 50MB
            
            if large_logs:
                checks.append(HealthCheck(
                    name="log_file_sizes",
                    status=HealthStatus.WARNING,
                    message=f"Large log files detected: {[f.name for f in large_logs]}"
                ))
            else:
                checks.append(HealthCheck(
                    name="log_file_sizes",
                    status=HealthStatus.HEALTHY,
                    message=f"Log file sizes are normal ({len(log_files)} files)"
                ))
            
            # Check for recent errors in logs
            try:
                error_log = logs_dir / "errors.log"
                if error_log.exists():
                    # Count errors in last hour
                    recent_errors = 0
                    with open(error_log, 'r') as f:
                        for line in f:
                            if "ERROR" in line:
                                # Simple time check (could be improved)
                                recent_errors += 1
                    
                    if recent_errors > 10:
                        checks.append(HealthCheck(
                            name="recent_errors",
                            status=HealthStatus.WARNING,
                            message=f"High error rate: {recent_errors} recent errors"
                        ))
                    else:
                        checks.append(HealthCheck(
                            name="recent_errors",
                            status=HealthStatus.HEALTHY,
                            message=f"Error rate is normal: {recent_errors} recent errors"
                        ))
                        
            except Exception as e:
                checks.append(HealthCheck(
                    name="recent_errors",
                    status=HealthStatus.WARNING,
                    message=f"Could not check error logs: {e}"
                ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="log_files",
                status=HealthStatus.CRITICAL,
                message=f"Log file check failed: {e}"
            ))
        
        return checks
    
    def _check_ssl_certificates(self) -> List[HealthCheck]:
        """Check SSL certificate health"""
        checks = []
        
        try:
            ssl_dir = self.config.SSL_DIR
            
            if not ssl_dir.exists():
                checks.append(HealthCheck(
                    name="ssl_directory",
                    status=HealthStatus.WARNING,
                    message="SSL directory does not exist"
                ))
                return checks
            
            cert_file = self.config.SSL_CERT_FILE
            key_file = self.config.SSL_KEY_FILE
            
            if not cert_file.exists() or not key_file.exists():
                checks.append(HealthCheck(
                    name="ssl_certificates",
                    status=HealthStatus.WARNING,
                    message="SSL certificates not found"
                ))
                return checks
            
            # Check certificate expiration (simplified)
            cert_stat = cert_file.stat()
            cert_age_days = (datetime.now() - datetime.fromtimestamp(cert_stat.st_mtime)).days
            
            if cert_age_days > 365:
                checks.append(HealthCheck(
                    name="ssl_certificate_age",
                    status=HealthStatus.WARNING,
                    message=f"SSL certificate is {cert_age_days} days old"
                ))
            else:
                checks.append(HealthCheck(
                    name="ssl_certificate_age",
                    status=HealthStatus.HEALTHY,
                    message=f"SSL certificate is {cert_age_days} days old"
                ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="ssl_certificates",
                status=HealthStatus.WARNING,
                message=f"SSL certificate check failed: {e}"
            ))
        
        return checks
    
    def _check_backup_system(self) -> List[HealthCheck]:
        """Check backup system health"""
        checks = []
        
        try:
            backup_dir = self.config.DATABASE_BACKUP_PATH
            
            if not backup_dir.exists():
                checks.append(HealthCheck(
                    name="backup_directory",
                    status=HealthStatus.WARNING,
                    message="Backup directory does not exist"
                ))
                return checks
            
            # Check for recent backups
            backup_files = list(backup_dir.glob("*.db"))
            
            if not backup_files:
                checks.append(HealthCheck(
                    name="backup_files",
                    status=HealthStatus.WARNING,
                    message="No backup files found"
                ))
                return checks
            
            # Check backup age
            newest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            backup_age_hours = (datetime.now() - datetime.fromtimestamp(newest_backup.stat().st_mtime)).total_seconds() / 3600
            
            backup_status = HealthStatus.HEALTHY
            if backup_age_hours > 48:  # 2 days
                backup_status = HealthStatus.WARNING
            if backup_age_hours > 168:  # 1 week
                backup_status = HealthStatus.CRITICAL
            
            checks.append(HealthCheck(
                name="backup_freshness",
                status=backup_status,
                message=f"Newest backup: {newest_backup.name} ({backup_age_hours:.1f} hours old)",
                value=backup_age_hours,
                threshold=48
            ))
            
            # Check backup count
            backup_count = len(backup_files)
            if backup_count < 3:
                checks.append(HealthCheck(
                    name="backup_count",
                    status=HealthStatus.WARNING,
                    message=f"Only {backup_count} backup files found"
                ))
            else:
                checks.append(HealthCheck(
                    name="backup_count",
                    status=HealthStatus.HEALTHY,
                    message=f"Backup count is good: {backup_count} files"
                ))
                
        except Exception as e:
            checks.append(HealthCheck(
                name="backup_system",
                status=HealthStatus.WARNING,
                message=f"Backup system check failed: {e}"
            ))
        
        return checks
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall health status from individual checks"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        critical_count = sum(1 for check in checks if check.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for check in checks if check.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 2:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def _generate_health_summary(self, checks: List[HealthCheck]) -> Dict[str, Any]:
        """Generate health summary"""
        status_counts = {
            "healthy": sum(1 for check in checks if check.status == HealthStatus.HEALTHY),
            "warning": sum(1 for check in checks if check.status == HealthStatus.WARNING),
            "critical": sum(1 for check in checks if check.status == HealthStatus.CRITICAL),
            "unknown": sum(1 for check in checks if check.status == HealthStatus.UNKNOWN)
        }
        
        total_checks = len(checks)
        healthy_percentage = (status_counts["healthy"] / total_checks) * 100 if total_checks else 0

        headline = "Geen health checks uitgevoerd"
        summary_details: Dict[str, Any] = {}

        if total_checks:
            warning_percent = (status_counts["warning"] / total_checks) * 100
            critical_percent = (status_counts["critical"] / total_checks) * 100
            summary_details = {
                "healthy_percent": healthy_percentage,
                "warning_percent": warning_percent,
                "critical_percent": critical_percent,
            }

            if status_counts["critical"]:
                headline = f"{status_counts['critical']} kritieke checks gedetecteerd"
            elif status_counts["warning"]:
                headline = f"{status_counts['warning']} waarschuwingen gedetecteerd"
            else:
                headline = "Alle health checks zijn groen"

        return {
            "total_checks": total_checks,
            "status_counts": status_counts,
            "health_percentage": healthy_percentage,
            "headline": headline,
            "details": summary_details,
        }
    
    def _generate_recommendations(self, checks: List[HealthCheck]) -> List[str]:
        """Generate recommendations based on health checks"""
        recommendations = []
        
        for check in checks:
            if check.status == HealthStatus.CRITICAL:
                if check.name == "cpu_usage":
                    recommendations.append("High CPU usage detected. Consider optimizing processes or upgrading hardware.")
                elif check.name == "memory_usage":
                    recommendations.append("High memory usage detected. Consider closing unnecessary applications or upgrading RAM.")
                elif check.name == "disk_usage":
                    recommendations.append("High disk usage detected. Consider cleaning up files or expanding storage.")
                elif check.name == "pi_connectivity":
                    recommendations.append("Pi is offline. Check network connection and Pi status.")
                elif check.name == "data_freshness":
                    recommendations.append("Data is stale. Check Pi connectivity and sync status.")
            
            elif check.status == HealthStatus.WARNING:
                if check.name == "backup_freshness":
                    recommendations.append("Backup is getting old. Consider running a manual backup.")
                elif check.name == "ssl_certificate_age":
                    recommendations.append("SSL certificate is getting old. Consider renewing it.")
                elif check.name == "log_file_sizes":
                    recommendations.append("Large log files detected. Consider log rotation.")
        
        return recommendations
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            health for health in self.health_history
            if datetime.fromisoformat(health["timestamp"]) > cutoff_time
        ]
    
    def get_current_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "status": self.health_status.value,
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_history_count": len(self.health_history)
        }

