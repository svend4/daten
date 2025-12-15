# api/main.py
"""
REST API для Information Operating System
Использует FastAPI для создания RESTful интерфейса
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import jwt
import os
from pathlib import Path

# Создание приложения FastAPI
app = FastAPI(
    title="Information Operating System API",
    description="Комплексная система управления знаниями и документами",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
SECRET_KEY = os.getenv("IOS_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Security
security = HTTPBearer()


# ============================================================================
# PYDANTIC MODELS (Модели данных)
# ============================================================================

class UserLogin(BaseModel):
    """Модель для входа пользователя"""
    username: str
    password: str


class Token(BaseModel):
    """Модель токена"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class DomainCreate(BaseModel):
    """Модель для создания домена"""
    name: str = Field(..., description="Название домена")
    language: str = Field(default="de", description="Язык домена")
    description: Optional[str] = Field(None, description="Описание домена")
    entity_types: List[str] = Field(default_factory=list, description="Типы сущностей")


class DomainResponse(BaseModel):
    """Модель ответа домена"""
    name: str
    language: str
    description: Optional[str]
    entity_types: List[str]
    created_at: datetime
    statistics: Dict[str, Any]


class DocumentUpload(BaseModel):
    """Модель для загрузки документа"""
    title: Optional[str] = None
    domain_name: str
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    """Модель ответа документа"""
    doc_id: str
    title: str
    document_type: str
    category: str
    subcategory: Optional[str]
    confidence: float
    created_at: datetime
    file_path: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Модель поискового запроса"""
    query: str = Field(..., description="Поисковый запрос")
    search_type: str = Field(default="full_text", description="Тип поиска: full_text, semantic, faceted, hybrid")
    domain_name: Optional[str] = Field(None, description="Домен для поиска")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: Dict[str, Any] = Field(default_factory=dict)
    ranking: str = Field(default="hybrid", description="Стратегия ранжирования")


class SearchResponse(BaseModel):
    """Модель ответа поиска"""
    results: List[Dict[str, Any]]
    total_count: int
    facets: Optional[Dict[str, Dict[str, int]]]
    query: str
    search_time_ms: float


class EntityCreate(BaseModel):
    """Модель для создания сущности"""
    type: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_document: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class EntityResponse(BaseModel):
    """Модель ответа сущности"""
    id: str
    type: str
    name: str
    properties: Dict[str, Any]
    source_document: str
    confidence: float
    created_at: datetime
    updated_at: datetime


class RelationCreate(BaseModel):
    """Модель для создания отношения"""
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RelationResponse(BaseModel):
    """Модель ответа отношения"""
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any]
    confidence: float
    created_at: datetime


class ContextCreate(BaseModel):
    """Модель для создания контекста"""
    name: str
    type: str  # work, personal, project, research, legal_case
    description: Optional[str] = None
    active_domains: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ContextResponse(BaseModel):
    """Модель ответа контекста"""
    id: str
    name: str
    type: str
    description: Optional[str]
    active_domains: List[str]
    active_projects: List[str]
    active_documents: List[str]
    last_accessed: datetime
    access_count: int


class GraphQuery(BaseModel):
    """Модель запроса к графу"""
    query_type: str  # cypher, entity_type, entity_name, path
    query: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)


class GraphStatistics(BaseModel):
    """Модель статистики графа"""
    total_entities: int
    total_relations: int
    entity_types: Dict[str, int]
    relation_types: Dict[str, int]
    density: float
    connected_components: int


# ============================================================================
# DEPENDENCY INJECTION (Зависимости)
# ============================================================================

# Глобальный IOS Root (инициализируется при старте)
ios_root: Optional['IOSRoot'] = None


def get_ios_root() -> 'IOSRoot':
    """Получить IOS Root"""
    if ios_root is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IOS system not initialized"
        )
    return ios_root


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Проверка JWT токена"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(token_data: Dict = Depends(verify_token)) -> str:
    """Получить текущего пользователя"""
    return token_data.get("sub")


# ============================================================================
# AUTHENTICATION ENDPOINTS (Аутентификация)
# ============================================================================

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_data: UserLogin):
    """
    Вход в систему и получение JWT токена
    
    - **username**: Имя пользователя
    - **password**: Пароль
    """
    # TODO: Проверка пользователя в базе данных
    # Это упрощенная версия - в продакшене использовать настоящую аутентификацию
    
    if user_data.username == "admin" and user_data.password == "admin":
        # Создать токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires
        
        payload = {
            "sub": user_data.username,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        return Token(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(current_user: str = Depends(get_current_user)):
    """
    Выход из системы
    """
    # TODO: Добавить токен в blacklist
    return {"message": "Successfully logged out"}


# ============================================================================
# DOMAIN ENDPOINTS (Домены)
# ============================================================================

@app.get("/api/domains", response_model=List[str], tags=["Domains"])
async def list_domains(
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить список всех доменов
    """
    return ios.list_domains()


