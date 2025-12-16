"""
API Routes - Все маршруты API
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import secrets
from datetime import datetime

# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: str

class DocumentCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str] = []
    category: Optional[str] = None
    created_at: str
    updated_at: str

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    semantic: bool = False

# ============================================================================
# Demo Data & Authentication
# ============================================================================

# Demo users database
DEMO_USERS = {
    "admin": {
        "id": "user_001",
        "username": "admin",
        "password": "admin123",  # In production, use hashed passwords!
        "email": "admin@ios-system.local",
        "role": "admin",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "demo": {
        "id": "user_002",
        "username": "demo",
        "password": "demo123",
        "email": "demo@ios-system.local",
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z"
    }
}

# Active sessions (in-memory - for demo only)
ACTIVE_SESSIONS = {}

# Demo documents
DEMO_DOCUMENTS = [
    {
        "id": "doc_001",
        "title": "Welcome to IOS System",
        "content": "This is a demo document showcasing the Information Operating System. You can create, edit, and organize your documents here.",
        "tags": ["welcome", "demo", "getting-started"],
        "category": "tutorial",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    },
    {
        "id": "doc_002",
        "title": "How to Use Search",
        "content": "The search feature allows you to find documents quickly. Use keywords, tags, or semantic search for better results.",
        "tags": ["search", "tutorial", "features"],
        "category": "tutorial",
        "created_at": "2024-01-02T10:00:00Z",
        "updated_at": "2024-01-02T10:00:00Z"
    },
    {
        "id": "doc_003",
        "title": "Knowledge Graph Explained",
        "content": "The knowledge graph helps you visualize relationships between your documents and concepts.",
        "tags": ["graph", "knowledge", "features"],
        "category": "tutorial",
        "created_at": "2024-01-03T10:00:00Z",
        "updated_at": "2024-01-03T10:00:00Z"
    }
]

# ============================================================================
# Auth Router
# ============================================================================

auth_router = APIRouter()

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Авторизация пользователя - Demo implementation"""
    # Check if user exists and password matches
    user = DEMO_USERS.get(request.username)

    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Generate session token
    token = secrets.token_urlsafe(32)

    # Store session
    ACTIVE_SESSIONS[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "created_at": datetime.utcnow().isoformat()
    }

    # Return token and user info
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    )

@auth_router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Регистрация нового пользователя - Demo implementation"""
    # Check if username already exists
    if request.username in DEMO_USERS:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Check if email already exists
    for user in DEMO_USERS.values():
        if user["email"] == request.email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

    # Generate new user ID
    user_id = f"user_{len(DEMO_USERS) + 1:03d}"

    # Create new user
    new_user = {
        "id": user_id,
        "username": request.username,
        "password": request.password,  # In production, use hashed passwords!
        "email": request.email,
        "role": "user",  # New users get 'user' role by default
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    # Add to users database
    DEMO_USERS[request.username] = new_user

    # Generate session token (auto-login after registration)
    token = secrets.token_urlsafe(32)

    # Store session
    ACTIVE_SESSIONS[token] = {
        "user_id": new_user["id"],
        "username": new_user["username"],
        "created_at": datetime.utcnow().isoformat()
    }

    # Return token and user info
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
    )

@auth_router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Выход из системы"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        ACTIVE_SESSIONS.pop(token, None)

    return {"message": "Logged out successfully"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Получение текущего пользователя"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    session = ACTIVE_SESSIONS.get(token)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find user
    user = next(
        (u for u in DEMO_USERS.values() if u["id"] == session["user_id"]),
        None
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        created_at=user["created_at"]
    )

# ============================================================================
# Documents Router
# ============================================================================

documents_router = APIRouter()

@documents_router.get("/", response_model=List[DocumentResponse])
async def list_documents(limit: int = 100, offset: int = 0):
    """Список документов - Demo implementation"""
    # Return demo documents
    start = offset
    end = offset + limit
    docs = DEMO_DOCUMENTS[start:end]

    return [DocumentResponse(**doc) for doc in docs]

@documents_router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    """Создание документа - Demo implementation"""
    # Create new document with generated ID
    new_id = f"doc_{str(len(DEMO_DOCUMENTS) + 1).zfill(3)}"
    now = datetime.utcnow().isoformat() + "Z"

    new_doc = {
        "id": new_id,
        "title": document.title,
        "content": document.content,
        "tags": document.tags or [],
        "category": document.category,
        "created_at": now,
        "updated_at": now
    }

    DEMO_DOCUMENTS.append(new_doc)

    return DocumentResponse(**new_doc)

@documents_router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Получение документа - Demo implementation"""
    doc = next((d for d in DEMO_DOCUMENTS if d["id"] == doc_id), None)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(**doc)

