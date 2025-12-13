Отлично! Продолжаем с Day 117-118: Security Enhancement. Это включает:
1. Comprehensive Audit Logging
2. Two-Factor Authentication (2FA/MFA)
3. Advanced RBAC
4. Security monitoring
5. Compliance features

Создам детальную реализацию этих компонентов.# 🔒 DAY 117-118: SECURITY ENHANCEMENT

---

## 📊 ЦЕЛЬ

Усилить безопасность системы через:
- Comprehensive Audit Logging (все действия пользователей)
- Two-Factor Authentication (2FA/MFA)
- Enhanced RBAC с fine-grained permissions
- Security monitoring и alerting
- Compliance готовность (GDPR, SOC2)

---

## ФАЙЛ 63: `ios_core/security/audit_log.py`

```python
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
```

---

## ФАЙЛ 64: `ios_core/security/mfa.py`

```python
"""
Multi-Factor Authentication (MFA) / Two-Factor Authentication (2FA)
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
import base64

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Base
from ..database import async_session

logger = logging.getLogger(__name__)


class MFASecretModel(Base):
    """MFA secret storage"""
    
    __tablename__ = "mfa_secrets"
    
    user_id = Column(String(100), primary_key=True)
    secret = Column(String(32), nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(String(500), nullable=True)  # Comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)


class MFAManager:
    """
    Multi-Factor Authentication Manager
    
    Supports:
    - TOTP (Time-based One-Time Password) via Google Authenticator, Authy, etc.
    - Backup codes for recovery
    
    Usage:
        mfa = MFAManager()
        
        # Setup MFA for user
        qr_code = await mfa.setup_mfa(
            user_id="user123",
            user_email="user@example.com"
        )
        
        # User scans QR code with authenticator app
        
        # Verify initial code
        valid = await mfa.verify_code(user_id="user123", code="123456")
        if valid:
            await mfa.enable_mfa(user_id="user123")
        
        # Subsequent logins
        valid = await mfa.verify_code(user_id="user123", code="654321")
    """
    
    def __init__(self, issuer_name: str = "IOS System"):
        self.issuer_name = issuer_name
    
    async def setup_mfa(
        self,
        user_id: str,
        user_email: str
    ) -> Dict[str, str]:
        """
        Setup MFA for user
        
        Args:
            user_id: User identifier
            user_email: User email (displayed in authenticator app)
        
        Returns:
            Dictionary with QR code image and secret
        """
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        # Save to database (not enabled yet)
        async with async_session() as session:
            mfa_secret = MFASecretModel(
                user_id=user_id,
                secret=secret,
                enabled=False,
                backup_codes=",".join(backup_codes)
            )
            
            # Upsert
            await session.merge(mfa_secret)
            await session.commit()
        
        logger.info(f"MFA setup initiated for user: {user_id}")
        
        return {
            "qr_code": qr_code_base64,
            "secret": secret,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    async def verify_code(
        self,
        user_id: str,
        code: str,
        allow_backup: bool = True
    ) -> bool:
        """
        Verify TOTP code or backup code
        
        Args:
            user_id: User identifier
            code: 6-digit TOTP code or backup code
            allow_backup: Allow backup codes
        
        Returns:
            True if valid
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(MFASecretModel).where(MFASecretModel.user_id == user_id)
            )
            mfa_secret = result.scalar_one_or_none()
            
            if not mfa_secret:
                logger.warning(f"MFA not setup for user: {user_id}")
                return False
            
            # Try TOTP code
            totp = pyotp.TOTP(mfa_secret.secret)
            
            if totp.verify(code, valid_window=1):  # Allow 1 interval before/after
                # Update last used
                mfa_secret.last_used = datetime.utcnow()
                await session.commit()
                
                logger.info(f"MFA code verified for user: {user_id}")
                return True
            
            # Try backup code
            if allow_backup and mfa_secret.backup_codes:
                backup_codes = mfa_secret.backup_codes.split(",")
                
                if code in backup_codes:
                    # Remove used backup code
                    backup_codes.remove(code)
                    mfa_secret.backup_codes = ",".join(backup_codes)
                    mfa_secret.last_used = datetime.utcnow()
                    await session.commit()
                    
                    logger.warning(
                        f"Backup code used for user: {user_id}. "
                        f"Remaining: {len(backup_codes)}"
                    )
                    return True
            
            logger.warning(f"Invalid MFA code for user: {user_id}")
            return False
    
    async def enable_mfa(self, user_id: str) -> bool:
        """
        Enable MFA after initial verification
        
        Args:
            user_id: User identifier
        
        Returns:
            Success status
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(MFASecretModel).where(MFASecretModel.user_id == user_id)
            )
            mfa_secret = result.scalar_one_or_none()
            
            if not mfa_secret:
                return False
            
            mfa_secret.enabled = True
            mfa_secret.verified_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"MFA enabled for user: {user_id}")
            return True
    
    async def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Success status
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(MFASecretModel).where(MFASecretModel.user_id == user_id)
            )
            mfa_secret = result.scalar_one_or_none()
            
            if not mfa_secret:
                return False
            
            # Delete MFA secret
            await session.delete(mfa_secret)
            await session.commit()
            
            logger.warning(f"MFA disabled for user: {user_id}")
            return True
    
    async def is_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for user"""
        
        async with async_session() as session:
            result = await session.execute(
                select(MFASecretModel.enabled)
                .where(MFASecretModel.user_id == user_id)
            )
            enabled = result.scalar_one_or_none()
            
            return enabled == True
    
    async def regenerate_backup_codes(
        self,
        user_id: str
    ) -> Optional[List[str]]:
        """
        Regenerate backup codes
        
        Args:
            user_id: User identifier
        
        Returns:
            New backup codes
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(MFASecretModel).where(MFASecretModel.user_id == user_id)
            )
            mfa_secret = result.scalar_one_or_none()
            
            if not mfa_secret:
                return None
            
            # Generate new codes
            backup_codes = self._generate_backup_codes()
            mfa_secret.backup_codes = ",".join(backup_codes)
            await session.commit()
            
            logger.info(f"Backup codes regenerated for user: {user_id}")
            return backup_codes
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        
        import secrets
        
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(
                secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
                for _ in range(8)
            )
            codes.append(code)
        
        return codes


# Global MFA manager
mfa_manager = MFAManager()
```

