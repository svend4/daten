Пользователь хочет конкретный implementation plan. Учитывая аудит, я рекомендую PATH 3 (Balanced Approach) как наиболее реалистичный и эффективный. 

Создам детальный, практичный план с:
1. Конкретными задачами по дням
2. Приоритизацией
3. Checkpoints
4. Code snippets
5. Конкретными файлами для создания
6. Testing strategy
7. Rollback plans
8. Success criteria

Это должен быть actionable план, который Max может начать выполнять прямо сейчас.# ДЕТАЛЬНЫЙ IMPLEMENTATION PLAN
## IOS System - Path 3: Balanced Approach

---

## 📋 ОБЗОР ПЛАНА

**Выбранная стратегия:** Balanced Approach (Quality + Speed)  
**Общая длительность:** 4 месяца  
**Режим работы:** Part-time (20 часов/неделю)  
**Цель:** Production-ready система с вашими SGB-IX документами

---

## 🎯 PHASE 1: FOUNDATION (Месяц 1-2, 8 недель)

### WEEK 1: Project Setup & Core Integration

#### Day 1-2: Project Structure & Environment

**Задачи:**
```bash
1. Создать Git репозиторий
2. Установить project structure
3. Настроить development environment
4. Создать базовые конфигурации
```

**Конкретные файлы для создания:**

```bash
# 1. Создать структуру проекта
ios-system/
├── .github/
│   └── workflows/
│       └── ci.yml
├── ios_core/              # Core system
│   ├── __init__.py
│   ├── system.py          # Main orchestrator
│   ├── config.py          # Configuration
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Repository pattern
│   ├── services/          # Business logic
│   └── exceptions.py      # Custom exceptions
├── api/                   # FastAPI application
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   ├── routes/
│   └── middleware/
├── tests/                 # Tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── docker/                # Docker files
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

**Файл 1: `pyproject.toml`**
```toml
[project]
name = "ios-system"
version = "0.1.0"
description = "Information Operating System - Knowledge Management Platform"
authors = [{name = "Max", email = "your-email@example.com"}]
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}

dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.23",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "whoosh>=2.7.4",
    "scikit-learn>=1.3.2",
    "networkx>=3.2.1",
    "plotly>=5.18.0",
    "python-docx>=1.1.0",
    "PyPDF2>=3.0.1",
    "openpyxl>=3.1.2",
    "python-pptx>=0.6.23",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "isort>=5.12.0",
    "mypy>=1.7.0",
    "ruff>=0.1.6",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Файл 2: `ios_core/config.py`**
```python
"""
Configuration management for IOS System
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "IOS System"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Paths
    ios_root_path: str = Field(default="/data/ios-root")
    upload_dir: str = Field(default="/data/uploads")
    export_dir: str = Field(default="/data/exports")
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db"
    )
    
    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    
    # Security
    secret_key: str = Field(default="change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # API
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]
    
    # Limits
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    rate_limit_per_minute: int = 60
    
    # Search
    search_index_path: str = Field(default="/data/search-indexes")
    
    # Features
    enable_websocket: bool = True
    enable_analytics: bool = True
    
    class Config:
        env_prefix = "IOS_"


# Global settings instance
settings = Settings()
```

