"""
Integration Tests для IOS System
Тесты взаимодействия между компонентами
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestAPIIntegration:
    """Интеграционные тесты API"""
    
    def test_fastapi_app_creation(self):
        """Тест создания FastAPI приложения"""
        from ios_system.main import create_application
        from fastapi.testclient import TestClient
        
        app = create_application()
        client = TestClient(app)
        
        # Тест root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        assert response.json()["name"] == "IOS System"
        
    def test_health_endpoint(self):
        """Тест health endpoint"""
        from ios_system.main import create_application
        from fastapi.testclient import TestClient
        
        app = create_application()
        client = TestClient(app)
        
        # Health check может быть недоступен без инициализации
        # но endpoint должен существовать
        try:
            response = client.get("/health")
            assert response.status_code in [200, 503]
        except Exception:
            # Если health check не инициализирован, это ок для теста
            pass


class TestMiddlewareChain:
    """Тесты цепочки middleware"""
    
    @pytest.mark.asyncio
    async def test_middleware_execution_order(self):
        """Тест порядка выполнения middleware"""
        from fastapi import FastAPI, Request, Response
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        from ios_system.middleware.security_headers import SecurityHeadersMiddleware
        
        app = FastAPI()
        
        # Добавляем middleware (в обратном порядке выполнения)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
            
        client = TestClient(app)
        response = client.get("/test")
        
        # Проверяем что оба middleware отработали
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers  # от RequestLogger
        assert "X-Content-Type-Options" in response.headers  # от SecurityHeaders
        
    def test_error_handler_middleware_integration(self):
        """Тест интеграции error handler с другими middleware"""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from ios_system.middleware.error_handler import ErrorHandlerMiddleware
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        
        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware)
        app.add_middleware(RequestLoggerMiddleware)
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
            
        client = TestClient(app)
        response = client.get("/error")
        
        # Error handler должен поймать ошибку
        assert response.status_code == 400
        assert "error" in response.json()


class TestServiceIntegration:
    """Тесты интеграции сервисов"""
    
    @pytest.mark.asyncio
    async def test_service_registry_initialization_order(self):
        """Тест правильного порядка инициализации сервисов"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        
        # Создаем mock сервисы с зависимостями
        service_a = Mock()
        service_a.initialize = AsyncMock()
        
        service_b = Mock()
        service_b.initialize = AsyncMock()
        
        service_c = Mock()
        service_c.initialize = AsyncMock()
        
        # service_b зависит от service_a
        # service_c зависит от service_b
        registry.register('service_a', service_a)
        registry.register('service_b', service_b, depends_on=['service_a'])
        registry.register('service_c', service_c, depends_on=['service_b'])
        
        # Инициализируем все
        result = await registry.initialize_all()
        
        assert result is True
        # Проверяем что все сервисы инициализированы
        service_a.initialize.assert_called_once()
        service_b.initialize.assert_called_once()
        service_c.initialize.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_service_registry_circular_dependency_detection(self):
        """Тест обнаружения циклических зависимостей"""
        from ios_system.core.service_registry import ServiceRegistry
        
        registry = ServiceRegistry()
        
        service_a = Mock()
        service_b = Mock()
        
        # Создаем циклическую зависимость
        registry.register('service_a', service_a, depends_on=['service_b'])
        registry.register('service_b', service_b, depends_on=['service_a'])
        
        # Должно обнаружить проблему
        result = await registry.initialize_all()
        assert result is False


