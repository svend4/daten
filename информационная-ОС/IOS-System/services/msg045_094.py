"""
Comprehensive Audit Logging System
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from ipaddress import ip_address

from sqlalchemy import Column, String, DateTime, JSON, Integer, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.dialects.postgresql import JSONB

from ..models import Base
from ..database import async_session

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types"""
    
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    MFA_ENABLE = "auth.mfa.enable"
    MFA_DISABLE = "auth.mfa.disable"
    MFA_VERIFY = "auth.mfa.verify"
    
    # Documents
    DOCUMENT_CREATE = "document.create"
    DOCUMENT_READ = "document.read"
    DOCUMENT_UPDATE = "document.update"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_DOWNLOAD = "document.download"
    DOCUMENT_SHARE = "document.share"
    
    # Search
    SEARCH_EXECUTE = "search.execute"
    SEARCH_EXPORT = "search.export"
    
    # Users & Permissions
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_SUSPEND = "user.suspend"
    ROLE_ASSIGN = "role.assign"
    ROLE_REVOKE = "role.revoke"
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    
    # Configuration
    CONFIG_CHANGE = "config.change"
    DOMAIN_CREATE = "domain.create"
    DOMAIN_DELETE = "domain.delete"
    
    # Data
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_DELETE_BULK = "data.delete.bulk"
    
    # API
    API_KEY_CREATE = "api.key.create"
    API_KEY_REVOKE = "api.key.revoke"
    
    # Security
    SECURITY_ALERT = "security.alert"
    SECURITY_BREACH = "security.breach"


