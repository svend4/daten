"""
Enhanced Encryption Service - Продвинутое шифрование данных
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Сервис для шифрования и дешифрования данных
    Поддерживает:
    - Symmetric encryption (Fernet)
    - Field-level encryption
    - Key rotation
    - Multiple encryption keys
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or Fernet.generate_key()
        self.fernet = Fernet(self.master_key)
        self.keys_cache: Dict[str, Fernet] = {}
        
    def encrypt(self, data: str, key_id: Optional[str] = None) -> str:
        """
        Шифрование данных
        
        Args:
            data: Данные для шифрования (строка)
            key_id: ID ключа (для key rotation)
            
        Returns:
            Зашифрованные данные (base64)
        """
        try:
            fernet = self._get_fernet(key_id)
            encrypted = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt(self, encrypted_data: str, key_id: Optional[str] = None) -> str:
        """
        Дешифрование данных
        
        Args:
            encrypted_data: Зашифрованные данные (base64)
            key_id: ID ключа
            
        Returns:
            Расшифрованные данные (строка)
        """
        try:
            fernet = self._get_fernet(key_id)
            encrypted = base64.b64decode(encrypted_data)
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
            
    def encrypt_json(self, data: Dict[str, Any], key_id: Optional[str] = None) -> str:
        """
        Шифрование JSON данных
        
        Args:
            data: Словарь для шифрования
            key_id: ID ключа
            
        Returns:
            Зашифрованная строка
        """
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str, key_id)
        
    def decrypt_json(self, encrypted_data: str, key_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Дешифрование JSON данных
        
        Args:
            encrypted_data: Зашифрованная строка
            key_id: ID ключа
            
        Returns:
            Расшифрованный словарь
        """
        json_str = self.decrypt(encrypted_data, key_id)
        return json.loads(json_str)
        
    def encrypt_field(self, value: Any) -> str:
        """
        Шифрование отдельного поля (field-level encryption)
        
        Args:
            value: Значение для шифрования
            
        Returns:
            Зашифрованная строка
        """
        if value is None:
            return None
            
        str_value = str(value)
        return self.encrypt(str_value)
        
    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        Дешифрование отдельного поля
        
        Args:
            encrypted_value: Зашифрованное значение
            
        Returns:
            Расшифрованная строка или None
        """
        if not encrypted_value:
            return None
            
        return self.decrypt(encrypted_value)
        
    def generate_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Генерация ключа из пароля
        
        Args:
            password: Пароль
            salt: Salt (если None, генерируется новый)
            
        Returns:
            Ключ шифрования
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
        
    def rotate_key(self, old_key_id: str, new_key_id: str):
        """
        Ротация ключей
        
        Args:
            old_key_id: Старый ключ
            new_key_id: Новый ключ
        """
        # Generate new key
        new_key = Fernet.generate_key()
        self.keys_cache[new_key_id] = Fernet(new_key)
        
        logger.info(f"Key rotated: {old_key_id} -> {new_key_id}")
        
    def _get_fernet(self, key_id: Optional[str] = None) -> Fernet:
        """
        Получение Fernet instance для ключа
        
        Args:
            key_id: ID ключа
            
        Returns:
            Fernet instance
        """
        if key_id and key_id in self.keys_cache:
            return self.keys_cache[key_id]
            
        return self.fernet
        
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Хеширование пароля
        
        Args:
            password: Пароль
            salt: Salt
            
        Returns:
            (hash, salt) в base64
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        password_hash = kdf.derive(password.encode())
        
        return (
            base64.b64encode(password_hash).decode(),
            base64.b64encode(salt).decode()
        )
        
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        Проверка пароля
        
        Args:
            password: Пароль для проверки
            password_hash: Хеш пароля (base64)
            salt: Salt (base64)
            
        Returns:
            True если пароль верный
        """
        try:
            salt_bytes = base64.b64decode(salt)
            computed_hash, _ = EncryptionService.hash_password(password, salt_bytes)
            return computed_hash == password_hash
            
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False


class FieldEncryption:
    """
    Декоратор для автоматического шифрования/дешифрования полей модели
    """
    
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
        
    def encrypt_fields(self, obj: Any, fields: list):
        """
        Шифрование указанных полей объекта
        
        Args:
            obj: Объект
            fields: Список имен полей для шифрования
        """
        for field in fields:
            if hasattr(obj, field):
                value = getattr(obj, field)
                if value is not None:
                    encrypted = self.encryption_service.encrypt_field(value)
                    setattr(obj, field, encrypted)
                    
    def decrypt_fields(self, obj: Any, fields: list):
        """
        Дешифрование указанных полей объекта
        
        Args:
            obj: Объект
            fields: Список имен полей для дешифрования
        """
        for field in fields:
            if hasattr(obj, field):
                encrypted = getattr(obj, field)
                if encrypted is not None:
                    decrypted = self.encryption_service.decrypt_field(encrypted)
                    setattr(obj, field, decrypted)
