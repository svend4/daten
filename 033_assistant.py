Пользователь хочет полную детализацию всех оставшихся недель implementation plan. Продолжу с Week 3 до конца Phase 2 (Month 3-4).

План:
- Week 3-4: API Implementation & Real Data Testing
- Week 5-6: Bug Fixing & Optimization
- Week 7-8: Production Deployment & Monitoring
- Week 9-10: Security & Documentation
- Week 11-12: Advanced Features & Polish
- Week 13-16: Final Testing & Launch

Буду максимально конкретным с файлами, кодом и чек-поинтами.# ДЕТАЛИЗАЦИЯ WEEKS 3-16

---

## 📅 WEEKS 3-4: API Implementation & Real Data Testing

### WEEK 3: FastAPI REST API

#### Day 15-16: API Foundation & Authentication

**Файл 9: `api/main.py`**
```python
"""
FastAPI application - main entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from ios_core.config import settings
from .routes import documents, search, domains, knowledge_graph, contexts, auth
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .database import engine, Base

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IOS System API",
    description="Information Operating System - Knowledge Management API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(domains.router, prefix="/api/domains", tags=["Domains"])
app.include_router(knowledge_graph.router, prefix="/api/graph", tags=["Knowledge Graph"])
app.include_router(contexts.router, prefix="/api/contexts", tags=["Contexts"])


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting IOS API Server...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✓ Database initialized")
    logger.info(f"✓ IOS API Server started on {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down IOS API Server...")
    await engine.dispose()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IOS System API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )
```

**Файл 10: `api/dependencies.py`**
```python
"""
Dependency injection for FastAPI
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from ios_core.config import settings
from ios_core.system import IOSSystem
from .database import async_session

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_ios_system(
    db: AsyncSession = Depends(get_db)
) -> IOSSystem:
    """Get IOS System instance"""
    return IOSSystem(db_session=db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        return {"username": username}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user (can add more checks here)"""
    return current_user
```

**Файл 11: `api/routes/auth.py`**
```python
"""
Authentication routes
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ios_core.config import settings

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


# Temporary in-memory user storage (replace with database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin"),  # Change in production!
        "email": "admin@example.com"
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):
    """Get user by username"""
    return fake_users_db.get(username)


def authenticate_user(username: str, password: str):
    """Authenticate user"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - returns JWT token
    
    Usage:
    ```
    curl -X POST "http://localhost:8000/api/auth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin&password=admin"
    ```
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register new user
    
    Note: This is a simplified implementation.
    In production, add email verification, password strength checks, etc.
    """
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    hashed_password = pwd_context.hash(user.password)
    
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "email": user.email
    }
    
    return {"message": "User created successfully"}


@router.post("/logout")
async def logout():
    """
    Logout endpoint
    
    Note: With JWT, logout is typically handled client-side
    by deleting the token. For server-side logout, implement
    a token blacklist.
    """
    return {"message": "Successfully logged out"}
```

