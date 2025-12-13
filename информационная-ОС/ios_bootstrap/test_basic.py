"""
Basic integration tests for IOS Bootstrap

Эти тесты проверяют что базовая инфраструктура работает
"""

import pytest
from fastapi.testclient import TestClient
from ios_bootstrap.main import app


client = TestClient(app)


class TestBasicEndpoints:
    """Test basic endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns 200"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "features" in data

    def test_api_status_endpoint(self):
        """Test API status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data
        assert "endpoints" in data
        assert "database" in data
        assert "redis" in data

    def test_docs_endpoint(self):
        """Test OpenAPI docs are accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_openapi_json(self):
        """Test OpenAPI JSON schema"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestConfiguration:
    """Test configuration"""

    def test_settings_loaded(self):
        """Test settings are loaded"""
        from ios_bootstrap.config import settings

        assert settings.app_name is not None
        assert settings.version is not None
        assert settings.database_url is not None
        assert settings.redis_url is not None

    def test_environment_variables(self):
        """Test environment variables"""
        from ios_bootstrap.config import settings

        # Should have defaults
        assert settings.environment in ["development", "staging", "production"]
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
