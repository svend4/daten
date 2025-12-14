# security/best_practices.py
"""
Security Best Practices для IOS
"""

from typing import Optional
import secrets
import hashlib
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import re

# ============================================================================
# PASSWORD SECURITY
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordPolicy:
    """Политика паролей"""
    
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, Optional[str]]:
        """Валидация пароля"""
        
        if len(password) < PasswordPolicy.MIN_LENGTH:
            return False, f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters"
        
        if PasswordPolicy.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if PasswordPolicy.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if PasswordPolicy.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if PasswordPolicy.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Проверка на общие пароли
        common_passwords = ["password123", "qwerty123", "admin123"]
        if password.lower() in common_passwords:
            return False, "Password is too common"
        
        return True, None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# API KEY SECURITY
# ============================================================================

class APIKeyManager:
    """Управление API ключами"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Генерация безопасного API ключа"""
        return f"ios_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Хэширование API ключа для хранения"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Проверка API ключа"""
        return APIKeyManager.hash_api_key(api_key) == hashed_key


# ============================================================================
# RATE LIMITING
# ============================================================================

from collections import defaultdict
from time import time

class RateLimiter:
    """Rate limiting для защиты от abuse"""
    
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str, max_requests: int = 100, 
                   window_seconds: int = 60) -> bool:
        """Проверка rate limit"""
        
        now = time()
        window_start = now - window_seconds
        
        # Очистить старые запросы
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Проверить лимит
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Добавить новый запрос
        self.requests[identifier].append(now)
        return True


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Валидация пользовательского ввода"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Санитизация имени файла"""
        # Удалить опасные символы
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # Удалить path traversal
        filename = filename.replace('..', '')
        return filename
    
    @staticmethod
    def validate_domain_name(domain_name: str) -> bool:
        """Валидация имени домена"""
        # Только буквы, цифры, дефис, подчеркивание
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, domain_name))
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """Валидация поискового запроса"""
        # Проверка на SQL injection паттерны
        dangerous_patterns = [
            r'(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b)',
            r'(--|;|\/\*|\*\/)',
            r'(\bUNION\b.*\bSELECT\b)',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        return True


# ============================================================================
# ENCRYPTION
# ============================================================================

from cryptography.fernet import Fernet

class Encryptor:
    """Шифрование данных"""
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Шифрование"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Расшифровка"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Логирование для аудита"""
    
    @staticmethod
    def log_event(event_type: str, user_id: str, details: dict, 
                  severity: str = "INFO"):
        """Логировать событие"""
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'severity': severity,
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent')
        }
        
        # TODO: Отправить в централизованное логирование
        print(f"AUDIT: {log_entry}")
    
    @staticmethod
    def log_authentication(user_id: str, success: bool, ip_address: str):
        """Логировать попытку аутентификации"""
        AuditLogger.log_event(
            'authentication',
            user_id,
            {
                'success': success,
                'ip_address': ip_address
            },
            severity='WARNING' if not success else 'INFO'
        )
    
    @staticmethod
    def log_data_access(user_id: str, resource: str, action: str):
        """Логировать доступ к данным"""
        AuditLogger.log_event(
            'data_access',
            user_id,
            {
                'resource': resource,
                'action': action
            }
        )
    
    @staticmethod
    def log_configuration_change(user_id: str, change: dict):
        """Логировать изменение конфигурации"""
        AuditLogger.log_event(
            'configuration_change',
            user_id,
            change,
            severity='WARNING'
        )


# ============================================================================
# SECURITY HEADERS
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для security headers"""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


def configure_security(app: FastAPI):
    """Настроить безопасность приложения"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://your-domain.com"],  # Указать конкретные домены
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        max_age=3600
    )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)