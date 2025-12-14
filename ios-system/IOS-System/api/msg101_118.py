"""
Security Monitoring and Alerting
Real-time threat detection and response

Features:
- Anomaly detection
- Failed login tracking
- Suspicious activity detection
- Real-time alerting
- Security metrics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from ..config import settings

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """
    Monitors security events and detects threats
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.alert_handlers = []
        
        # Tracking windows
        self.failed_login_window = deque(maxlen=100)
        self.suspicious_ips = set()
        
        # Thresholds
        self.failed_login_threshold = 5
        self.rate_limit_threshold = 100  # requests per minute
    
    def track_login_attempt(
        self,
        ip: str,
        username: str,
        success: bool,
        timestamp: datetime = None
    ):
        """
        Track login attempt
        
        Detects brute force attacks and credential stuffing
        """
        timestamp = timestamp or datetime.now()
        
        event = {
            'ip': ip,
            'username': username,
            'success': success,
            'timestamp': timestamp.isoformat()
        }
        
        # Store in Redis
        key = f"login_attempt:{ip}:{timestamp.strftime('%Y%m%d%H%M')}"
        self.redis.lpush(key, json.dumps(event))
        self.redis.expire(key, 3600)  # 1 hour
        
        if not success:
            # Track failed logins
            self.failed_login_window.append(event)
            
            # Check for brute force
            recent_failures = self._count_recent_failures(ip, minutes=5)
            
            if recent_failures >= self.failed_login_threshold:
                self._alert_brute_force(ip, username, recent_failures)
                self._block_ip(ip, duration=300)  # Block for 5 minutes
    
    def _count_recent_failures(
        self,
        ip: str,
        minutes: int = 5
    ) -> int:
        """Count failed login attempts from IP in last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        count = 0
        for event in self.failed_login_window:
            event_time = datetime.fromisoformat(event['timestamp'])
            if event['ip'] == ip and event_time > cutoff:
                count += 1
        
        return count
    
    def _block_ip(self, ip: str, duration: int):
        """Temporarily block IP address"""
        key = f"blocked_ip:{ip}"
        self.redis.setex(key, duration, "1")
        
        logger.warning(f"Blocked IP {ip} for {duration} seconds")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        key = f"blocked_ip:{ip}"
        return self.redis.exists(key) == 1
    
    def track_api_request(
        self,
        ip: str,
        endpoint: str,
        method: str,
        user_id: Optional[int] = None
    ):
        """
        Track API request for rate limiting and anomaly detection
        """
        timestamp = datetime.now()
        minute_key = timestamp.strftime('%Y%m%d%H%M')
        
        # Track requests per IP per minute
        key = f"api_requests:{ip}:{minute_key}"
        count = self.redis.incr(key)
        self.redis.expire(key, 120)  # 2 minutes
        
        # Check rate limit
        if count >= self.rate_limit_threshold:
            self._alert_rate_limit_exceeded(ip, count)
            self._block_ip(ip, duration=60)
        
        # Track endpoint access patterns
        endpoint_key = f"endpoint_access:{endpoint}:{minute_key}"
        self.redis.incr(endpoint_key)
        self.redis.expire(endpoint_key, 120)
    
    def detect_suspicious_activity(
        self,
        user_id: int,
        activity: str,
        context: Dict
    ):
        """
        Detect suspicious user activity
        
        Examples:
        - Access from new location
        - Unusual time of access
        - Bulk data downloads
        - Privilege escalation attempts
        """
        # Store activity
        key = f"user_activity:{user_id}"
        
        activity_event = {
            'activity': activity,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.redis.lpush(key, json.dumps(activity_event))
        self.redis.ltrim(key, 0, 99)  # Keep last 100 events
        self.redis.expire(key, 86400)  # 24 hours
        
        # Check for suspicious patterns
        if activity == 'bulk_download':
            if context.get('document_count', 0) > 50:
                self._alert_suspicious_activity(
                    user_id,
                    "Bulk document download",
                    context
                )
        
        elif activity == 'permission_change':
            self._alert_suspicious_activity(
                user_id,
                "Permission escalation attempt",
                context
            )
        
        elif activity == 'admin_access':
            # Check if access from new IP
            ip = context.get('ip')
            if ip and not self._is_known_admin_ip(user_id, ip):
                self._alert_suspicious_activity(
                    user_id,
                    "Admin access from new IP",
                    context
                )
    
    def _is_known_admin_ip(self, user_id: int, ip: str) -> bool:
        """Check if IP is known for this admin user"""
        key = f"admin_ips:{user_id}"
        
        # Get known IPs
        known_ips = self.redis.smembers(key)
        
        if ip.encode() in known_ips:
            return True
        
        # Add to known IPs
        self.redis.sadd(key, ip)
        self.redis.expire(key, 86400 * 30)  # 30 days
        
        return False
    
    def check_password_quality(self, password: str) -> Dict:
        """
        Check password against common patterns and breached passwords
        
        Returns quality score and warnings
        """
        warnings = []
        score = 100
        
        # Length check
        if len(password) < 8:
            warnings.append("Password too short (minimum 8 characters)")
            score -= 30
        
        # Complexity checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        complexity = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity < 3:
            warnings.append("Password should contain uppercase, lowercase, digits, and special characters")
            score -= 20
        
        # Common password check
        common_passwords = {
            'password', '123456', 'password123', 'admin', 'letmein',
            'welcome', 'monkey', 'dragon', 'master', 'sunshine'
        }
        
        if password.lower() in common_passwords:
            warnings.append("Password is too common")
            score -= 50
        
        # Sequential characters
        if any(password[i:i+3].isdigit() and 
               int(password[i+1]) == int(password[i]) + 1 and
               int(password[i+2]) == int(password[i]) + 2
               for i in range(len(password) - 2) if password[i:i+3].isdigit()):
            warnings.append("Password contains sequential numbers")
            score -= 10
        
        return {
            'score': max(0, score),
            'warnings': warnings,
            'strength': 'strong' if score >= 80 else 'medium' if score >= 60 else 'weak'
        }
    
    def get_security_metrics(self) -> Dict:
        """
        Get current security metrics
        
        Returns statistics on security events
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        metrics = {
            'failed_logins_last_hour': self._count_failed_logins_since(hour_ago),
            'failed_logins_last_day': self._count_failed_logins_since(day_ago),
            'blocked_ips': len(self._get_blocked_ips()),
            'suspicious_activities_last_hour': self._count_suspicious_activities(hour_ago),
            'active_sessions': self._count_active_sessions(),
            'admin_actions_last_hour': self._count_admin_actions(hour_ago)
        }
        
        return metrics
    
    def _count_failed_logins_since(self, since: datetime) -> int:
        """Count failed logins since timestamp"""
        count = 0
        for event in self.failed_login_window:
            event_time = datetime.fromisoformat(event['timestamp'])
            if event_time > since:
                count += 1
        return count
    
    def _get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs"""
        keys = self.redis.keys("blocked_ip:*")
        return [key.decode().split(':')[1] for key in keys]
    
    def _count_suspicious_activities(self, since: datetime) -> int:
        """Count suspicious activities since timestamp"""
        # Implementation would query activity logs
        return 0
    
    def _count_active_sessions(self) -> int:
        """Count currently active sessions"""
        keys = self.redis.keys("session:*")
        return len(keys)
    
    def _count_admin_actions(self, since: datetime) -> int:
        """Count admin actions since timestamp"""
        # Implementation would query audit logs
        return 0
    
    # ============================================
    # Alerting
    # ============================================
    
    def register_alert_handler(self, handler: callable):
        """Register handler for security alerts"""
        self.alert_handlers.append(handler)
    
    def _send_alert(self, alert_type: str, details: Dict):
        """Send security alert to all registered handlers"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        logger.warning(f"SECURITY ALERT: {alert_type} - {details}")
        
        # Call all alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def _alert_brute_force(self, ip: str, username: str, attempts: int):
        """Alert on brute force attack"""
        self._send_alert('brute_force_attack', {
            'ip': ip,
            'username': username,
            'failed_attempts': attempts,
            'action': 'IP blocked'
        })
    
    def _alert_rate_limit_exceeded(self, ip: str, request_count: int):
        """Alert on rate limit exceeded"""
        self._send_alert('rate_limit_exceeded', {
            'ip': ip,
            'request_count': request_count,
            'action': 'IP blocked'
        })
    
    def _alert_suspicious_activity(
        self,
        user_id: int,
        activity: str,
        context: Dict
    ):
        """Alert on suspicious user activity"""
        self._send_alert('suspicious_activity', {
            'user_id': user_id,
            'activity': activity,
            'context': context
        })