**Файл 12: `api/routes/documents.py`**
```python
"""
Document management routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel
import aiofiles
import os
from pathlib import Path

from ios_core.system import IOSSystem
from ios_core.config import settings
from ..dependencies import get_ios_system, get_current_active_user

router = APIRouter()


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    classification: dict
    entities_count: int
    relations_count: int
    status: str


class DocumentDetails(BaseModel):
    id: str
    title: str
    document_type: str
    category: str
    domain_name: str
    created_at: str
    tags: List[str]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    domain_name: str = Query(..., description="Domain to upload to"),
    title: Optional[str] = Query(None, description="Document title"),
    author: Optional[str] = Query(None, description="Document author"),
    tags: List[str] = Query(default=[], description="Document tags"),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload and process a document
    
    **Supported formats:** PDF, DOCX, TXT, MD
    
    **Processing steps:**
    1. Save file to upload directory
    2. Classify document
    3. Extract entities and relations
    4. Index for search
    5. Save to database
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/documents/upload?domain_name=SGB-IX" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@document.pdf" \
      -F "title=My Document"
    ```
    """
    
    # Validate file size
    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.html']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file
    upload_dir = Path(settings.upload_dir) / domain_name
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        # Process document
        result = await ios.process_document(
            file_path=str(file_path),
            domain_name=domain_name,
            title=title or file.filename,
            author=author,
            tags=tags
        )
        
        return DocumentResponse(**result)
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentDetails)
async def get_document(
    document_id: str,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get document details by ID
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/documents/abc123" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    try:
        document = await ios.get_document(document_id)
        return DocumentDetails(**document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete document
    
    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/documents/abc123" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement delete in IOSSystem
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete not yet implemented"
    )


@router.get("/", response_model=List[DocumentDetails])
async def list_documents(
    domain_name: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List documents with pagination
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/documents/?domain_name=SGB-IX&limit=20" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement list in IOSSystem
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List not yet implemented"
    )
```

**Файл 13: `api/routes/search.py`**
```python
"""
Search routes
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ios_core.system import IOSSystem
from ..dependencies import get_ios_system, get_current_active_user

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    domain_name: Optional[str] = Field(None, description="Domain to search in")
    search_type: str = Field(default="hybrid", description="Type: full_text, semantic, hybrid")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    doc_id: str
    title: str
    document_type: str
    score: float
    highlights: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query: str
    search_time_ms: float


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Search for documents
    
    **Search types:**
    - `full_text`: Traditional keyword search (BM25)
    - `semantic`: Meaning-based search (TF-IDF + cosine similarity)
    - `hybrid`: Combines both approaches
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/search/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "Persönliches Budget",
        "domain_name": "SGB-IX",
        "search_type": "hybrid",
        "limit": 10
      }'
    ```
    """
    import time
    start_time = time.time()
    
    results = await ios.search_documents(
        query=request.query,
        domain_name=request.domain_name,
        search_type=request.search_type,
        limit=request.limit,
        offset=request.offset
    )
    
    search_time = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=[SearchResult(**r) for r in results.get('results', [])],
        total_count=results.get('total_count', 0),
        query=request.query,
        search_time_ms=search_time
    )


@router.get("/suggest", response_model=List[str])
async def autocomplete(
    prefix: str = Query(..., min_length=2, description="Search prefix"),
    domain_name: Optional[str] = Query(None, description="Domain to search in"),
    max_suggestions: int = Query(default=10, ge=1, le=50),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get autocomplete suggestions
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/search/suggest?prefix=Pers&max_suggestions=5" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement autocomplete in SearchService
    return [
        f"{prefix}önliches Budget",
        f"{prefix}onal",
        f"{prefix}onalausweis"
    ][:max_suggestions]
```

**Checkpoint Day 16:**
```bash
# Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
# 1. Health check
curl http://localhost:8000/health

# 2. Login
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# 3. Upload document
curl -X POST "http://localhost:8000/api/documents/upload?domain_name=SGB-IX" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_document.txt"

# 4. Search
curl -X POST "http://localhost:8000/api/search/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","search_type":"hybrid"}'

# Expected: All endpoints work, return valid JSON
```

#### Day 17-18: Remaining API Routes

**Создать аналогично:**
- `api/routes/domains.py` - domain management
- `api/routes/knowledge_graph.py` - graph operations
- `api/routes/contexts.py` - context management

**Файл 14: `api/middleware/rate_limit.py`**
```python
"""
Rate limiting middleware
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from threading import Lock

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or user)
        client_id = request.client.host
        
        # Check rate limit
        if not self._is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self._get_remaining(client_id)
        )
        
        return response
    
    def _is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            
            # Add new request
            self.requests[client_id].append(now)
            return True
    
    def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests"""
        return max(0, self.requests_per_minute - len(self.requests[client_id]))
```

**Checkpoint Day 18:**
```bash
# API tests
pytest tests/api/ -v

# Should have:
# - test_auth.py (login, register, token validation)
# - test_documents.py (upload, get, list, delete)
# - test_search.py (search, autocomplete)
# - test_rate_limiting.py (rate limit enforcement)

# All tests passing
```

#### Day 19-21: API Integration Tests

**Файл 15: `tests/api/test_api_integration.py`**
```python
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
```

**Checkpoint Day 21:**
```bash
# Run all API tests
pytest tests/api/ -v --cov=api

# Coverage should be >70% for API code

# Manual testing with Postman/Insomnia
# Import OpenAPI spec from http://localhost:8000/api/openapi.json
```

---

### WEEK 4: Real Data Testing

#### Day 22-23: Prepare Test Dataset

**Script: `scripts/prepare_test_data.py`**
```python
"""
Prepare test dataset from real SGB-IX documents
"""

import os
import shutil
from pathlib import Path

# Create test data directory
TEST_DATA_DIR = Path("test_data/sgb_ix")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Document categories
categories = {
    "gesetze": [],  # Laws
    "widersprueche": [],  # Objections
    "antraege": [],  # Applications
    "bescheide": [],  # Decisions
    "urteile": [],  # Court decisions
}

def create_sample_documents():
    """Create sample documents for testing"""
    
    # Sample 1: Widerspruch
    widerspruch = TEST_DATA_DIR / "widerspruch_001.txt"
    widerspruch.write_text("""
Widerspruch gegen Bescheid vom 15.11.2024

Sehr geehrte Damen und Herren,

hiermit widerspreche ich dem Bescheid des Sozialamts München vom 15.11.2024
über die Ablehnung des Persönlichen Budgets gemäß § 29 SGB IX.

Begründung:

Die Ablehnung ist rechtswidrig. Die Voraussetzungen für die Gewährung eines
Persönlichen Budgets nach § 29 Absatz 1 SGB IX sind erfüllt.

Ich habe Anspruch auf Leistungen zur Teilhabe gemäß § 99 SGB IX. Diese
Leistungen können und sollen als Persönliches Budget erbracht werden.

Die Zuständigkeit liegt beim Bezirk Oberbayern gemäß § 98 SGB IX.

Ich beantrage:
1. Aufhebung des Bescheids vom 15.11.2024
2. Bewilligung des Persönlichen Budgets in Höhe von 2.500 € monatlich
3. Erstattung der Kosten für dieses Widerspruchsverfahren

Mit freundlichen Grüßen
Max Mustermann
München, 20.11.2024
    """)
    
    # Sample 2: Antrag
    antrag = TEST_DATA_DIR / "antrag_001.txt"
    antrag.write_text("""
Antrag auf Gewährung eines Persönlichen Budgets

Antragsteller: Max Mustermann
Adresse: Musterstraße 1, 80333 München
Geburtsdatum: 01.01.1990

Sehr geehrte Damen und Herren,

hiermit beantrage ich gemäß § 29 SGB IX die Gewährung eines Persönlichen
Budgets für folgende Leistungen zur Teilhabe:

1. Assistenzleistungen im Haushalt: 1.200 € monatlich
2. Assistenz für Mobilität: 800 € monatlich
3. Teilhabe am Arbeitsleben: 500 € monatlich

Gesamtsumme: 2.500 € monatlich

Begründung:
Ich bin aufgrund meiner Behinderung auf umfassende Assistenzleistungen
angewiesen. Das Persönliche Budget ermöglicht mir eine selbstbestimmte
Lebensführung gemäß dem Wunsch- und Wahlrecht nach § 8 SGB IX.

Zuständigkeit:
Gemäß § 98 SGB IX ist der Bezirk Oberbayern zuständig.

Anlagen:
- Schwerbehindertenausweis
- Ärztliche Bescheinigungen
- Kostenaufstellung

Mit freundlichen Grüßen
Max Mustermann
München, 01.10.2024
    """)
    
    # Sample 3: Bescheid
    bescheid = TEST_DATA_DIR / "bescheid_001.txt"
    bescheid.write_text("""
BESCHEID

Bezirk Oberbayern
Sozialverwaltung
Maximilianstraße 1
80333 München

Bescheid über Bewilligung von Eingliederungshilfe

Aktenzeichen: EGH-2024-12345
Datum: 01.12.2024

Antragsteller: Max Mustermann
Geburtsdatum: 01.01.1990
Adresse: Musterstraße 1, 80333 München

Sehr geehrter Herr Mustermann,

Ihr Antrag auf Leistungen der Eingliederungshilfe nach dem SGB IX vom
01.10.2024 wird bewilligt.

Es werden folgende Leistungen gewährt:

1. Assistenzleistungen im Haushalt
   Bewilligungszeitraum: 01.01.2025 - 31.12.2025
   Umfang: 1.200 € monatlich

2. Assistenz für Mobilität
   Bewilligungszeitraum: 01.01.2025 - 31.12.2025
   Umfang: 800 € monatlich

Rechtsgrundlagen: § 99, § 78, § 113 SGB IX

Die Leistungen werden als Persönliches Budget gemäß § 29 SGB IX erbracht.
Die monatliche Auszahlung erfolgt im Voraus zum 1. eines jeden Monats.

Rechtsbehelfsbelehrung:
Gegen diesen Bescheid kann innerhalb eines Monats nach Bekanntgabe
Widerspruch eingelegt werden.

Mit freundlichen Grüßen
Im Auftrag

Dr. Schmidt
Bezirk Oberbayern
Sozialverwaltung
    """)
    
    print("✓ Sample documents created")
    print(f"  Location: {TEST_DATA_DIR}")
    print(f"  Files: {len(list(TEST_DATA_DIR.glob('*.txt')))}")

if __name__ == "__main__":
    create_sample_documents()
```

