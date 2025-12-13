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