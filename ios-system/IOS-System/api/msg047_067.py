"""
Compliance reporting endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from ios_core.security.compliance import compliance_reporter
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class ComplianceReportResponse(BaseModel):
    period: dict
    summary: Optional[dict] = None
    security: Optional[dict] = None
    availability: Optional[dict] = None
    processing_integrity: Optional[dict] = None
    confidentiality: Optional[dict] = None
    privacy: Optional[dict] = None


@router.get("/gdpr", response_model=dict)
@require_permission(Permission.ADMIN_SYSTEM)
async def get_gdpr_report(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate GDPR compliance report
    
    Requires: ADMIN_SYSTEM permission
    """
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    report = await compliance_reporter.generate_gdpr_report(
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/soc2", response_model=ComplianceReportResponse)
@require_permission(Permission.ADMIN_SYSTEM)
async def get_soc2_report(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate SOC 2 compliance report
    
    Requires: ADMIN_SYSTEM permission
    """
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    report = await compliance_reporter.generate_soc2_report(
        start_date=start_date,
        end_date=end_date
    )
    
    return ComplianceReportResponse(**report)


@router.get("/audit-trail")
@require_permission(Permission.ADMIN_SYSTEM)
async def export_audit_trail(
    days: int = Query(7, ge=1, le=90),
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export complete audit trail
    
    Requires: ADMIN_SYSTEM permission
    """
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    data = await compliance_reporter.export_audit_trail(
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    # Return as file download
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"audit_trail_{start_date.date()}_{end_date.date()}.{format}"
    
    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )