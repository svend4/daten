"""
Security Monitoring & Alerting
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from .audit_log import audit_logger, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """
    Monitor security events and trigger alerts
    
    Detects:
    - Brute force login attempts
    - Suspicious activity patterns
    - Permission escalation attempts
    - Mass data exports
    - Configuration changes
    """
    
    # Thresholds
    FAILED_LOGIN_THRESHOLD = 5  # Failed logins in time window
    FAILED_LOGIN_WINDOW = 300  # 5 minutes
    
    MASS_EXPORT_THRESHOLD = 10  # Exports in time window
    MASS_EXPORT_WINDOW = 3600  # 1 hour
    
    def __init__(self):
        self.failed_logins = defaultdict(list)  # IP -> timestamps
        self.exports = defaultdict(list)  # user_id -> timestamps
        self.monitoring = False
    
    async def start_monitoring(self):
        """Start continuous security monitoring"""
        
        self.monitoring = True
        logger.info("Security monitoring started")
        
        while self.monitoring:
            try:
                await self._check_security_events()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}", exc_info=True)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Security monitoring stopped")
    
    async def _check_security_events(self):
        """Check for security events"""
        
        # Get recent alerts
        alerts = await audit_logger.get_security_alerts(hours=1)
        
        for alert in alerts:
            # Check for brute force
            if alert.action == AuditAction.LOGIN_FAILED.value:
                await self._check_brute_force(alert)
            
            # Check for suspicious exports
            elif alert.action == AuditAction.DATA_EXPORT.value:
                await self._check_mass_export(alert)
            
            # Check for privilege escalation
            elif alert.action in [
                AuditAction.ROLE_ASSIGN.value,
                AuditAction.PERMISSION_GRANT.value
            ]:
                await self._check_privilege_escalation(alert)
    
    async def _check_brute_force(self, alert):
        """Check for brute force login attempts"""
        
        ip = alert.ip_address
        if not ip:
            return
        
        # Add to tracking
        now = datetime.utcnow().timestamp()
        self.failed_logins[ip].append(now)
        
        # Clean old entries
        cutoff = now - self.FAILED_LOGIN_WINDOW
        self.failed_logins[ip] = [
            ts for ts in self.failed_logins[ip]
            if ts > cutoff
        ]
        
        # Check threshold
        if len(self.failed_logins[ip]) >= self.FAILED_LOGIN_THRESHOLD:
            await self._trigger_alert(
                "Brute Force Attack Detected",
                f"IP {ip} has {len(self.failed_logins[ip])} failed login attempts "
                f"in the last {self.FAILED_LOGIN_WINDOW // 60} minutes",
                severity=AuditSeverity.CRITICAL,
                details={
                    "ip_address": ip,
                    "attempts": len(self.failed_logins[ip]),
                    "window_seconds": self.FAILED_LOGIN_WINDOW
                }
            )
            
            # Clear to avoid duplicate alerts
            self.failed_logins[ip] = []
    
    async def _check_mass_export(self, alert):
        """Check for mass data exports"""
        
        user_id = alert.user_id
        if not user_id:
            return
        
        # Add to tracking
        now = datetime.utcnow().timestamp()
        self.exports[user_id].append(now)
        
        # Clean old entries
        cutoff = now - self.MASS_EXPORT_WINDOW
        self.exports[user_id] = [
            ts for ts in self.exports[user_id]
            if ts > cutoff
        ]
        
        # Check threshold
        if len(self.exports[user_id]) >= self.MASS_EXPORT_THRESHOLD:
            await self._trigger_alert(
                "Mass Data Export Detected",
                f"User {user_id} has exported data {len(self.exports[user_id])} times "
                f"in the last {self.MASS_EXPORT_WINDOW // 60} minutes",
                severity=AuditSeverity.WARNING,
                details={
                    "user_id": user_id,
                    "exports": len(self.exports[user_id]),
                    "window_seconds": self.MASS_EXPORT_WINDOW
                }
            )
            
            self.exports[user_id] = []
    
    async def _check_privilege_escalation(self, alert):
        """Check for potential privilege escalation"""
        
        # Log suspicious privilege changes
        if alert.severity in [AuditSeverity.ERROR.value, AuditSeverity.CRITICAL.value]:
            await self._trigger_alert(
                "Suspicious Privilege Change",
                f"Privilege change by {alert.user_id} flagged as suspicious",
                severity=AuditSeverity.WARNING,
                details={
                    "user_id": alert.user_id,
                    "action": alert.action,
                    "resource": f"{alert.resource_type}/{alert.resource_id}"
                }
            )
    
    async def _trigger_alert(
        self,
        title: str,
        message: str,
        severity: AuditSeverity,
        details: Optional[Dict] = None
    ):
        """Trigger security alert"""
        
        logger.warning(f"SECURITY ALERT: {title} - {message}")
        
        # Log to audit
        await audit_logger.log(
            action=AuditAction.SECURITY_ALERT,
            user_id="system",
            details={
                "title": title,
                "message": message,
                **(details or {})
            },
            success=True,
            severity=severity
        )
        
        # Send notifications (email, Slack, etc.)
        await self._send_notification(title, message, severity, details)
    
    async def _send_notification(
        self,
        title: str,
        message: str,
        severity: AuditSeverity,
        details: Optional[Dict] = None
    ):
        """Send alert notification"""
        
        # TODO: Implement notification channels
        # - Email to admins
        # - Slack webhook
        # - PagerDuty (for critical)
        # - Sentry
        
        # For now, just log
        logger.info(f"Notification sent: {title}")


# Global security monitor
security_monitor = SecurityMonitor()