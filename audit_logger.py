#!/usr/bin/env python3
"""
Trading Bot Dashboard - Audit Logging System
Comprehensive audit trail for all dashboard activities
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, Any, Optional
from flask import request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.audit_file = self.log_dir / "audit.jsonl"
        
    def log_activity(self, action: str, details: Dict[str, Any], 
                    user_agent: str = None, ip_address: str = None) -> None:
        """Log an audit event"""
        try:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'details': details,
                'user_agent': user_agent or self._get_user_agent(),
                'ip_address': ip_address or self._get_ip_address(),
                'session_id': self._get_session_id()
            }
            
            # Write to JSONL file (one JSON object per line)
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            # Also log to standard logger
            logger.info(f"🔍 AUDIT: {action} - {details}")
            
        except Exception as e:
            logger.error(f"❌ Audit logging failed: {e}")
    
    def log_sync_activity(self, action: str, success: bool, 
                         error_message: str = None, files_synced: int = 0) -> None:
        """Log sync-related activities"""
        details = {
            'sync_action': action,
            'success': success,
            'files_synced': files_synced,
            'error_message': error_message
        }
        self.log_activity('SYNC_ACTIVITY', details)
    
    def log_api_access(self, endpoint: str, method: str, 
                      response_code: int, response_time_ms: float = None) -> None:
        """Log API access"""
        details = {
            'endpoint': endpoint,
            'method': method,
            'response_code': response_code,
            'response_time_ms': response_time_ms
        }
        self.log_activity('API_ACCESS', details)
    
    def log_data_export(self, export_type: str, file_size: int, 
                       record_count: int = None) -> None:
        """Log data export activities"""
        details = {
            'export_type': export_type,
            'file_size': file_size,
            'record_count': record_count
        }
        self.log_activity('DATA_EXPORT', details)
    
    def log_backup_activity(self, action: str, backup_name: str = None, 
                           success: bool = True, error_message: str = None) -> None:
        """Log backup activities"""
        details = {
            'backup_action': action,
            'backup_name': backup_name,
            'success': success,
            'error_message': error_message
        }
        self.log_activity('BACKUP_ACTIVITY', details)
    
    def log_security_event(self, event_type: str, severity: str, 
                          details: Dict[str, Any]) -> None:
        """Log security-related events"""
        security_details = {
            'event_type': event_type,
            'severity': severity,
            **details
        }
        self.log_activity('SECURITY_EVENT', security_details)
    
    def log_configuration_change(self, config_type: str, 
                                old_value: Any, new_value: Any) -> None:
        """Log configuration changes"""
        details = {
            'config_type': config_type,
            'old_value': str(old_value),
            'new_value': str(new_value)
        }
        self.log_activity('CONFIG_CHANGE', details)
    
    def get_audit_logs(self, action_filter: str = None, 
                      start_date: datetime = None, 
                      end_date: datetime = None, 
                      limit: int = 100) -> list:
        """Retrieve audit logs with optional filtering"""
        try:
            logs = []
            
            if not self.audit_file.exists():
                return logs
            
            with open(self.audit_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if action_filter and log_entry.get('action') != action_filter:
                            continue
                        
                        if start_date:
                            log_time = datetime.fromisoformat(log_entry['timestamp'])
                            if log_time < start_date:
                                continue
                        
                        if end_date:
                            log_time = datetime.fromisoformat(log_entry['timestamp'])
                            if log_time > end_date:
                                continue
                        
                        logs.append(log_entry)
                        
                        if len(logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Error retrieving audit logs: {e}")
            return []
    
    def get_audit_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get audit summary for the last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logs = self.get_audit_logs(start_date=start_date, end_date=end_date, limit=1000)
            
            # Count by action type
            action_counts = {}
            api_calls = 0
            sync_activities = 0
            security_events = 0
            
            for log in logs:
                action = log.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
                
                if action == 'API_ACCESS':
                    api_calls += 1
                elif action == 'SYNC_ACTIVITY':
                    sync_activities += 1
                elif action == 'SECURITY_EVENT':
                    security_events += 1
            
            return {
                'period_days': days,
                'total_events': len(logs),
                'action_breakdown': action_counts,
                'api_calls': api_calls,
                'sync_activities': sync_activities,
                'security_events': security_events,
                'unique_ips': len(set(log.get('ip_address') for log in logs if log.get('ip_address')))
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating audit summary: {e}")
            return {}
    
    def _get_user_agent(self) -> str:
        """Get user agent from Flask request context"""
        try:
            if request:
                return request.headers.get('User-Agent', 'Unknown')
        except:
            pass
        return 'System'
    
    def _get_ip_address(self) -> str:
        """Get IP address from Flask request context"""
        try:
            if request:
                return request.remote_addr or 'Unknown'
        except:
            pass
        return '127.0.0.1'
    
    def _get_session_id(self) -> str:
        """Get session ID if available"""
        try:
            if request and hasattr(request, 'cookies'):
                return request.cookies.get('session', 'No-Session')
        except:
            pass
        return 'No-Session'


# Global audit logger instance
audit_logger = AuditLogger()


def log_sync_activity(action: str, success: bool, error_message: str = None, files_synced: int = 0):
    """Convenience function for sync logging"""
    audit_logger.log_sync_activity(action, success, error_message, files_synced)


def log_api_access(endpoint: str, method: str, response_code: int, response_time_ms: float = None):
    """Convenience function for API logging"""
    audit_logger.log_api_access(endpoint, method, response_code, response_time_ms)


def log_security_event(event_type: str, severity: str, details: Dict[str, Any]):
    """Convenience function for security logging"""
    audit_logger.log_security_event(event_type, severity, details)


if __name__ == "__main__":
    # Test the audit logger
    audit_logger = AuditLogger()
    
    # Test various log types
    audit_logger.log_sync_activity('MANUAL_SYNC', True, files_synced=5)
    audit_logger.log_api_access('/api/portfolio', 'GET', 200, 150.5)
    audit_logger.log_security_event('FAILED_LOGIN', 'HIGH', {'attempts': 3})
    
    # Show summary
    summary = audit_logger.get_audit_summary(1)
    print(f"Audit Summary: {summary}")