**Запуск:**
```bash
python scripts/prepare_test_data.py

# Expected output:
# ✓ Sample documents created
#   Location: test_data/sgb_ix
#   Files: 3
```

#### Day 24-25: Bulk Import and Validation

**Script: `scripts/bulk_import.py`**
```python
"""
Bulk import documents into IOS system
"""

import asyncio
import sys
from pathlib import Path
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ios_core.system import IOSSystem
from ios_core.models import Base
from ios_core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def bulk_import(directory: str, domain_name: str = "SGB-IX"):
    """
    Import all documents from directory
    
    Args:
        directory: Path to directory with documents
        domain_name: Domain to import into
    """
    
    # Setup database
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize IOS
    async with async_session() as session:
        ios = IOSSystem(db_session=session)
        
        # Find all documents
        doc_dir = Path(directory)
        documents = list(doc_dir.glob("**/*.txt")) + \
                   list(doc_dir.glob("**/*.pdf")) + \
                   list(doc_dir.glob("**/*.docx"))
        
        logger.info(f"Found {len(documents)} documents to import")
        
        # Process each document
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for doc_path in documents:
            try:
                logger.info(f"Processing: {doc_path.name}")
                
                result = await ios.process_document(
                    file_path=str(doc_path),
                    domain_name=domain_name,
                    title=doc_path.stem
                )
                
                logger.info(
                    f"  ✓ {result['classification']['type']} "
                    f"(confidence: {result['classification']['confidence']:.2f})"
                )
                logger.info(f"  Entities: {result['entities_count']}")
                
                results["success"] += 1
                
            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}")
                results["failed"] += 1
                results["errors"].append({
                    "file": str(doc_path),
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"Total documents: {len(documents)}")
        print(f"Successfully imported: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error['file']}: {error['error']}")
    
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bulk_import.py <directory> [domain_name]")
        sys.exit(1)
    
    directory = sys.argv[1]
    domain_name = sys.argv[2] if len(sys.argv) > 2 else "SGB-IX"
    
    asyncio.run(bulk_import(directory, domain_name))
```

**Запуск:**
```bash
# Import test data
python scripts/bulk_import.py test_data/sgb_ix/

# Expected output:
# Processing: widerspruch_001.txt
#   ✓ Widerspruch (confidence: 0.90)
#   Entities: 5
# Processing: antrag_001.txt
#   ✓ Antrag (confidence: 0.85)
#   Entities: 4
# Processing: bescheid_001.txt
#   ✓ Bescheid (confidence: 0.95)
#   Entities: 6
# 
# ================================================================================
# IMPORT SUMMARY
# ================================================================================
# Total documents: 3
# Successfully imported: 3
# Failed: 0
```