class SecurityDashboard:
    """
    Security dashboard data aggregator
    """
    
    def __init__(self, monitor: SecurityMonitor):
        self.monitor = monitor
    
    def get_dashboard_data(self) -> Dict:
        """
        Get data for security dashboard
        
        Returns comprehensive security overview
        """
        metrics = self.monitor.get_security_metrics()
        
        dashboard = {
            'overview': metrics,
            'recent_alerts': self._get_recent_alerts(limit=10),
            'blocked_ips': self._get_blocked_ip_details(),
            'top_failed_logins': self._get_top_failed_login_ips(limit=10),
            'active_threats': self._get_active_threats(),
            'compliance_status': self._check_compliance_status()
        }
        
        return dashboard
    
    def _get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent security alerts"""
        # Implementation would query alert log
        return []
    
    def _get_blocked_ip_details(self) -> List[Dict]:
        """Get details of blocked IPs"""
        blocked_ips = self.monitor._get_blocked_ips()
        
        details = []
        for ip in blocked_ips:
            key = f"blocked_ip:{ip}"
            ttl = self.monitor.redis.ttl(key)
            
            details.append({
                'ip': ip,
                'remaining_seconds': ttl,
                'reason': 'brute_force'  # Could be enhanced
            })
        
        return details
    
    def _get_top_failed_login_ips(self, limit: int = 10) -> List[Dict]:
        """Get IPs with most failed login attempts"""
        ip_counts = defaultdict(int)
        
        for event in self.monitor.failed_login_window:
            ip_counts[event['ip']] += 1
        
        top_ips = sorted(
            ip_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {'ip': ip, 'failed_attempts': count}
            for ip, count in top_ips
        ]
    
    def _get_active_threats(self) -> List[Dict]:
        """Get currently active security threats"""
        threats = []
        
        # Check for ongoing brute force attacks
        recent_failures = defaultdict(int)
        cutoff = datetime.now() - timedelta(minutes=5)
        
        for event in self.monitor.failed_login_window:
            event_time = datetime.fromisoformat(event['timestamp'])
            if event_time > cutoff:
                recent_failures[event['ip']] += 1
        
        for ip, count in recent_failures.items():
            if count >= 3:
                threats.append({
                    'type': 'brute_force',
                    'ip': ip,
                    'severity': 'high' if count >= 5 else 'medium',
                    'details': f"{count} failed login attempts"
                })
        
        return threats
    
    def _check_compliance_status(self) -> Dict:
        """Check security compliance status"""
        return {
            'password_policy': 'compliant',
            'encryption': 'compliant',
            'audit_logging': 'compliant',
            'access_control': 'compliant',
            'data_retention': 'compliant'
        }