@app.post("/api/domains", response_model=DomainResponse, tags=["Domains"], status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain_data: DomainCreate,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Создать новый домен
    
    - **name**: Название домена (уникальное)
    - **language**: Язык домена (de, en, ru)
    - **description**: Описание домена
    - **entity_types**: Список типов сущностей
    """
    try:
        config = {
            'language': domain_data.language,
            'description': domain_data.description,
            'entity_types': domain_data.entity_types
        }
        
        domain = ios.create_domain(domain_data.name, config)
        
        return DomainResponse(
            name=domain.name,
            language=config['language'],
            description=config.get('description'),
            entity_types=config.get('entity_types', []),
            created_at=datetime.now(),
            statistics=domain.get_statistics() if hasattr(domain, 'get_statistics') else {}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/domains/{domain_name}", response_model=DomainResponse, tags=["Domains"])
async def get_domain(
    domain_name: str,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить информацию о домене
    """
    try:
        domain = ios.get_domain(domain_name)
        
        return DomainResponse(
            name=domain.name,
            language=domain.config.get('language', 'de'),
            description=domain.config.get('description'),
            entity_types=domain.config.get('entity_types', []),
            created_at=datetime.now(),
            statistics=domain.get_statistics() if hasattr(domain, 'get_statistics') else {}
        )
    
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )


@app.delete("/api/domains/{domain_name}", tags=["Domains"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_name: str,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Удалить домен
    """
    try:
        ios.delete_domain(domain_name)
        return None
    
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )


# ============================================================================
# DOCUMENT ENDPOINTS (Документы)
# ============================================================================

@app.post("/api/documents/upload", response_model=DocumentResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    domain_name: str = Query(..., description="Домен для документа"),
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    tags: List[str] = Query(default_factory=list),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Загрузить документ в систему
    
    Документ будет автоматически классифицирован, и из него будут извлечены сущности.
    """
    try:
        # Получить домен
        domain = ios.get_domain(domain_name)
        
        # Сохранить файл
        file_path = f"/tmp/uploads/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Создать документ
        document = Document(
            id=f"doc_{hash(file.filename)}_{int(datetime.now().timestamp())}",
            title=title or file.filename,
            content=content.decode('utf-8', errors='ignore'),
            file_path=file_path,
            author=author,
            creation_date=datetime.now()
        )
        
        # Добавить в домен (автоматическая классификация и извлечение сущностей)
        domain.add_document(document)
        
        # Получить классификацию
        classification = domain.classify(document)
        
        # Получить сущности
        entities = domain.extract_entities(document)
        
        return DocumentResponse(
            doc_id=document.id,
            title=document.title,
            document_type=classification.document_type,
            category=classification.category,
            subcategory=classification.subcategory,
            confidence=classification.confidence,
            created_at=document.creation_date,
            file_path=file_path,
            entities=[e.to_dict() for e in entities],
            tags=tags
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/documents/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(
    doc_id: str,
    domain_name: str = Query(...),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить информацию о документе
    """
    try:
        domain = ios.get_domain(domain_name)
        # TODO: Реализовать получение документа из домена
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document retrieval not yet implemented"
        )
    
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )


@app.get("/api/documents/{doc_id}/download", tags=["Documents"])
async def download_document(
    doc_id: str,
    domain_name: str = Query(...),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Скачать файл документа
    """
    # TODO: Реализовать скачивание документа
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document download not yet implemented"
    )


# ============================================================================
# SEARCH ENDPOINTS (Поиск)
# ============================================================================

@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(
    search_request: SearchRequest,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Поиск документов
    
    Поддерживаемые типы поиска:
    - **full_text**: Полнотекстовый поиск (BM25)
    - **semantic**: Семантический поиск (по смыслу)
    - **faceted**: Фасетный поиск (с агрегациями)
    - **hybrid**: Комбинация полнотекстового и семантического
    """
    import time
    start_time = time.time()
    
    try:
        # Получить домен
        if search_request.domain_name:
            domain = ios.get_domain(search_request.domain_name)
            search_engine = domain.search_engine
        else:
            # Поиск по всей системе
            search_engine = ios.global_search_engine
        
        # Выполнить поиск
        results = search_engine.search(
            query=search_request.query,
            search_type=search_request.search_type,
            limit=search_request.limit,
            offset=search_request.offset,
            filters=search_request.filters,
            ranking=search_request.ranking
        )
        
        search_time = (time.time() - start_time) * 1000  # в миллисекундах
        
        return SearchResponse(
            results=results['results'],
            total_count=results['total_count'],
            facets=results.get('facets'),
            query=search_request.query,
            search_time_ms=search_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/search/suggest", response_model=List[str], tags=["Search"])
async def autocomplete(
    prefix: str = Query(..., min_length=1),
    domain_name: Optional[str] = Query(None),
    max_suggestions: int = Query(default=10, ge=1, le=50),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Автодополнение для поисковых запросов
    """
    try:
        if domain_name:
            domain = ios.get_domain(domain_name)
            search_engine = domain.search_engine
        else:
            search_engine = ios.global_search_engine
        
        suggestions = search_engine.suggest_queries(prefix, max_suggestions)
        
        return suggestions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# KNOWLEDGE GRAPH ENDPOINTS (Граф знаний)
# ============================================================================

@app.get("/api/graph/{domain_name}/statistics", response_model=GraphStatistics, tags=["Knowledge Graph"])
async def get_graph_statistics(
    domain_name: str,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить статистику графа знаний
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        
        stats = kg.get_statistics()
        
        return GraphStatistics(**stats)
    
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )


@app.post("/api/graph/{domain_name}/entities", response_model=EntityResponse, tags=["Knowledge Graph"])
async def create_entity(
    domain_name: str,
    entity_data: EntityCreate,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Создать новую сущность в графе знаний
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        
        # Создать сущность
        entity = Entity(
            id=f"entity_{entity_data.type}_{hash(entity_data.name)}",
            type=entity_data.type,
            name=entity_data.name,
            properties=entity_data.properties,
            source_document=entity_data.source_document,
            confidence=entity_data.confidence,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Добавить в граф
        kg.add_entity(entity)
        kg.save()
        
        return EntityResponse(**entity.to_dict())
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/graph/{domain_name}/entities", response_model=List[EntityResponse], tags=["Knowledge Graph"])
async def list_entities(
    domain_name: str,
    entity_type: Optional[str] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить список сущностей
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        query_engine = GraphQueryEngine(kg)
        
        if entity_type:
            entities = query_engine.find_entities_by_type(entity_type)
        else:
            entities = list(kg.entity_index.values())
        
        # Пагинация
        entities = entities[offset:offset + limit]
        
        return [EntityResponse(**e.to_dict()) for e in entities]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/graph/{domain_name}/entities/{entity_id}", response_model=EntityResponse, tags=["Knowledge Graph"])
async def get_entity(
    domain_name: str,
    entity_id: str,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить информацию о сущности
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        
        entity = kg.get_entity(entity_id)
        
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity '{entity_id}' not found"
            )
        
        return EntityResponse(**entity.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/graph/{domain_name}/entities/{entity_id}/related", response_model=List[EntityResponse], tags=["Knowledge Graph"])
async def get_related_entities(
    domain_name: str,
    entity_id: str,
    relation_type: Optional[str] = Query(None),
    direction: str = Query(default="both", regex="^(in|out|both)$"),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить связанные сущности
    
    - **relation_type**: Тип отношения (опционально)
    - **direction**: Направление связей (in, out, both)
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        
        related = kg.get_related_entities(entity_id, relation_type, direction)
        
        return [EntityResponse(**e.to_dict()) for e in related]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/graph/{domain_name}/relations", response_model=RelationResponse, tags=["Knowledge Graph"])
async def create_relation(
    domain_name: str,
    relation_data: RelationCreate,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Создать новое отношение между сущностями
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        
        # Создать отношение
        relation = Relation(
            id=f"rel_{relation_data.type}_{relation_data.source_id}_{relation_data.target_id}",
            type=relation_data.type,
            source_id=relation_data.source_id,
            target_id=relation_data.target_id,
            properties=relation_data.properties,
            source_document="api",
            confidence=relation_data.confidence,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Добавить в граф
        kg.add_relation(relation)
        kg.save()
        
        return RelationResponse(**relation.to_dict())
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/graph/{domain_name}/query", tags=["Knowledge Graph"])
async def query_graph(
    domain_name: str,
    graph_query: GraphQuery,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Выполнить запрос к графу знаний
    
    Поддерживаемые типы запросов:
    - **cypher**: Cypher-подобный запрос
    - **entity_type**: Поиск по типу сущности
    - **entity_name**: Поиск по имени сущности
    - **path**: Поиск пути между сущностями
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        query_engine = GraphQueryEngine(kg)
        
        if graph_query.query_type == "cypher":
            results = query_engine.cypher_like_query(graph_query.query)
        
        elif graph_query.query_type == "entity_type":
            entities = query_engine.find_entities_by_type(graph_query.query)
            results = [e.to_dict() for e in entities[:graph_query.limit]]
        
        elif graph_query.query_type == "entity_name":
            entities = query_engine.find_entities_by_name(graph_query.query)
            results = [e.to_dict() for e in entities[:graph_query.limit]]
        
        elif graph_query.query_type == "path":
            source_id = graph_query.parameters.get('source_id')
            target_id = graph_query.parameters.get('target_id')
            max_length = graph_query.parameters.get('max_length', 5)
            
            if not source_id or not target_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Path query requires 'source_id' and 'target_id' parameters"
                )
            
            path = kg.find_path(source_id, target_id, max_length)
            results = path if path else []
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown query type: {graph_query.query_type}"
            )
        
        return {"results": results}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# CONTEXT ENDPOINTS (Контексты)
# ============================================================================

@app.get("/api/contexts", response_model=List[ContextResponse], tags=["Contexts"])
async def list_contexts(
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Получить список всех контекстов
    """
    try:
        context_manager = ContextManager(ios)
        
        contexts = [ContextResponse(**ctx.to_dict()) for ctx in context_manager.contexts.values()]
        
        return contexts
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/contexts", response_model=ContextResponse, tags=["Contexts"], status_code=status.HTTP_201_CREATED)
async def create_context(
    context_data: ContextCreate,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Создать новый контекст
    """
    try:
        context_manager = ContextManager(ios)
        
        from .context_manager import ContextType
        
        context = context_manager.create_context(
            name=context_data.name,
            context_type=ContextType(context_data.type),
            description=context_data.description or "",
            active_domains=context_data.active_domains,
            properties=context_data.properties
        )
        
        return ContextResponse(**context.to_dict())
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/contexts/{context_id}/switch", response_model=Dict[str, Any], tags=["Contexts"])
async def switch_context(
    context_id: str,
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Переключиться на другой контекст
    """
    try:
        context_manager = ContextManager(ios)
        
        state = context_manager.switch_context(context_id)
        
        return state
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ANALYTICS ENDPOINTS (Аналитика)
# ============================================================================

@app.get("/api/analytics/{domain_name}/graph", tags=["Analytics"])
async def graph_analytics(
    domain_name: str,
    analysis_type: str = Query(..., regex="^(most_connected|central|communities|recommendations)$"),
    top_n: int = Query(default=10, ge=1, le=100),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Аналитика графа знаний
    
    Типы анализа:
    - **most_connected**: Наиболее связанные сущности
    - **central**: Центральные сущности (PageRank)
    - **communities**: Обнаружение сообществ
    - **recommendations**: Рекомендации по улучшению
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        analytics = GraphAnalytics(kg)
        
        if analysis_type == "most_connected":
            results = analytics.get_most_connected_entities(top_n=top_n)
            return {
                "results": [
                    {"entity": e.to_dict(), "degree": degree}
                    for e, degree in results
                ]
            }
        
        elif analysis_type == "central":
            results = analytics.get_central_entities('pagerank', top_n=top_n)
            return {
                "results": [
                    {"entity": e.to_dict(), "score": score}
                    for e, score in results
                ]
            }
        
        elif analysis_type == "communities":
            communities = analytics.detect_communities('louvain')
            return {
                "communities": {
                    name: [e.to_dict() for e in entities]
                    for name, entities in communities.items()
                }
            }
        
        elif analysis_type == "recommendations":
            recommendations = analytics.generate_recommendations()
            return {"recommendations": recommendations}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# EXPORT ENDPOINTS (Экспорт)
# ============================================================================

@app.get("/api/export/{domain_name}/graph", tags=["Export"])
async def export_graph(
    domain_name: str,
    format: str = Query(..., regex="^(gexf|cytoscape|json)$"),
    ios: 'IOSRoot' = Depends(get_ios_root),
    current_user: str = Depends(get_current_user)
):
    """
    Экспортировать граф знаний
    
    Форматы:
    - **gexf**: Формат для Gephi
    - **cytoscape**: Формат для Cytoscape.js
    - **json**: JSON формат
    """
    try:
        domain = ios.get_domain(domain_name)
        kg = domain.knowledge_graph
        viz = GraphVisualization(kg)
        
        output_path = f"/tmp/export_{domain_name}_{format}"
        
        if format == "gexf":
            viz.export_to_gephi(output_file=f"{output_path}.gexf")
            return FileResponse(
                f"{output_path}.gexf",
                media_type="application/xml",
                filename=f"{domain_name}_graph.gexf"
            )
        
        elif format == "cytoscape":
            viz.export_to_cytoscape(output_file=f"{output_path}.json")
            return FileResponse(
                f"{output_path}.json",
                media_type="application/json",
                filename=f"{domain_name}_graph.json"
            )
        
        elif format == "json":
            # Простой JSON экспорт
            data = {
                "entities": [e.to_dict() for e in kg.entity_index.values()],
                "relations": [r.to_dict() for r in kg.relation_index.values()]
            }
            return JSONResponse(content=data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# SYSTEM ENDPOINTS (Система)
# ============================================================================

@app.get("/api/system/status", tags=["System"])
async def system_status(ios: 'IOSRoot' = Depends(get_ios_root)):
    """
    Получить статус системы
    """
    return {
        "status": "running",
        "version": "1.0.0",
        "domains_count": len(ios.list_domains()),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/system/health", tags=["System"])
async def health_check():
    """
    Проверка здоровья системы
    """
    return {"status": "healthy"}


# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global ios_root
    
    # Инициализировать IOS Root
    ios_root_path = os.getenv("IOS_ROOT_PATH", "/home/max/IOS-System")
    ios_root = IOSRoot(ios_root_path)
    
    print(f"✓ IOS System initialized at {ios_root_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    global ios_root
    
    if ios_root:
        # Сохранить все данные
        # TODO: Implement graceful shutdown
        pass
    
    print("✓ IOS System shut down")