**Файл 3: `ios_core/system.py`**
```python
"""
Main IOS System orchestrator
This is the heart of the system that integrates all components
"""

import logging
from typing import Optional
from pathlib import Path

from .config import settings
from .models import Document
from .services.classifier import ClassificationService
from .services.knowledge_graph import KnowledgeGraphService
from .services.search import SearchService
from .services.context import ContextService
from .repositories.document_repository import DocumentRepository
from .exceptions import IOSError, DocumentNotFoundError

logger = logging.getLogger(__name__)


class IOSSystem:
    """
    Main system orchestrator that coordinates all IOS components
    
    This is the facade that applications interact with.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize IOS System
        
        Args:
            db_session: SQLAlchemy async session (optional, for testing)
        """
        self.config = settings
        self.db_session = db_session
        
        # Initialize paths
        self._ensure_directories()
        
        # Initialize services (lazy loading)
        self._classifier_service: Optional[ClassificationService] = None
        self._kg_service: Optional[KnowledgeGraphService] = None
        self._search_service: Optional[SearchService] = None
        self._context_service: Optional[ContextService] = None
        
        logger.info(f"IOS System initialized at {settings.ios_root_path}")
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.config.ios_root_path,
            self.config.upload_dir,
            self.config.export_dir,
            self.config.search_index_path,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Service getters (lazy initialization)
    
    @property
    def classifier(self) -> ClassificationService:
        """Get classifier service"""
        if self._classifier_service is None:
            self._classifier_service = ClassificationService()
        return self._classifier_service
    
    @property
    def knowledge_graph(self) -> KnowledgeGraphService:
        """Get knowledge graph service"""
        if self._kg_service is None:
            self._kg_service = KnowledgeGraphService()
        return self._kg_service
    
    @property
    def search(self) -> SearchService:
        """Get search service"""
        if self._search_service is None:
            self._search_service = SearchService()
        return self._search_service
    
    @property
    def context(self) -> ContextService:
        """Get context service"""
        if self._context_service is None:
            self._context_service = ContextService()
        return self._context_service
    
    # Core operations
    
    async def process_document(
        self,
        file_path: str,
        domain_name: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> dict:
        """
        Complete document processing pipeline
        
        This is the main entry point for adding documents to the system.
        
        Args:
            file_path: Path to the document file
            domain_name: Domain to add the document to
            title: Optional document title
            author: Optional author name
            tags: Optional list of tags
            
        Returns:
            Dictionary with processing results
            
        Raises:
            IOSError: If processing fails
        """
        try:
            logger.info(f"Processing document: {file_path} for domain: {domain_name}")
            
            # Step 1: Create document object
            document = await self._create_document(
                file_path, title, author, tags
            )
            
            # Step 2: Classify document
            classification = await self.classifier.classify(document)
            logger.info(
                f"Document classified as {classification.document_type} "
                f"with confidence {classification.confidence:.2f}"
            )
            
            # Step 3: Extract entities and relations
            entities = await self.knowledge_graph.extract_entities(document)
            relations = await self.knowledge_graph.extract_relations(
                document, entities
            )
            logger.info(
                f"Extracted {len(entities)} entities and {len(relations)} relations"
            )
            
            # Step 4: Index for search
            await self.search.index_document(
                document, classification, entities, domain_name
            )
            logger.info("Document indexed for search")
            
            # Step 5: Save to database
            if self.db_session:
                repo = DocumentRepository(self.db_session)
                await repo.save(document, classification, entities, domain_name)
                logger.info("Document saved to database")
            
            return {
                "document_id": document.id,
                "title": document.title,
                "classification": {
                    "type": classification.document_type,
                    "category": classification.category,
                    "confidence": classification.confidence,
                },
                "entities_count": len(entities),
                "relations_count": len(relations),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise IOSError(f"Failed to process document: {str(e)}") from e
    
    async def search_documents(
        self,
        query: str,
        domain_name: Optional[str] = None,
        search_type: str = "hybrid",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        """
        Search for documents
        
        Args:
            query: Search query
            domain_name: Optional domain to search in
            search_type: Type of search (full_text, semantic, hybrid)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Search results dictionary
        """
        return await self.search.search(
            query=query,
            domain_name=domain_name,
            search_type=search_type,
            limit=limit,
            offset=offset
        )
    
    async def get_document(self, document_id: str) -> dict:
        """
        Get document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document details
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        if not self.db_session:
            raise IOSError("Database session not available")
        
        repo = DocumentRepository(self.db_session)
        document = await repo.get_by_id(document_id)
        
        if not document:
            raise DocumentNotFoundError(f"Document {document_id} not found")
        
        return document.to_dict()
    
    async def _create_document(
        self,
        file_path: str,
        title: Optional[str],
        author: Optional[str],
        tags: Optional[list[str]]
    ) -> Document:
        """Create document object from file"""
        from datetime import datetime
        import hashlib
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Generate document ID
        doc_id = hashlib.md5(content).hexdigest()
        
        # Create document
        document = Document(
            id=doc_id,
            title=title or Path(file_path).stem,
            content=content.decode('utf-8', errors='ignore'),
            file_path=file_path,
            author=author,
            tags=tags or [],
            creation_date=datetime.now()
        )
        
        return document
    
    async def shutdown(self):
        """Cleanup and shutdown"""
        logger.info("Shutting down IOS System")
        # TODO: Close connections, cleanup resources
```

