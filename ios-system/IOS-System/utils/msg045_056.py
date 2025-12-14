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