class AuditSeverity(str, Enum):
    """Audit event severity"""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogModel(Base):
    """Audit log database model"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.INFO.value)
    
    # User context
    user_id = Column(String(100), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Request context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Resource details
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    
    # Event data
    details = Column(JSONB, nullable=True)
    
    # Outcome
    success = Column(String(10), nullable=False)  # 'success', 'failed', 'partial'
    error_message = Column(String(1000), nullable=True)
    
    # Metadata
    duration_ms = Column(Integer, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_timestamp_action', 'timestamp', 'action'),
        Index('ix_audit_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_severity', 'severity', 'timestamp'),
    )


class AuditLogger:
    """
    Audit logging service
    
    Usage:
        audit = AuditLogger()
        
        await audit.log(
            action=AuditAction.DOCUMENT_READ,
            user_id="user123",
            resource_type="document",
            resource_id="doc456",
            details={"title": "Contract.pdf"},
            ip_address=request.client.host
        )
    """
    
    def __init__(self):
        self.session = None
    
    async def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        severity: AuditSeverity = AuditSeverity.INFO
    ):
        """
        Log an audit event
        
        Args:
            action: Action being audited
            user_id: User performing action
            username: Username (for convenience)
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: User agent string
            request_id: Request ID for tracing
            resource_type: Type of resource (document, user, etc.)
            resource_id: Resource identifier
            details: Additional event details
            success: Whether action succeeded
            error_message: Error message if failed
            duration_ms: Action duration in milliseconds
            severity: Event severity
        """
        
        # Determine severity if not explicitly set
        if not success and severity == AuditSeverity.INFO:
            severity = AuditSeverity.ERROR
        
        # Create audit entry
        audit_entry = AuditLogModel(
            timestamp=datetime.utcnow(),
            action=action.value,
            severity=severity.value,
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            success="success" if success else "failed",
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        # Save to database
        try:
            async with async_session() as session:
                session.add(audit_entry)
                await session.commit()
                
                # Also log to application logger
                log_message = self._format_log_message(audit_entry)
                
                if severity == AuditSeverity.CRITICAL:
                    logger.critical(log_message)
                elif severity == AuditSeverity.ERROR:
                    logger.error(log_message)
                elif severity == AuditSeverity.WARNING:
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)
            
            # If audit logging fails, at least log to application log
            logger.error(
                f"AUDIT FAILED: {action.value} by {user_id} on {resource_type}/{resource_id}",
                exc_info=True
            )
    
    def _format_log_message(self, entry: AuditLogModel) -> str:
        """Format audit entry for logging"""
        
        parts = [
            f"action={entry.action}",
            f"user={entry.user_id or 'anonymous'}",
        ]
        
        if entry.resource_type:
            parts.append(f"resource={entry.resource_type}/{entry.resource_id}")
        
        if entry.ip_address:
            parts.append(f"ip={entry.ip_address}")
        
        parts.append(f"result={entry.success}")
        
        if entry.error_message:
            parts.append(f"error={entry.error_message}")
        
        return " ".join(parts)
    
    async def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogModel]:
        """
        Query audit logs
        
        Returns:
            List of audit log entries
        """
        
        async with async_session() as session:
            query = select(AuditLogModel)
            
            # Build filters
            filters = []
            
            if user_id:
                filters.append(AuditLogModel.user_id == user_id)
            
            if action:
                filters.append(AuditLogModel.action == action.value)
            
            if resource_type:
                filters.append(AuditLogModel.resource_type == resource_type)
            
            if resource_id:
                filters.append(AuditLogModel.resource_id == resource_id)
            
            if severity:
                filters.append(AuditLogModel.severity == severity.value)
            
            if start_date:
                filters.append(AuditLogModel.timestamp >= start_date)
            
            if end_date:
                filters.append(AuditLogModel.timestamp <= end_date)
            
            if success_only is not None:
                if success_only:
                    filters.append(AuditLogModel.success == "success")
                else:
                    filters.append(AuditLogModel.success == "failed")
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by timestamp desc
            query = query.order_by(AuditLogModel.timestamp.desc())
            
            # Pagination
            query = query.limit(limit).offset(offset)
            
            # Execute
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit statistics
        
        Returns:
            Statistics dictionary
        """
        
        async with async_session() as session:
            # Base query
            base_query = select(AuditLogModel)
            
            if start_date:
                base_query = base_query.where(AuditLogModel.timestamp >= start_date)
            if end_date:
                base_query = base_query.where(AuditLogModel.timestamp <= end_date)
            
            # Total events
            total_result = await session.execute(
                select(func.count(AuditLogModel.id))
            )
            total = total_result.scalar_one()
            
            # By action
            action_result = await session.execute(
                select(
                    AuditLogModel.action,
                    func.count(AuditLogModel.id)
                )
                .group_by(AuditLogModel.action)
                .order_by(func.count(AuditLogModel.id).desc())
                .limit(10)
            )
            by_action = dict(action_result.all())
            
            # By user
            user_result = await session.execute(
                select(
                    AuditLogModel.user_id,
                    func.count(AuditLogModel.id)
                )
                .where(AuditLogModel.user_id.isnot(None))
                .group_by(AuditLogModel.user_id)
                .order_by(func.count(AuditLogModel.id).desc())
                .limit(10)
            )
            by_user = dict(user_result.all())
            
            # By severity
            severity_result = await session.execute(
                select(
                    AuditLogModel.severity,
                    func.count(AuditLogModel.id)
                )
                .group_by(AuditLogModel.severity)
            )
            by_severity = dict(severity_result.all())
            
            # Failed actions
            failed_result = await session.execute(
                select(func.count(AuditLogModel.id))
                .where(AuditLogModel.success == "failed")
            )
            failed = failed_result.scalar_one()
            
            return {
                "total_events": total,
                "failed_events": failed,
                "success_rate": (total - failed) / total * 100 if total > 0 else 0,
                "by_action": by_action,
                "by_user": by_user,
                "by_severity": by_severity
            }
    
    async def get_security_alerts(
        self,
        hours: int = 24
    ) -> List[AuditLogModel]:
        """
        Get recent security alerts
        
        Args:
            hours: Look back period in hours
        
        Returns:
            List of security-related audit entries
        """
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        async with async_session() as session:
            result = await session.execute(
                select(AuditLogModel)
                .where(
                    and_(
                        AuditLogModel.timestamp >= cutoff,
                        or_(
                            AuditLogModel.severity.in_([
                                AuditSeverity.ERROR.value,
                                AuditSeverity.CRITICAL.value
                            ]),
                            AuditLogModel.action.in_([
                                AuditAction.LOGIN_FAILED.value,
                                AuditAction.SECURITY_ALERT.value,
                                AuditAction.SECURITY_BREACH.value
                            ])
                        )
                    )
                )
                .order_by(AuditLogModel.timestamp.desc())
            )
            
            return result.scalars().all()


# Global audit logger
audit_logger = AuditLogger()