**Checkpoint Day 2:**
```bash
# Verify setup
python -c "from ios_core.system import IOSSystem; print('✓ Import successful')"
pytest --collect-only  # Should show 0 tests (we'll add them next)
black --check ios_core/
mypy ios_core/
```

#### Day 3-4: Database Models & Repositories

**Файл 4: `ios_core/models/__init__.py`**
```python
"""
SQLAlchemy models for IOS System
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class DocumentModel(Base):
    """Document model"""
    
    __tablename__ = 'documents'
    
    id = Column(String(64), primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    file_path = Column(String(1000))
    author = Column(String(255))
    
    # Classification
    document_type = Column(String(50))
    category = Column(String(100))
    subcategory = Column(String(100))
    classification_confidence = Column(Float)
    
    # Metadata
    domain_name = Column(String(100), index=True)
    tags = Column(JSON)  # Array of strings
    metadata = Column(JSON)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entities = relationship("EntityModel", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'document_type': self.document_type,
            'category': self.category,
            'domain_name': self.domain_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tags': self.tags or [],
        }


class EntityModel(Base):
    """Entity model"""
    
    __tablename__ = 'entities'
    
    id = Column(String(64), primary_key=True)
    type = Column(String(50), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    properties = Column(JSON)
    
    # Source
    source_document_id = Column(String(64), ForeignKey('documents.id'))
    confidence = Column(Float, default=1.0)
    
    # Domain
    domain_name = Column(String(100), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="entities")
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'properties': self.properties or {},
            'confidence': self.confidence,
        }


class RelationModel(Base):
    """Relation model"""
    
    __tablename__ = 'relations'
    
    id = Column(String(64), primary_key=True)
    type = Column(String(50), nullable=False, index=True)
    
    source_entity_id = Column(String(64), index=True)
    target_entity_id = Column(String(64), index=True)
    
    properties = Column(JSON)
    confidence = Column(Float, default=1.0)
    
    # Source
    source_document_id = Column(String(64))
    domain_name = Column(String(100), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'source_id': self.source_entity_id,
            'target_id': self.target_entity_id,
            'properties': self.properties or {},
        }


class DomainModel(Base):
    """Domain model"""
    
    __tablename__ = 'domains'
    
    name = Column(String(100), primary_key=True)
    language = Column(String(10), default='de')
    description = Column(Text)
    config = Column(JSON)
    
    # Statistics (cached)
    documents_count = Column(Integer, default=0)
    entities_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Файл 5: `ios_core/repositories/document_repository.py`**
```python
"""
Repository pattern for documents
"""

from typing import Optional, List
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DocumentModel, EntityModel
from ..exceptions import DocumentNotFoundError


