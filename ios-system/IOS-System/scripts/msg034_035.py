"""
Data encryption at rest
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

from ..config import settings


class EncryptionManager:
    """Manage encryption/decryption of sensitive data"""
    
    def __init__(self):
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher from key"""
        # Derive key from secret
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ios_system_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.secret_key.encode())
        )
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt file"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.cipher.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_file(self, encrypted_path: str, output_path: str):
        """Decrypt file"""
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.cipher.decrypt(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)


# Global instance
encryption_manager = EncryptionManager()