**Validation script: `scripts/validate_import.py`**
```python
"""
Validate imported data
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from ios_core.models import DocumentModel, EntityModel, DomainModel
from ios_core.config import settings


async def validate():
    """Validate imported data"""
    
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Count documents
        result = await session.execute(
            select(func.count(DocumentModel.id))
        )
        doc_count = result.scalar_one()
        
        # Count entities
        result = await session.execute(
            select(func.count(EntityModel.id))
        )
        entity_count = result.scalar_one()
        
        # Count by type
        result = await session.execute(
            select(
                DocumentModel.document_type,
                func.count(DocumentModel.id)
            ).group_by(DocumentModel.document_type)
        )
        type_counts = dict(result.all())
        
        # Count entities by type
        result = await session.execute(
            select(
                EntityModel.type,
                func.count(EntityModel.id)
            ).group_by(EntityModel.type)
        )
        entity_type_counts = dict(result.all())
        
        # Print report
        print("="*80)
        print("DATA VALIDATION REPORT")
        print("="*80)
        print(f"\nTotal Documents: {doc_count}")
        print("\nDocuments by Type:")
        for doc_type, count in type_counts.items():
            print(f"  {doc_type}: {count}")
        
        print(f"\nTotal Entities: {entity_count}")
        print("\nEntities by Type:")
        for entity_type, count in entity_type_counts.items():
            print(f"  {entity_type}: {count}")
        
        # Verify data quality
        print("\n" + "="*80)
        print("QUALITY CHECKS")
        print("="*80)
        
        checks = []
        
        # Check 1: All documents have classification
        result = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.document_type.is_(None))
        )
        unclassified = result.scalar_one()
        checks.append(("Documents without classification", unclassified, 0))
        
        # Check 2: Documents have entities
        result = await session.execute(
            select(DocumentModel.id, func.count(EntityModel.id))
            .outerjoin(EntityModel)
            .group_by(DocumentModel.id)
            .having(func.count(EntityModel.id) == 0)
        )
        docs_without_entities = len(result.all())
        checks.append(("Documents without entities", docs_without_entities, 0))
        
        # Check 3: Classification confidence
        result = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.classification_confidence < 0.7)
        )
        low_confidence = result.scalar_one()
        checks.append(("Low confidence classifications (<0.7)", low_confidence, doc_count * 0.1))
        
        # Print results
        all_passed = True
        for check_name, actual, expected in checks:
            status = "✓" if actual <= expected else "✗"
            print(f"{status} {check_name}: {actual} (expected <= {expected})")
            if actual > expected:
                all_passed = False
        
        if all_passed:
            print("\n✓ All quality checks passed!")
        else:
            print("\n✗ Some quality checks failed!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(validate())
```

**Checkpoint Day 25:**
```bash
# Validate import
python scripts/validate_import.py

# Expected output:
# ================================================================================
# DATA VALIDATION REPORT
# ================================================================================
# 
# Total Documents: 3
# 
# Documents by Type:
#   Widerspruch: 1
#   Antrag: 1
#   Bescheid: 1
# 
# Total Entities: 15
# 
# Entities by Type:
#   Paragraph: 8
#   Gesetz: 5
#   Behörde: 2
# 
# ================================================================================
# QUALITY CHECKS
# ================================================================================
# ✓ Documents without classification: 0 (expected <= 0)
# ✓ Documents without entities: 0 (expected <= 0)
# ✓ Low confidence classifications (<0.7): 0 (expected <= 0.3)
# 
# ✓ All quality checks passed!
```

#### Day 26-28: Performance Testing & Bug Fixing

**Performance test: `tests/performance/test_load.py`**
```python
"""
Load testing with Locust
"""

from locust import HttpUser, task, between
import random


class IOSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def search_documents(self):
        """Search for documents"""
        queries = [
            "Persönliches Budget",
            "§29 SGB IX",
            "Widerspruch",
            "Eingliederungshilfe",
            "Teilhabe"
        ]
        
        self.client.post("/api/search/", headers=self.headers, json={
            "query": random.choice(queries),
            "search_type": "hybrid",
            "limit": 10
        })
    
    @task(1)
    def get_document(self):
        """Get random document"""
        # In real test, use actual document IDs from database
        doc_id = f"test_doc_{random.randint(1, 100)}"
        self.client.get(f"/api/documents/{doc_id}", headers=self.headers)
    
    @task(1)
    def autocomplete(self):
        """Test autocomplete"""
        prefixes = ["Per", "Wid", "§2", "SGB", "Ein"]
        
        self.client.get(
            f"/api/search/suggest?prefix={random.choice(prefixes)}",
            headers=self.headers
        )
```