class DocumentRepository:
    """Repository for document operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(
        self,
        document,
        classification,
        entities: List,
        domain_name: str
    ) -> DocumentModel:
        """
        Save document to database
        
        Args:
            document: Document object
            classification: Classification result
            entities: List of extracted entities
            domain_name: Domain name
            
        Returns:
            Saved DocumentModel
        """
        # Create document model
        doc_model = DocumentModel(
            id=document.id,
            title=document.title,
            content=document.content[:10000],  # Truncate for storage
            file_path=document.file_path,
            author=document.author,
            document_type=classification.document_type,
            category=classification.category,
            subcategory=classification.subcategory,
            classification_confidence=classification.confidence,
            domain_name=domain_name,
            tags=document.tags,
        )
        
        self.session.add(doc_model)
        
        # Save entities
        for entity in entities:
            entity_model = EntityModel(
                id=entity.id,
                type=entity.type,
                name=entity.name,
                properties=entity.properties,
                source_document_id=document.id,
                confidence=entity.confidence,
                domain_name=domain_name,
            )
            self.session.add(entity_model)
        
        await self.session.commit()
        await self.session.refresh(doc_model)
        
        return doc_model
    
    async def get_by_id(self, document_id: str) -> Optional[DocumentModel]:
        """Get document by ID"""
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_domain(
        self,
        domain_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentModel]:
        """List documents in domain"""
        result = await self.session.execute(
            select(DocumentModel)
            .where(DocumentModel.domain_name == domain_name)
            .limit(limit)
            .offset(offset)
            .order_by(DocumentModel.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def count_by_domain(self, domain_name: str) -> int:
        """Count documents in domain"""
        result = await self.session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.domain_name == domain_name)
        )
        return result.scalar_one()
    
    async def delete(self, document_id: str):
        """Delete document"""
        await self.session.execute(
            delete(DocumentModel).where(DocumentModel.id == document_id)
        )
        await self.session.commit()
```

**Файл 6: `alembic.ini` и миграции**
```bash
# Initialize Alembic
alembic init migrations

# Edit alembic.ini
sqlalchemy.url = postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_db

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Run migration
alembic upgrade head
```

**Checkpoint Day 4:**
```bash
# Test database setup
python -c "
from ios_core.models import Base
from sqlalchemy import create_engine
engine = create_engine('postgresql://ios_user:ios_password@localhost:5432/ios_db')
Base.metadata.create_all(engine)
print('✓ Database schema created')
"
```

#### Day 5-7: First Integration Test

**Файл 7: `tests/integration/test_document_pipeline.py`**
```python
"""
Integration test for complete document processing pipeline
This is the most important test - it validates the entire system
"""

import pytest
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ios_core.system import IOSSystem
from ios_core.models import Base
from ios_core.config import settings


@pytest.fixture
async def db_session():
    """Create test database session"""
    # Use test database
    engine = create_async_engine(
        "postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_test",
        echo=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_document_path(tmp_path):
    """Create test document"""
    doc_path = tmp_path / "test_widerspruch.txt"
    doc_path.write_text("""
    Widerspruch gegen Bescheid vom 15.11.2024
    
    Sehr geehrte Damen und Herren,
    
    hiermit widerspreche ich dem Bescheid vom 15.11.2024 über die Ablehnung
    des Persönlichen Budgets gemäß § 29 SGB IX.
    
    Die Ablehnung ist rechtswidrig, da die Voraussetzungen nach § 29 SGB IX
    eindeutig erfüllt sind.
    
    Zuständigkeit liegt beim Bezirk Oberbayern gemäß § 98 SGB IX.
    
    Mit freundlichen Grüßen
    Max Mustermann
    """)
    return str(doc_path)


@pytest.mark.asyncio
async def test_complete_document_pipeline(db_session, test_document_path):
    """
    Test complete document processing pipeline
    
    This test validates:
    1. Document processing
    2. Classification
    3. Entity extraction
    4. Relation extraction
    5. Database storage
    6. Search indexing
    """
    # Initialize system
    ios = IOSSystem(db_session=db_session)
    
    # Process document
    result = await ios.process_document(
        file_path=test_document_path,
        domain_name="SGB-IX",
        title="Test Widerspruch",
        tags=["test", "widerspruch"]
    )
    
    # Verify result
    assert result['status'] == 'success'
    assert result['document_id'] is not None
    assert result['classification']['type'] == 'Widerspruch'
    assert result['classification']['confidence'] > 0.7
    assert result['entities_count'] > 0
    
    # Verify document in database
    document = await ios.get_document(result['document_id'])
    assert document['title'] == 'Test Widerspruch'
    assert document['domain_name'] == 'SGB-IX'
    
    # Verify search indexing
    search_results = await ios.search_documents(
        query="Widerspruch",
        domain_name="SGB-IX"
    )
    assert search_results['total_count'] > 0
    assert any(
        doc['doc_id'] == result['document_id'] 
        for doc in search_results['results']
    )
    
    print("✓ Complete pipeline test passed!")


@pytest.mark.asyncio
async def test_entity_extraction(db_session, test_document_path):
    """Test that entities are correctly extracted"""
    ios = IOSSystem(db_session=db_session)
    
    result = await ios.process_document(
        file_path=test_document_path,
        domain_name="SGB-IX"
    )
    
    # Should extract:
    # - § 29 (Paragraph)
    # - § 98 (Paragraph)
    # - SGB IX (Gesetz)
    # - Bezirk Oberbayern (Behörde)
    # - Persönliches Budget (Leistung)
    
    assert result['entities_count'] >= 3  # At minimum
    
    print("✓ Entity extraction test passed!")


@pytest.mark.asyncio
async def test_classification_accuracy(db_session, tmp_path):
    """Test classification with different document types"""
    ios = IOSSystem(db_session=db_session)
    
    test_cases = [
        {
            "content": "Antrag auf Persönliches Budget gemäß § 29 SGB IX...",
            "expected_type": "Antrag",
            "filename": "antrag.txt"
        },
        {
            "content": "Bescheid: Die Leistung wird bewilligt...",
            "expected_type": "Bescheid",
            "filename": "bescheid.txt"
        },
        {
            "content": "Widerspruch gegen den Bescheid vom...",
            "expected_type": "Widerspruch",
            "filename": "widerspruch.txt"
        },
    ]
    
    for test_case in test_cases:
        # Create test file
        file_path = tmp_path / test_case['filename']
        file_path.write_text(test_case['content'])
        
        # Process
        result = await ios.process_document(
            file_path=str(file_path),
            domain_name="SGB-IX"
        )
        
        # Verify
        assert result['classification']['type'] == test_case['expected_type'], \
            f"Expected {test_case['expected_type']}, got {result['classification']['type']}"
    
    print("✓ Classification accuracy test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Запуск тестов:**
```bash
# Setup test database
createdb ios_test
psql ios_test -c "CREATE USER ios_user WITH PASSWORD 'ios_password';"
psql ios_test -c "GRANT ALL PRIVILEGES ON DATABASE ios_test TO ios_user;"

# Run tests
pytest tests/integration/test_document_pipeline.py -v -s

# Expected output:
# test_complete_document_pipeline PASSED
# test_entity_extraction PASSED
# test_classification_accuracy PASSED
```

**Checkpoint Day 7:**
```bash
# All integration tests should pass
pytest tests/integration/ -v

# Check code quality
black --check .
mypy ios_core/
ruff check .

# Commit milestone
git add .
git commit -m "Week 1 complete: Core integration + first tests"
git tag v0.1.0-week1
```

---

### WEEK 2: Service Layer Implementation

#### Day 8-10: Classification Service

**Файл 8: `ios_core/services/classifier.py`**
```python
"""
Classification service - wraps the classification engine
"""

import logging
from typing import Dict, List
from dataclasses import dataclass

from ..models import Document

logger = logging.getLogger(__name__)


@dataclass
class Classification:
    """Classification result"""
    document_type: str
    category: str
    subcategory: str = ""
    confidence: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ClassificationService:
    """Service for document classification"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.rule_classifier = RuleBasedClassifier()
        # ML classifier будет добавлен позже
    
    async def classify(self, document: Document) -> Classification:
        """
        Classify document
        
        Args:
            document: Document to classify
            
        Returns:
            Classification result
        """
        logger.info(f"Classifying document: {document.title}")
        
        # Extract features
        features = self.feature_extractor.extract(document)
        
        # Apply rule-based classifier
        classification = self.rule_classifier.classify(features)
        
        logger.info(
            f"Classified as {classification.document_type} "
            f"with confidence {classification.confidence:.2f}"
        )
        
        return classification