---

## ФАЙЛ 65: `api/routes/auth_enhanced.py`

```python
"""
Enhanced authentication with MFA
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr

from ios_core.security.mfa import mfa_manager
from ios_core.security.audit_log import audit_logger, AuditAction, AuditSeverity
from ..dependencies import get_current_user

router = APIRouter()


class MFASetupResponse(BaseModel):
    qr_code: str
    secret: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str


class MFAStatusResponse(BaseModel):
    enabled: bool
    last_used: Optional[datetime] = None


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Setup MFA for current user
    
    Returns QR code to scan with authenticator app
    """
    
    user_id = current_user["username"]
    user_email = current_user.get("email", f"{user_id}@example.com")
    
    # Setup MFA
    mfa_data = await mfa_manager.setup_mfa(user_id, user_email)
    
    # Audit log
    await audit_logger.log(
        action=AuditAction.MFA_ENABLE,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        success=True
    )
    
    return MFASetupResponse(**mfa_data)


@router.post("/mfa/verify")
async def verify_mfa(
    verify_request: MFAVerifyRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify MFA code and enable MFA
    """
    
    user_id = current_user["username"]
    
    # Verify code
    valid = await mfa_manager.verify_code(user_id, verify_request.code)
    
    if not valid:
        # Audit failed verification
        await audit_logger.log(
            action=AuditAction.MFA_VERIFY,
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            success=False,
            severity=AuditSeverity.WARNING
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )
    
    # Enable MFA
    await mfa_manager.enable_mfa(user_id)
    
    # Audit successful verification
    await audit_logger.log(
        action=AuditAction.MFA_VERIFY,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        success=True
    )
    
    return {"message": "MFA enabled successfully"}


@router.delete("/mfa")
async def disable_mfa(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable MFA for current user
    """
    
    user_id = current_user["username"]
    
    # Disable MFA
    success = await mfa_manager.disable_mfa(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA not enabled"
        )
    
    # Audit
    await audit_logger.log(
        action=AuditAction.MFA_DISABLE,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        success=True,
        severity=AuditSeverity.WARNING
    )
    
    return {"message": "MFA disabled"}


@router.get("/mfa/status", response_model=MFAStatusResponse)
async def mfa_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get MFA status for current user
    """
    
    user_id = current_user["username"]
    
    enabled = await mfa_manager.is_enabled(user_id)
    
    return MFAStatusResponse(enabled=enabled)


@router.post("/mfa/regenerate-backup-codes")
async def regenerate_backup_codes(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Regenerate backup codes
    """
    
    user_id = current_user["username"]
    
    codes = await mfa_manager.regenerate_backup_codes(user_id)
    
    if not codes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA not enabled"
        )
    
    # Audit
    await audit_logger.log(
        action=AuditAction.MFA_ENABLE,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        details={"action": "regenerate_backup_codes"},
        success=True,
        severity=AuditSeverity.WARNING
    )
    
    return {"backup_codes": codes}
```

---

## ФАЙЛ 66: `api/routes/audit.py`