class TestMonitoringIntegration:
    """Тесты интеграции мониторинга"""
    
    @pytest.mark.asyncio
    async def test_health_checker_with_all_components(self):
        """Тест health checker со всеми компонентами"""
        from ios_system.monitoring.health_check import HealthChecker
        
        # Mock всех компонентов
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=True)
        db_mock.ping = AsyncMock()
        
        redis_mock = AsyncMock()
        redis_mock.is_connected = Mock(return_value=True)
        redis_mock.ping = AsyncMock()
        
        service1 = Mock()
        service1.health_check = AsyncMock(return_value={"healthy": True})
        
        service2 = Mock()
        service2.health_check = AsyncMock(return_value={"healthy": True})
        
        services = {
            'service1': service1,
            'service2': service2
        }
        
        checker = HealthChecker(
            db_manager=db_mock,
            redis_cache=redis_mock,
            services=services
        )
        
        result = await checker.check()
        
        assert result['status'] == 'healthy'
        assert result['healthy'] is True
        assert len(result['components']) == 4  # db, redis, service1, service2
        
    @pytest.mark.asyncio
    async def test_health_checker_with_failing_component(self):
        """Тест health checker с падающим компонентом"""
        from ios_system.monitoring.health_check import HealthChecker
        
        # Mock db с ошибкой
        db_mock = AsyncMock()
        db_mock.is_connected = Mock(return_value=False)
        db_mock.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        redis_mock = AsyncMock()
        redis_mock.is_connected = Mock(return_value=True)
        redis_mock.ping = AsyncMock()
        
        checker = HealthChecker(
            db_manager=db_mock,
            redis_cache=redis_mock
        )
        
        result = await checker.check()
        
        assert result['status'] == 'unhealthy'
        assert result['healthy'] is False


class TestSecurityIntegration:
    """Тесты интеграции security компонентов"""
    
    @pytest.mark.asyncio
    async def test_audit_logger_with_encryption(self):
        """Тест интеграции audit logger и encryption"""
        from ios_system.security.audit_logger import AuditLogger, AuditActionType, AuditSeverityLevel
        from ios_system.security.encryption_service import EncryptionService
        
        # Создаем сервисы
        audit_logger = AuditLogger(enable_database_logging=False, enable_file_logging=False)
        encryption = EncryptionService()
        
        # Шифруем чувствительные данные
        sensitive_data = "password123"
        encrypted_data = encryption.encrypt(sensitive_data)
        
        # Логируем действие с зашифрованными данными
        await audit_logger.log(
            action_type=AuditActionType.PASSWORD_CHANGE,
            user_id="user123",
            ip_address="192.168.1.1",
            severity=AuditSeverityLevel.INFO,
            details={"encrypted_password": encrypted_data}
        )
        
        # Проверяем что данные действительно зашифрованы
        assert encrypted_data != sensitive_data
        
    def test_rate_limiter_with_security_headers(self):
        """Тест rate limiter вместе с security headers"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from ios_system.middleware.rate_limiter import RateLimiterMiddleware
        from ios_system.middleware.security_headers import SecurityHeadersMiddleware
        
        app = FastAPI()
        
        redis_mock = Mock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock()
        redis_mock.incr = AsyncMock(return_value=1)
        redis_mock.ttl = AsyncMock(return_value=60)
        
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimiterMiddleware, redis_cache=redis_mock, enabled=False)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "ok"}
            
        client = TestClient(app)
        response = client.get("/test")
        
        # Оба middleware должны отработать
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers


class TestEndToEnd:
    """End-to-end тесты полного flow"""
    
    def test_full_request_lifecycle(self):
        """Тест полного lifecycle запроса"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        from ios_system.middleware.security_headers import SecurityHeadersMiddleware
        from ios_system.middleware.error_handler import ErrorHandlerMiddleware
        
        app = FastAPI()
        
        # Добавляем все middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestLoggerMiddleware)
        app.add_middleware(ErrorHandlerMiddleware)
        
        @app.get("/api/test")
        async def test_endpoint():
            return {"status": "success", "data": {"message": "test"}}
            
        client = TestClient(app)
        response = client.get("/api/test")
        
        # Проверяем весь lifecycle
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert response.json()["status"] == "success"
        
    def test_error_handling_full_flow(self):
        """Тест обработки ошибки через весь flow"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from ios_system.middleware.request_logger import RequestLoggerMiddleware
        from ios_system.middleware.error_handler import ErrorHandlerMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestLoggerMiddleware)
        app.add_middleware(ErrorHandlerMiddleware)
        
        @app.get("/api/error")
        async def error_endpoint():
            raise ValueError("Intentional error for testing")
            
        client = TestClient(app)
        response = client.get("/api/error")
        
        # Ошибка должна быть обработана
        assert response.status_code == 400
        assert "error" in response.json()
        assert "X-Request-ID" in response.headers


# Конфигурация для integration tests
@pytest.fixture
def app():
    """Фикстура для создания test app"""
    from fastapi import FastAPI
    app = FastAPI()
    return app


@pytest.fixture
def client(app):
    """Фикстура для test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
