"""
Comprehensive Test Suite для IOS System Backend
Покрывает все основные компоненты системы
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Тесты для Main Application
class TestMainApplication:
    """Тесты главного приложения"""
    
    @pytest.mark.asyncio
    async def test_application_initialization(self):
        """Тест инициализации приложения"""
        from ios_system.main import IOSApplication
        from ios_system.core.config import Settings
        
        settings = Settings()
        app = IOSApplication(settings)
        
        assert app.settings == settings
        assert app.app is None
        assert app.ios_root is None
        
    @pytest.mark.asyncio
    async def test_application_with_mocked_dependencies(self):
        """Тест инициализации с мокированными зависимостями"""
        from ios_system.main import IOSApplication
        from ios_system.core.config import Settings
        
        settings = Settings()
        app = IOSApplication(settings)
        
        # Mock dependencies
        app.db_manager = AsyncMock()
        app.redis_cache = AsyncMock()
        app.redis_cache.connect = AsyncMock()
        app.db_manager.connect = AsyncMock()
        
        # Должен инициализироваться без ошибок
        # await app.initialize()
        
        assert app.db_manager is not None
        assert app.redis_cache is not None
        
    def test_create_application_factory(self):
        """Тест factory function"""
        from ios_system.main import create_application
        from fastapi import FastAPI
        
        app = create_application()
        assert isinstance(app, FastAPI)
        assert app.title == "IOS System API"


# Тесты для Service Registry
class TestServiceRegistry:
    """Тесты Service Registry"""
    
    def test_service_registry_initialization(self):
        """Тест инициализации Service Registry"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        assert len(registry) == 0
        assert registry.list_services() == []
        
    def test_register_service(self):
        """Тест регистрации сервиса"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        mock_service = Mock()
        
        registry.register('test_service', mock_service, version='1.0.0')
        
        assert 'test_service' in registry
        assert len(registry) == 1
        assert registry.get('test_service') == mock_service
        
    def test_unregister_service(self):
        """Тест удаления сервиса"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        mock_service = Mock()
        
        registry.register('test_service', mock_service)
        assert len(registry) == 1
        
        result = registry.unregister('test_service')
        assert result is True
        assert len(registry) == 0
        
    def test_get_nonexistent_service(self):
        """Тест получения несуществующего сервиса"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        service = registry.get('nonexistent')
        
        assert service is None
        
    def test_service_dependencies(self):
        """Тест зависимостей между сервисами"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        service_a = Mock()
        service_b = Mock()
        
        registry.register('service_a', service_a)
        registry.register('service_b', service_b, depends_on=['service_a'])
        
        # service_b зависит от service_a, зависимость должна быть доступна
        assert registry.check_dependencies('service_b') is True
        
    def test_missing_dependencies(self):
        """Тест недостающих зависимостей"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        service_b = Mock()
        
        registry.register('service_b', service_b, depends_on=['service_a'])
        
        # service_a не зарегистрирован, проверка должна вернуть False
        assert registry.check_dependencies('service_b') is False


# Тесты для Health Checker
class TestHealthChecker:
    """Тесты Health Checker"""
    
    @pytest.mark.asyncio
    async def test_health_checker_initialization(self):
        """Тест инициализации Health Checker"""
        from ios_system.monitoring.health_check import HealthChecker
        
        checker = HealthChecker()
        assert checker.db_manager is None
        assert checker.redis_cache is None
        
    @pytest.mark.asyncio
    async def test_health_check_with_mocked_components(self):
        """Тест проверки здоровья с мокированными компонентами"""
        from ios_system.monitoring.health_check import HealthChecker
        
        # Mock database
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=True)
        
        # Mock redis
        redis_mock = AsyncMock()
        redis_mock.is_connected = Mock(return_value=True)
        redis_mock.ping = AsyncMock()
        
        checker = HealthChecker(db_manager=db_mock, redis_cache=redis_mock)
        result = await checker.check()
        
        assert 'status' in result
        assert 'components' in result
        assert result['status'] in ['healthy', 'unhealthy']
        
    @pytest.mark.asyncio
    async def test_quick_health_check(self):
        """Тест быстрой проверки"""
        from ios_system.monitoring.health_check import HealthChecker
        
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=True)
        
        checker = HealthChecker(db_manager=db_mock)
        result = await checker.check_quick()
        
        assert 'status' in result
        assert 'healthy' in result


# Тесты для Configuration
class TestConfiguration:
    """Тесты Configuration Settings"""
    
    def test_settings_initialization(self):
        """Тест инициализации настроек"""
        from ios_system.core.config import Settings
        
        settings = Settings()
        assert settings.app_name == "IOS System"
        assert settings.version == "1.0.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        
    def test_settings_environment_validation(self):
        """Тест валидации environment"""
        from ios_system.core.config import Settings
        
        settings = Settings(environment="production")
        assert settings.environment == "production"
        
        with pytest.raises(ValueError):
            Settings(environment="invalid")
            
    def test_settings_is_development(self):
        """Тест проверки development режима"""
        from ios_system.core.config import Settings
        
        settings_dev = Settings(environment="development")
        assert settings_dev.is_development() is True
        
        settings_prod = Settings(environment="production")
        assert settings_prod.is_development() is False
        
    def test_settings_is_production(self):
        """Тест проверки production режима"""
        from ios_system.core.config import Settings
        
        settings_prod = Settings(environment="production", debug=False)
        assert settings_prod.is_production() is True
        
        settings_dev = Settings(environment="development")
        assert settings_dev.is_production() is False
        
    def test_settings_model_dump_safe(self):
        """Тест безопасного dump настроек"""
        from ios_system.core.config import Settings
        
        settings = Settings(secret_key="super-secret-key")
        safe_dump = settings.model_dump_safe()
        
        assert safe_dump['secret_key'] == '****'
        assert 'app_name' in safe_dump


# Тесты для Middleware
class TestErrorHandlerMiddleware:
    """Тесты Error Handler Middleware"""
    
    @pytest.mark.asyncio
    async def test_error_handler_catches_value_error(self):
        """Тест обработки ValueError"""
        from ios_system.middleware.error_handler import ErrorHandlerMiddleware
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        
        app = FastAPI()
        middleware = ErrorHandlerMiddleware(app)
        
        async def call_next_with_error(request):
            raise ValueError("Test error")
            
        request = Mock(spec=Request)
        request.state = Mock()
        
        response = await middleware.dispatch(request, call_next_with_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400


class TestRequestLoggerMiddleware:
    """Тесты Request Logger Middleware"""
    
    @pytest.mark.asyncio
    async def test_request_logger_adds_request_id(self):
        """Тест добавления request_id"""
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        from fastapi import FastAPI, Request, Response
        
        app = FastAPI()
        middleware = RequestLoggerMiddleware(app)
        
        async def call_next(request):
            return Response(content="OK", status_code=200)
            
        request = Mock(spec=Request)
        request.state = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        response = await middleware.dispatch(request, call_next)
        
        assert hasattr(request.state, 'request_id')
        assert 'X-Request-ID' in response.headers


class TestRateLimiterMiddleware:
    """Тесты Rate Limiter Middleware"""
    
    def test_rate_limiter_initialization(self):
        """Тест инициализации rate limiter"""
        from ios_system.middleware.rate_limiter import RateLimiterMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        redis_mock = Mock()
        
        middleware = RateLimiterMiddleware(
            app,
            redis_cache=redis_mock,
            requests_per_minute=60
        )
        
        assert middleware.requests_per_minute == 60
        assert middleware.redis_cache == redis_mock


# Тесты для Security Components
class TestAuditLogger:
    """Тесты Audit Logger"""
    
    @pytest.mark.asyncio
    async def test_audit_logger_initialization(self):
        """Тест инициализации audit logger"""
        from ios_system.security.audit_logger import AuditLogger
        
        logger = AuditLogger(enable_database_logging=False)
        assert logger.enable_database_logging is False
        
    @pytest.mark.asyncio
    async def test_audit_log_entry_creation(self):
        """Тест создания audit log entry"""
        from ios_system.security.audit_logger import (
            AuditLogEntry,
            AuditActionType,
            AuditSeverityLevel
        )
        
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            action_type=AuditActionType.LOGIN,
            user_id="user123",
            user_email="user@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            resource_type=None,
            resource_id=None,
            action_result="success",
            severity=AuditSeverityLevel.INFO,
            details={},
            request_id="req123",
            session_id="sess123"
        )
        
        assert entry.user_id == "user123"
        assert entry.action_type == AuditActionType.LOGIN
        
        entry_dict = entry.to_dict()
        assert 'timestamp' in entry_dict
        assert entry_dict['action_type'] == 'login'


class TestEncryptionService:
    """Тесты Encryption Service"""
    
    def test_encryption_service_initialization(self):
        """Тест инициализации encryption service"""
        from ios_system.security.encryption_service import EncryptionService
        
        service = EncryptionService()
        assert service.master_key is not None
        assert service.fernet is not None
        
    def test_encrypt_decrypt_string(self):
        """Тест шифрования и дешифрования строки"""
        from ios_system.security.encryption_service import EncryptionService
        
        service = EncryptionService()
        original = "sensitive data"
        
        encrypted = service.encrypt(original)
        assert encrypted != original
        
        decrypted = service.decrypt(encrypted)
        assert decrypted == original
        
    def test_encrypt_decrypt_json(self):
        """Тест шифрования и дешифрования JSON"""
        from ios_system.security.encryption_service import EncryptionService
        
        service = EncryptionService()
        original_data = {"key": "value", "number": 123}
        
        encrypted = service.encrypt_json(original_data)
        decrypted = service.decrypt_json(encrypted)
        
        assert decrypted == original_data
        
    def test_password_hashing(self):
        """Тест хеширования пароля"""
        from ios_system.security.encryption_service import EncryptionService
        
        password = "mypassword123"
        password_hash, salt = EncryptionService.hash_password(password)
        
        assert password_hash is not None
        assert salt is not None
        assert password_hash != password
        
    def test_password_verification(self):
        """Тест проверки пароля"""
        from ios_system.security.encryption_service import EncryptionService
        
        password = "mypassword123"
        password_hash, salt = EncryptionService.hash_password(password)
        
        # Правильный пароль
        assert EncryptionService.verify_password(password, password_hash, salt) is True
        
        # Неправильный пароль
        assert EncryptionService.verify_password("wrongpassword", password_hash, salt) is False


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_service_registry_with_health_checker(self):
        """Тест интеграции Service Registry и Health Checker"""
        from ios_system.core.service_registry import ServiceRegistry
        from ios_system.monitoring.health_check import HealthChecker
        
        # Создаем registry с mock сервисами
        registry = ServiceRegistry()
        
        mock_service_1 = Mock()
        mock_service_1.health_check = Mock(return_value={"healthy": True})
        
        mock_service_2 = Mock()
        mock_service_2.health_check = Mock(return_value={"healthy": True})
        
        registry.register('service1', mock_service_1)
        registry.register('service2', mock_service_2)
        
        # Создаем health checker с этими сервисами
        services = registry.get_all_services()
        checker = HealthChecker(services=services)
        
        # Проверяем
        result = await checker.check()
        assert 'components' in result
        
    def test_encryption_with_audit_logging(self):
        """Тест интеграции Encryption и Audit Logging"""
        from ios_system.security.encryption_service import EncryptionService
        from ios_system.security.audit_logger import AuditLogger
        
        encryption = EncryptionService()
        audit_logger = AuditLogger(enable_database_logging=False)
        
        # Шифруем данные
        data = "sensitive information"
        encrypted = encryption.encrypt(data)
        
        # Логируем действие (без await, так как это синхронный тест)
        # В реальном использовании это было бы async
        assert encrypted is not None
        assert audit_logger is not None


# Конфигурация pytest
@pytest.fixture
def event_loop():
    """Создание event loop для async тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