```python
"""
Audit log API endpoints
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from ios_core.security.audit_log import (
    audit_logger,
    AuditAction,
    AuditSeverity,
    AuditLogModel
)
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    severity: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: dict
    success: str
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class AuditStatisticsResponse(BaseModel):
    total_events: int
    failed_events: int
    success_rate: float
    by_action: dict
    by_user: dict
    by_severity: dict


@router.get("/logs", response_model=List[AuditLogResponse])
@require_permission(Permission.ADMIN_SYSTEM)
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),  # Max 30 days
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Query audit logs
    
    Requires: ADMIN_SYSTEM permission
    """
    
    # Calculate time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)
    
    # Convert action string to enum if provided
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
    
    # Convert severity string to enum if provided
    severity_enum = None
    if severity:
        try:
            severity_enum = AuditSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}"
            )
    
    # Query logs
    logs = await audit_logger.query(
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        severity=severity_enum,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return [AuditLogResponse.from_orm(log) for log in logs]


@router.get("/statistics", response_model=AuditStatisticsResponse)
@require_permission(Permission.ADMIN_SYSTEM)
async def get_audit_statistics(
    hours: int = Query(24, ge=1, le=720),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit statistics
    
    Requires: ADMIN_SYSTEM permission
    """
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)
    
    stats = await audit_logger.get_statistics(
        start_date=start_date,
        end_date=end_date
    )
    
    return AuditStatisticsResponse(**stats)


@router.get("/security-alerts", response_model=List[AuditLogResponse])
@require_permission(Permission.ADMIN_SYSTEM)
async def get_security_alerts(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent security alerts
    
    Returns audit entries with ERROR or CRITICAL severity,
    and security-related events.
    
    Requires: ADMIN_SYSTEM permission
    """
    
    alerts = await audit_logger.get_security_alerts(hours=hours)
    
    return [AuditLogResponse.from_orm(alert) for alert in alerts]


@router.get("/my-activity", response_model=List[AuditLogResponse])
async def get_my_activity(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's activity
    
    Any user can view their own audit trail
    """
    
    user_id = current_user["username"]
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)
    
    logs = await audit_logger.query(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return [AuditLogResponse.from_orm(log) for log in logs]
```

---

## ФАЙЛ 67: `api/middleware/audit_middleware.py`

```python
"""
Middleware for automatic audit logging
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ios_core.security.audit_log import audit_logger, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Automatically log all API requests
    """
    
    # Actions to audit
    AUDIT_ACTIONS = {
        ("POST", "/api/auth/token"): AuditAction.LOGIN_SUCCESS,
        ("POST", "/api/auth/logout"): AuditAction.LOGOUT,
        ("POST", "/api/documents/upload"): AuditAction.DOCUMENT_CREATE,
        ("GET", "/api/documents/{id}"): AuditAction.DOCUMENT_READ,
        ("PUT", "/api/documents/{id}"): AuditAction.DOCUMENT_UPDATE,
        ("DELETE", "/api/documents/{id}"): AuditAction.DOCUMENT_DELETE,
        ("POST", "/api/search"): AuditAction.SEARCH_EXECUTE,
        ("POST", "/api/data/export"): AuditAction.DATA_EXPORT,
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Get user info if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("username")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Determine if should audit
            action = self._get_audit_action(method, path)
            
            if action:
                # Log successful request
                await audit_logger.log(
                    action=action,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_id=request.headers.get("x-request-id"),
                    success=response.status_code < 400,
                    duration_ms=duration_ms,
                    severity=self._get_severity(response.status_code)
                )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log failed request
            action = self._get_audit_action(method, path)
            
            if action:
                await audit_logger.log(
                    action=action,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_id=request.headers.get("x-request-id"),
                    success=False,
                    error_message=str(e),
                    duration_ms=duration_ms,
                    severity=AuditSeverity.ERROR
                )
            
            raise
    
    def _get_audit_action(self, method: str, path: str) -> Optional[AuditAction]:
        """Determine audit action for request"""
        
        # Check exact match
        key = (method, path)
        if key in self.AUDIT_ACTIONS:
            return self.AUDIT_ACTIONS[key]
        
        # Check pattern match (simple implementation)
        for (m, p), action in self.AUDIT_ACTIONS.items():
            if method == m and self._path_matches(path, p):
                return action
        
        return None
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Simple path pattern matching"""
        
        path_parts = path.split("/")
        pattern_parts = pattern.split("/")
        
        if len(path_parts) != len(pattern_parts):
            return False
        
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Wildcard
            if path_part != pattern_part:
                return False
        
        return True
    
    def _get_severity(self, status_code: int) -> AuditSeverity:
        """Determine severity from status code"""
        
        if status_code >= 500:
            return AuditSeverity.ERROR
        elif status_code >= 400:
            return AuditSeverity.WARNING
        else:
            return AuditSeverity.INFO
```

---

## ФАЙЛ 68: `scripts/setup_security.sh`

