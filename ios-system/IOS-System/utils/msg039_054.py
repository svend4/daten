# ios_core/security/mfa.py

import pyotp
import qrcode
from io import BytesIO

class MFAManager:
    """Multi-factor authentication"""
    
    def generate_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    def get_qr_code(self, user_email: str, secret: str) -> bytes:
        """Generate QR code for authenticator app"""
        
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="IOS System"
        )
        
        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        
        return buffer.getvalue()
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)