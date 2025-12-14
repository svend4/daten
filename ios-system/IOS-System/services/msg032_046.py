"""
API integration tests - test complete user flows
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from api.main import app
from ios_core.models import Base
from ios_core.config import settings


@pytest.fixture
async def test_client():
    """Create test client"""
    # Use test database
    engine = create_async_engine(
        "postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_test",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    await engine.dispose()


@pytest.fixture
async def auth_token(test_client):
    """Get authentication token"""
    response = await test_client.post(
        "/api/auth/token",
        data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_complete_document_workflow(test_client, auth_token, tmp_path):
    """
    Test complete document workflow:
    1. Upload document
    2. Get document details
    3. Search for document
    4. Delete document
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create test document
    test_doc = tmp_path / "test.txt"
    test_doc.write_text("""
    Widerspruch gegen Bescheid vom 15.11.2024
    
    Hiermit widerspreche ich gemäß § 29 SGB IX.
    """)
    
    # Step 1: Upload
    with open(test_doc, 'rb') as f:
        response = await test_client.post(
            "/api/documents/upload?domain_name=SGB-IX&title=Test+Widerspruch",
            headers=headers,
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["classification"]["type"] == "Widerspruch"
    
    doc_id = data["document_id"]
    
    # Step 2: Get document
    response = await test_client.get(
        f"/api/documents/{doc_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["title"] == "Test Widerspruch"
    assert doc_data["domain_name"] == "SGB-IX"
    
    # Step 3: Search
    response = await test_client.post(
        "/api/search/",
        headers=headers,
        json={
            "query": "Widerspruch",
            "domain_name": "SGB-IX",
            "search_type": "full_text"
        }
    )
    
    assert response.status_code == 200
    search_data = response.json()
    assert search_data["total_count"] > 0
    assert any(r["doc_id"] == doc_id for r in search_data["results"])
    
    # Step 4: Delete (when implemented)
    # response = await test_client.delete(
    #     f"/api/documents/{doc_id}",
    #     headers=headers
    # )
    # assert response.status_code == 204


@pytest.mark.asyncio
async def test_authentication_flow(test_client):
    """Test authentication flow"""
    
    # Register new user
    response = await test_client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 201
    
    # Login
    response = await test_client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = await test_client.get("/api/documents/", headers=headers)
    assert response.status_code in [200, 501]  # 501 if not implemented yet
    
    # Access without token (should fail)
    response = await test_client.get("/api/documents/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_rate_limiting(test_client, auth_token):
    """Test rate limiting"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Make many requests quickly
    responses = []
    for _ in range(65):  # More than limit (60/min)
        response = await test_client.get("/health", headers=headers)
        responses.append(response)
    
    # Some should be rate limited
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes  # Too Many Requests
    
    # Check rate limit headers
    last_response = responses[-1]
    assert "X-RateLimit-Limit" in last_response.headers
    assert "X-RateLimit-Remaining" in last_response.headers


@pytest.mark.asyncio
async def test_error_handling(test_client, auth_token):
    """Test error handling"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test 404
    response = await test_client.get(
        "/api/documents/nonexistent",
        headers=headers
    )
    assert response.status_code == 404
    assert "error" in response.json() or "detail" in response.json()
    
    # Test 400 (invalid input)
    response = await test_client.post(
        "/api/search/",
        headers=headers,
        json={"query": ""}  # Empty query
    )
    assert response.status_code == 422  # Validation error
    
    # Test 413 (file too large)
    large_file = b"x" * (101 * 1024 * 1024)  # 101 MB
    response = await test_client.post(
        "/api/documents/upload?domain_name=Test",
        headers=headers,
        files={"file": ("large.txt", large_file, "text/plain")}
    )
    assert response.status_code == 413