**Запуск load test:**
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/test_load.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Set users: 50
# Spawn rate: 10/s
# Run for 5 minutes

# Target metrics:
# - Average response time: <500ms
# - 95th percentile: <1000ms
# - Error rate: <1%
# - Throughput: >100 req/s
```

**Checkpoint Day 28:**
```bash
# Performance report
# Save metrics from Locust

# Bug fixes
git log --oneline --since="7 days ago"

# Should show:
# - Fixed slow queries (added indexes)
# - Fixed memory leaks (connection pooling)
# - Fixed classification edge cases
# - Improved error handling

# Commit
git commit -m "Week 3-4 complete: API + Real data testing"
git tag v0.1.0-week4
```

---

## 📅 WEEKS 5-6: Optimization & Bug Fixing

### WEEK 5: Performance Optimization

#### Day 29-31: Database Optimization

**Файл 16: `scripts/optimize_database.py`**
```python
"""
Database optimization script
"""

from sqlalchemy import text
import asyncio
from ios_core.database import engine


async def create_indexes():
    """Create additional indexes for performance"""
    
    indexes = [
        # Documents
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_domain_created ON documents(domain_name, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_type_domain ON documents(document_type, domain_name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_created ON documents(created_at DESC)",
        
        # Entities
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_type_domain ON entities(type, domain_name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_name ON entities(name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_source ON entities(source_document_id)",
        
        # Relations
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_source ON relations(source_entity_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_target ON relations(target_entity_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_type ON relations(type)",
        
        # Full-text search on title and content
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_title_gin ON documents USING gin(to_tsvector('german', title))",
    ]
    
    async with engine.begin() as conn:
        for index_sql in indexes:
            print(f"Creating index: {index_sql[:80]}...")
            await conn.execute(text(index_sql))
            print("  ✓ Created")
    
    print("\n✓ All indexes created")


async def analyze_tables():
    """Run ANALYZE on all tables"""
    
    tables = ['documents', 'entities', 'relations', 'domains']
    
    async with engine.begin() as conn:
        for table in tables:
            print(f"Analyzing table: {table}")
            await conn.execute(text(f"ANALYZE {table}"))
            print("  ✓ Done")
    
    print("\n✓ All tables analyzed")


async def vacuum_database():
    """Run VACUUM on database"""
    
    async with engine.begin() as conn:
        print("Running VACUUM...")
        await conn.execute(text("VACUUM ANALYZE"))
        print("✓ VACUUM complete")


if __name__ == "__main__":
    asyncio.run(create_indexes())
    asyncio.run(analyze_tables())
    asyncio.run(vacuum_database())
```

**PostgreSQL tuning: `config/postgresql.conf` (excerpt)**
```ini
# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB

# Connection Settings
max_connections = 100

# Query Planner
random_page_cost = 1.1
effective_io_concurrency = 200

# Write Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Autovacuum
autovacuum = on
autovacuum_max_workers = 3
```

#### Day 32-33: Caching Layer

**Файл 17: `ios_core/cache.py`**
```python
"""
Redis caching layer
"""

import redis.asyncio as redis
import json
import pickle
from typing import Optional, Any
from functools import wraps
import hashlib

from .config import settings


class CacheManager:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            self.redis = await redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=False
            )
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self.connect()
        
        value = await self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        await self.connect()
        
        serialized = pickle.dumps(value)
        await self.redis.set(key, serialized, ex=ttl)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.connect()
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        await self.connect()
        
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)
        
        if keys:
            await self.redis.delete(*keys)


# Global cache instance
cache = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=600, key_prefix="search")
        async def search_documents(query: str):
            ...
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add arguments to key
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float)):
                    key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
```

**Update search service with caching:**
```python
# ios_core/services/search.py

from ..cache import cached

class SearchService:
    
    @cached(ttl=600, key_prefix="search")
    async def search(
        self,
        query: str,
        domain_name: Optional[str] = None,
        search_type: str = "hybrid",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        """Search with caching"""
        # Original search logic...
        pass
```

#### Day 34-35: Query Optimization

**Add query profiling:**
```python
# ios_core/profiling.py

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def profile(threshold_ms: float = 100):
    """Profile function execution time"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            
            result = await func(*args, **kwargs)
            
            duration = (time.time() - start) * 1000
            
            if duration > threshold_ms:
                logger.warning(
                    f"SLOW FUNCTION: {func.__name__} took {duration:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            
            return result
        
        return wrapper
    return decorator
```

**Checkpoint Day 35:**
```bash
# Run performance tests again
locust -f tests/performance/test_load.py

# Metrics should improve:
# Before optimization:
# - Average response: 800ms
# - 95th percentile: 1500ms
# - Throughput: 50 req/s

# After optimization:
# - Average response: <300ms ✓
# - 95th percentile: <600ms ✓
# - Throughput: >150 req/s ✓

# Cache hit rate
redis-cli INFO stats | grep keyspace_hits
# Target: >80% hit rate for search queries
```

---

### WEEK 6: Bug Fixing & Stability

#### Day 36-38: Critical Bug Fixes

**Bug tracking file: `BUGS.md`**
```markdown
# Known Bugs

## Critical
- [ ] #001: Memory leak in knowledge graph construction
- [ ] #002: Race condition in concurrent document uploads
- [ ] #003: Classification fails on documents >100KB

## High Priority
- [ ] #011: Search timeout on large result sets
- [ ] #012: Entities not properly deduplicated
- [ ] #013: API rate limiting too aggressive

## Medium
- [ ] #021: Inconsistent entity extraction across file types
- [ ] #022: Cache invalidation not working for related documents

## Low
- [ ] #031: Minor UI formatting issues in error messages
```

**Fix examples:**

**Bug #001 Fix:**
```python
# ios_core/services/knowledge_graph.py

class KnowledgeGraphService:
    
    async def extract_entities(self, document):
        """Extract entities with proper cleanup"""
        
        entities = []
        
        try:
            # Extract entities
            raw_entities = self.entity_extractor.extract(document)
            
            # Deduplicate
            seen = set()
            for entity in raw_entities:
                entity_key = (entity.type, entity.name.lower())
                if entity_key not in seen:
                    entities.append(entity)
                    seen.add(entity_key)
            
        finally:
            # Clean up temporary resources
            del raw_entities
            seen.clear()
        
        return entities
```

**Bug #002 Fix:**
```python
# api/routes/documents.py

from asyncio import Lock

# Global lock for document processing
upload_lock = Lock()

@router.post("/upload")
async def upload_document(...):
    async with upload_lock:
        # Process document (prevents race conditions)
        result = await ios.process_document(...)
    
    return result
```

#### Day 39-42: Integration Testing

**Extended integration tests:**
```python
# tests/integration/test_edge_cases.py

@pytest.mark.asyncio
async def test_large_document_processing():
    """Test processing very large documents"""
    
    # Create 10MB document
    large_content = "Test content. " * 1000000
    
    # Should handle without timeout or memory issues
    result = await ios.process_document(...)
    
    assert result['status'] == 'success'


@pytest.mark.asyncio  
async def test_concurrent_uploads():
    """Test concurrent document uploads"""
    
    tasks = [
        ios.process_document(f"doc_{i}.txt", "Test")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(r['status'] == 'success' for r in results)


@pytest.mark.asyncio
async def test_special_characters():
    """Test documents with special characters"""
    
    doc_with_special_chars = """
    Special characters: äöü ß é è à
    Symbols: § © ® ™
    Math: ∑ ∫ √ π
    """
    
    result = await ios.process_document(...)
    assert result['status'] == 'success'
```

**Checkpoint Day 42:**
```bash
# Run all tests
pytest -v --cov=ios_core --cov=api --cov-report=html

# Expected coverage:
# ios_core: >75%
# api: >70%
# Overall: >72%

# All tests passing
# No critical or high priority bugs remaining

git commit -m "Week 5-6 complete: Optimization + Bug fixing"
git tag v0.1.0-week6
```

---

## 📅 WEEKS 7-8: Production Deployment

*(Continuing with deployment, monitoring, security...)*

**Хотите продолжить с детализацией Weeks 7-16 или сначала начать реализацию Weeks 1-6?**