class FeatureExtractor:
    """Extract features from documents"""
    
    def extract(self, document: Document) -> Dict:
        """Extract all features"""
        content = document.content.lower()
        
        features = {
            'keywords': self._extract_keywords(content),
            'entities': self._extract_entities(content),
            'structure': self._analyze_structure(content),
        }
        
        return features
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords"""
        keywords = []
        
        # Common German legal keywords
        keyword_patterns = {
            'widerspruch': ['widerspruch', 'widerspreche'],
            'antrag': ['antrag', 'beantrage'],
            'bescheid': ['bescheid', 'bewilligungsbescheid'],
            'urteil': ['urteil', 'im namen des volkes'],
        }
        
        for category, patterns in keyword_patterns.items():
            if any(pattern in content for pattern in patterns):
                keywords.append(category)
        
        return keywords
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities (simplified)"""
        import re
        entities = []
        
        # Paragraphs
        paragraphs = re.findall(r'§\s*(\d+[a-z]?)', content)
        entities.extend([f"§{p}" for p in paragraphs])
        
        # Laws
        laws = re.findall(r'(SGB[\s-]?[IVX]+)', content, re.IGNORECASE)
        entities.extend(laws)
        
        return entities
    
    def _analyze_structure(self, content: str) -> Dict:
        """Analyze document structure"""
        lines = content.split('\n')
        
        return {
            'line_count': len(lines),
            'has_signature': any('mit freundlichen grüßen' in line.lower() for line in lines),
            'has_date': any(self._contains_date(line) for line in lines),
        }
    
    def _contains_date(self, text: str) -> bool:
        """Check if text contains a date"""
        import re
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        return bool(re.search(date_pattern, text))