@documents_router.put("/{doc_id}", response_model=DocumentResponse)
@documents_router.patch("/{doc_id}", response_model=DocumentResponse)
async def update_document(doc_id: str, document: DocumentCreate):
    """Обновление документа - Demo implementation"""
    doc = next((d for d in DEMO_DOCUMENTS if d["id"] == doc_id), None)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update document
    doc["title"] = document.title
    doc["content"] = document.content
    doc["tags"] = document.tags or []
    doc["category"] = document.category
    doc["updated_at"] = datetime.utcnow().isoformat() + "Z"

    return DocumentResponse(**doc)

@documents_router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Удаление документа - Demo implementation"""
    global DEMO_DOCUMENTS

    doc_index = next(
        (i for i, d in enumerate(DEMO_DOCUMENTS) if d["id"] == doc_id),
        None
    )

    if doc_index is None:
        raise HTTPException(status_code=404, detail="Document not found")

    DEMO_DOCUMENTS.pop(doc_index)

    return {"message": f"Document {doc_id} deleted successfully"}

# ============================================================================
# Search Router
# ============================================================================

search_router = APIRouter()

@search_router.post("/")
async def search(request: SearchRequest):
    """Поиск документов"""
    return {
        "query": request.query,
        "results": [],
        "total": 0,
        "semantic": request.semantic
    }

@search_router.get("/suggestions")
async def get_suggestions(q: str):
    """Подсказки для поиска"""
    return {"suggestions": []}

# ============================================================================
# Knowledge Graph Router
# ============================================================================

graph_router = APIRouter()

@graph_router.get("/")
async def get_graph():
    """Получение графа знаний"""
    return {"nodes": [], "edges": []}

@graph_router.get("/entities")
async def get_entities(limit: int = 100):
    """Список сущностей"""
    return {"entities": []}

@graph_router.get("/relations")
async def get_relations(limit: int = 100):
    """Список связей"""
    return {"relations": []}

@graph_router.get("/document/{doc_id}")
async def get_document_graph(doc_id: str):
    """Граф знаний для документа"""
    return {"nodes": [], "edges": []}

# ============================================================================
# Admin Router
# ============================================================================

admin_router = APIRouter()

@admin_router.get("/stats")
async def get_stats():
    """Статистика системы"""
    return {
        "documents_count": 0,
        "users_count": 1,
        "storage_used_mb": 0,
        "indices_count": 0
    }

@admin_router.get("/services")
async def get_services():
    """Статус сервисов"""
    return {"services": {}}

@admin_router.post("/reindex")
async def reindex():
    """Переиндексация документов"""
    return {"message": "Reindexing started"}

@admin_router.get("/logs")
async def get_logs(limit: int = 100):
    """Последние логи"""
    return {"logs": []}

# ============================================================================
# AI Router
# ============================================================================

ai_router = APIRouter()

@ai_router.post("/summarize")
async def summarize(text: str):
    """Суммаризация текста"""
    return {"summary": "Summary not available"}

@ai_router.post("/classify")
async def classify(text: str):
    """Классификация текста"""
    return {"category": "uncategorized", "confidence": 0.0}

@ai_router.post("/extract")
async def extract_entities(text: str):
    """Извлечение сущностей"""
    return {"entities": []}

@ai_router.post("/chat")
async def chat(message: str):
    """Чат с AI ассистентом"""
    return {"response": "AI chat not configured"}

# ============================================================================
# Dashboard Router - Additional endpoints for dashboard stats
# ============================================================================

dashboard_router = APIRouter()

@dashboard_router.get("/")
async def get_dashboard_stats():
    """Получение статистики для dashboard"""
    return {
        "documents_count": len(DEMO_DOCUMENTS),
        "users_count": len(DEMO_USERS),
        "storage_used_mb": len(DEMO_DOCUMENTS) * 0.5,  # Mock
        "recent_documents": DEMO_DOCUMENTS[:5],
        "activity": [
            {
                "id": "act_001",
                "type": "document_created",
                "user": "admin",
                "document_title": "Welcome to IOS System",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        ],
        "stats": {
            "total_documents": len(DEMO_DOCUMENTS),
            "total_searches": 42,
            "total_ai_requests": 15,
            "avg_document_size_kb": 12.5
        }
    }
