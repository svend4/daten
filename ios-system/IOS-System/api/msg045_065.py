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