class RuleBasedClassifier:
    """Rule-based document classifier"""
    
    def classify(self, features: Dict) -> Classification:
        """Classify based on rules"""
        keywords = features.get('keywords', [])
        entities = features.get('entities', [])
        structure = features.get('structure', {})
        
        # Rule 1: Widerspruch
        if 'widerspruch' in keywords and structure.get('has_signature'):
            return Classification(
                document_type='Widerspruch',
                category='Legal',
                subcategory='Objection',
                confidence=0.9,
                tags=['legal', 'objection']
            )
        
        # Rule 2: Antrag
        if 'antrag' in keywords and '§29' in entities:
            return Classification(
                document_type='Antrag',
                category='Application',
                subcategory='Personal Budget',
                confidence=0.85,
                tags=['application', 'personal-budget']
            )
        
        # Rule 3: Bescheid
        if 'bescheid' in keywords and structure.get('has_signature'):
            return Classification(
                document_type='Bescheid',
                category='Decision',
                confidence=0.9,
                tags=['decision', 'official']
            )
        
        # Rule 4: Urteil
        if 'urteil' in keywords:
            return Classification(
                document_type='Urteil',
                category='Legal',
                subcategory='Court Decision',
                confidence=0.95,
                tags=['court', 'decision']
            )
        
        # Default: Unknown
        return Classification(
            document_type='Unknown',
            category='Uncategorized',
            confidence=0.5,
            tags=['uncategorized']
        )
```

**Unit tests для classification:**
```python
# tests/unit/test_classification.py

import pytest
from ios_core.services.classifier import ClassificationService, FeatureExtractor
from ios_core.models import Document


@pytest.fixture
def classifier():
    return ClassificationService()


def test_classify_widerspruch(classifier):
    """Test Widerspruch classification"""
    doc = Document(
        id="test1",
        title="Widerspruch",
        content="""
        Widerspruch gegen Bescheid vom 15.11.2024
        
        Sehr geehrte Damen und Herren,
        hiermit widerspreche ich dem Bescheid.
        
        Mit freundlichen Grüßen
        """,
        file_path="",
        creation_date=None
    )
    
    result = await classifier.classify(doc)
    
    assert result.document_type == "Widerspruch"
    assert result.confidence > 0.8


def test_feature_extraction():
    """Test feature extraction"""
    extractor = FeatureExtractor()
    
    content = "Gemäß § 29 SGB IX beantrage ich..."
    features = extractor.extract(Document(
        id="test",
        content=content,
        title="",
        file_path="",
        creation_date=None
    ))
    
    assert '§29' in features['entities']
    assert any('sgb' in e.lower() for e in features['entities'])
```

#### Day 11-14: Knowledge Graph & Search Services

Аналогично создаем `ios_core/services/knowledge_graph.py` и `ios_core/services/search.py` с unit тестами.

**Checkpoint Day 14:**
```bash
# Run all tests
pytest -v

# Should show:
# - Unit tests: ~15 passing
# - Integration tests: ~3 passing

# Code coverage
pytest --cov=ios_core --cov-report=html
# Target: >60% coverage
```

---

### WEEKS 3-4: API & Real Data Testing

*(Продолжение следует с детализацией остальных недель...)*

---

**Хотите, чтобы я продолжил с детализацией остальных недель (3-8) или вы хотите сначала реализовать Week 1-2 и затем получить следующую порцию плана?**