"""
Tests for audit logging
"""

import pytest
from datetime import datetime, timedelta

from ios_core.security.audit_log import (
    audit_logger,
    AuditAction,
    AuditSeverity
)


@pytest.mark.asyncio
async def test_log_audit_event():
    """Test logging audit event"""
    
    await audit_logger.log(
        action=AuditAction.DOCUMENT_CREATE,
        user_id="test_user",
        ip_address="192.168.1.1",
        resource_type="document",
        resource_id="doc123",
        details={"title": "Test Document"},
        success=True
    )
    
    # Query recent logs
    logs = await audit_logger.query(
        user_id="test_user",
        limit=10
    )
    
    assert len(logs) > 0
    assert logs[0].action == AuditAction.DOCUMENT_CREATE.value
    assert logs[0].user_id == "test_user"


@pytest.mark.asyncio
async def test_query_by_action():
    """Test querying logs by action"""
    
    # Log multiple events
    for i in range(5):
        await audit_logger.log(
            action=AuditAction.DOCUMENT_READ,
            user_id=f"user_{i}",
            resource_id=f"doc_{i}",
            success=True
        )
    
    # Query by action
    logs = await audit_logger.query(
        action=AuditAction.DOCUMENT_READ,
        limit=10
    )
    
    assert len(logs) >= 5
    assert all(log.action == AuditAction.DOCUMENT_READ.value for log in logs)


@pytest.mark.asyncio
async def test_query_by_date_range():
    """Test querying logs by date range"""
    
    now = datetime.utcnow()
    
    # Log event
    await audit_logger.log(
        action=AuditAction.LOGIN_SUCCESS,
        user_id="test_user",
        success=True
    )
    
    # Query with date range
    logs = await audit_logger.query(
        start_date=now - timedelta(minutes=1),
        end_date=now + timedelta(minutes=1),
        limit=10
    )
    
    assert len(logs) > 0


@pytest.mark.asyncio
async def test_get_statistics():
    """Test getting audit statistics"""
    
    # Log various events
    actions = [
        AuditAction.LOGIN_SUCCESS,
        AuditAction.DOCUMENT_CREATE,
        AuditAction.SEARCH_EXECUTE,
        AuditAction.LOGIN_FAILED
    ]
    
    for action in actions:
        await audit_logger.log(
            action=action,
            user_id="test_user",
            success=(action != AuditAction.LOGIN_FAILED)
        )
    
    # Get statistics
    stats = await audit_logger.get_statistics()
    
    assert stats["total_events"] > 0
    assert "by_action" in stats
    assert "by_user" in stats
    assert "by_severity" in stats


@pytest.mark.asyncio
async def test_security_alerts():
    """Test getting security alerts"""
    
    # Log security event
    await audit_logger.log(
        action=AuditAction.LOGIN_FAILED,
        user_id="test_user",
        ip_address="192.168.1.1",
        success=False,
        severity=AuditSeverity.WARNING
    )
    
    # Get alerts
    alerts = await audit_logger.get_security_alerts(hours=1)
    
    assert len(alerts) > 0
    assert any(
        alert.action == AuditAction.LOGIN_FAILED.value
        for alert in alerts
    )


@pytest.mark.asyncio
async def test_failed_login_tracking():
    """Test tracking failed login attempts"""
    
    user_id = "suspicious_user"
    ip = "1.2.3.4"
    
    # Simulate multiple failed logins
    for _ in range(5):
        await audit_logger.log(
            action=AuditAction.LOGIN_FAILED,
            user_id=user_id,
            ip_address=ip,
            success=False,
            severity=AuditSeverity.WARNING
        )
    
    # Query failed logins
    logs = await audit_logger.query(
        user_id=user_id,
        action=AuditAction.LOGIN_FAILED,
        success_only=False,
        limit=10
    )
    
    assert len(logs) >= 5