```bash
#!/bin/bash
# Setup enhanced security features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         SECURITY ENHANCEMENT SETUP                         ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}[1/5] Creating database migrations...${NC}"

# Create Alembic migration for audit logs
cat > alembic/versions/004_add_security_tables.py << 'EOF'
"""Add security tables (audit logs, MFA)

Revision ID: 004
Revises: 003
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True, index=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('success', sa.String(10), nullable=False),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_timestamp_action', 'audit_logs', ['timestamp', 'action'])
    op.create_index('ix_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_severity', 'audit_logs', ['severity', 'timestamp'])
    
    # MFA secrets table
    op.create_table(
        'mfa_secrets',
        sa.Column('user_id', sa.String(100), primary_key=True),
        sa.Column('secret', sa.String(32), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=False, nullable=False),
        sa.Column('backup_codes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_table('mfa_secrets')
    op.drop_table('audit_logs')
EOF

echo -e "${GREEN}✓ Migration created${NC}"

echo -e "\n${YELLOW}[2/5] Running migrations...${NC}"

alembic upgrade head

echo -e "${GREEN}✓ Migrations applied${NC}"

echo -e "\n${YELLOW}[3/5] Installing dependencies...${NC}"

pip install pyotp qrcode pillow --quiet

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "\n${YELLOW}[4/5] Testing audit logging...${NC}"

python -c "
import asyncio
from ios_core.security.audit_log import audit_logger, AuditAction

async def test():
    await audit_logger.log(
        action=AuditAction.SECURITY_ALERT,
        user_id='system',
        details={'test': 'Security setup complete'},
        success=True
    )
    print('Audit log test successful')

asyncio.run(test())
"

echo -e "${GREEN}✓ Audit logging works${NC}"

echo -e "\n${YELLOW}[5/5] Testing MFA...${NC}"

python -c "
import asyncio
from ios_core.security.mfa import mfa_manager

async def test():
    result = await mfa_manager.setup_mfa('test_user', 'test@example.com')
    print(f'MFA setup successful. Secret: {result[\"secret\"][:8]}...')

asyncio.run(test())
"

echo -e "${GREEN}✓ MFA works${NC}"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            SECURITY ENHANCEMENT COMPLETE                   ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}Features enabled:${NC}"
echo "  ✓ Comprehensive audit logging"
echo "  ✓ Two-factor authentication (2FA)"
echo "  ✓ Security monitoring"
echo "  ✓ Compliance tracking"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Restart IOS API server"
echo "  2. Enable MFA for admin users"
echo "  3. Review audit logs in Kibana"
echo "  4. Configure security alerts"

echo -e "\n${GREEN}Done!${NC}"
```

---

## ФАЙЛ 69: `tests/security/test_mfa.py`

```python
"""
Tests for MFA
"""

import pytest
import pyotp

from ios_core.security.mfa import mfa_manager


@pytest.mark.asyncio
async def test_setup_mfa():
    """Test MFA setup"""
    
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    assert "qr_code" in result
    assert "secret" in result
    assert "backup_codes" in result
    assert len(result["backup_codes"]) == 10


@pytest.mark.asyncio
async def test_verify_code():
    """Test TOTP code verification"""
    
    # Setup MFA
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    secret = result["secret"]
    
    # Generate valid code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Verify
    is_valid = await mfa_manager.verify_code("test_user", valid_code)
    
    assert is_valid


@pytest.mark.asyncio
async def test_verify_backup_code():
    """Test backup code verification"""
    
    # Setup MFA
    result = await mfa_manager.setup_mfa(
        user_id="test_user",
        user_email="test@example.com"
    )
    
    backup_code = result["backup_codes"][0]
    
    # Verify backup code
    is_valid = await mfa_manager.verify_code("test_user", backup_code)
    
    assert is_valid
    
    # Should not work twice
    is_valid = await mfa_manager.verify_code("test_user", backup_code)
    
    assert not is_valid


@pytest.mark.asyncio
async def test_enable_disable_mfa():
    """Test enable/disable MFA"""
    
    user_id = "test_user"
    
    # Setup
    await mfa_manager.setup_mfa(user_id, "test@example.com")
    
    # Not enabled yet
    assert not await mfa_manager.is_enabled(user_id)
    
    # Enable
    await mfa_manager.enable_mfa(user_id)
    
    assert await mfa_manager.is_enabled(user_id)
    
    # Disable
    await mfa_manager.disable_mfa(user_id)
    
    assert not await mfa_manager.is_enabled(user_id)
```

---

**Продолжение следует... (требуется подтверждение для продолжения)**

Создано:
- ✅ Comprehensive Audit Logging
- ✅ Two-Factor Authentication (MFA)
- ✅ Enhanced API routes
- ✅ Audit middleware
- ✅ Setup scripts
- ✅ Tests

**Готовы к тестированию и завершению Day 117-118?**