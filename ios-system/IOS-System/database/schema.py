"""
Production Data Schema для IOS System
Полная схема БД для production deployment
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Float, Index, UniqueConstraint,
    Enum as SQLEnum, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# Enums
class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API = "api"


class DocumentStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentCategory(enum.Enum):
    REPORT = "report"
    MEMO = "memo"
    NOTE = "note"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    PRESENTATION = "presentation"
    OTHER = "other"


# Association Tables (Many-to-Many)
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    Index('idx_document_tags_document', 'document_id'),
    Index('idx_document_tags_tag', 'tag_id')
)

document_permissions = Table(
    'document_permissions',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('permission_level', String(20), default='read'),
    Index('idx_doc_perms_document', 'document_id'),
    Index('idx_doc_perms_user', 'user_id')
)


# Main Tables
class User(Base):
    """Пользователи системы"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Settings
    settings = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)
    
    # Relationships
    documents = relationship('Document', back_populates='owner', cascade='all, delete-orphan')
    api_keys = relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='user')
    
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_created', 'created_at'),
    )


class Document(Base):
    """Документы"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text)
    content_hash = Column(String(64), index=True)  # SHA-256 hash для дедупликации
    
    # Classification
    category = Column(SQLEnum(DocumentCategory), default=DocumentCategory.OTHER)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Metadata
    file_size = Column(Integer)  # bytes
    file_type = Column(String(50))
    language = Column(String(10), default='en')
    
    # Versioning
    version = Column(Integer, default=1)
    parent_version_id = Column(Integer, ForeignKey('documents.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Search & AI
    vector_id = Column(String(100), index=True)  # ID в Qdrant
    summary = Column(Text)
    keywords = Column(JSON, default=list)
    
    # Statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    owner = relationship('User', back_populates='documents')
    tags = relationship('Tag', secondary=document_tags, back_populates='documents')
    versions = relationship('Document', remote_side=[id])
    embeddings = relationship('DocumentEmbedding', back_populates='document', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_documents_owner', 'owner_id'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_category', 'category'),
        Index('idx_documents_created', 'created_at'),
        Index('idx_documents_updated', 'updated_at'),
        Index('idx_documents_hash', 'content_hash'),
        Index('idx_documents_vector', 'vector_id'),
        Index('idx_documents_fulltext', 'title', 'content', postgresql_using='gin'),
    )


class Tag(Base):
    """Теги для документов"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    color = Column(String(7))  # HEX color
    
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    documents = relationship('Document', secondary=document_tags, back_populates='tags')
    
    __table_args__ = (
        Index('idx_tags_name', 'name'),
        Index('idx_tags_usage', 'usage_count'),
    )


class DocumentEmbedding(Base):
    """Embeddings для документов"""
    __tablename__ = 'document_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    # Embedding data
    embedding_model = Column(String(100), nullable=False)
    embedding_vector = Column(JSON)  # Для небольших embeddings
    vector_id = Column(String(100), index=True)  # ID в векторной БД
    
    # Chunk information (для больших документов)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', back_populates='embeddings')
    
    __table_args__ = (
        Index('idx_embeddings_document', 'document_id'),
        Index('idx_embeddings_model', 'embedding_model'),
        Index('idx_embeddings_vector_id', 'vector_id'),
        UniqueConstraint('document_id', 'chunk_index', 'embedding_model', name='uq_doc_chunk_model'),
    )


class APIKey(Base):
    """API ключи пользователей"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # Первые символы для идентификации
    name = Column(String(100))
    
    # Permissions
    permissions = Column(JSON, default=list)
    rate_limit = Column(Integer, default=1000)  # requests per hour
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='api_keys')
    
    __table_args__ = (
        Index('idx_api_keys_user', 'user_id'),
        Index('idx_api_keys_hash', 'key_hash'),
        Index('idx_api_keys_active', 'is_active'),
    )


class Session(Base):
    """Сессии пользователей"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    
    # Session info
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    device_type = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    
    __table_args__ = (
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_active', 'is_active'),
        Index('idx_sessions_expires', 'expires_at'),
    )


class AuditLog(Base):
    """Audit логи"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event info
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    
    # User info
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    user_email = Column(String(100))
    ip_address = Column(String(45), index=True)
    user_agent = Column(String(255))
    
    # Resource info
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    
    # Action details
    action_result = Column(String(20))
    details = Column(JSON, default=dict)
    
    # Request tracking
    request_id = Column(String(100), index=True)
    session_id = Column(String(100))
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action_type'),
        Index('idx_audit_severity', 'severity'),
        Index('idx_audit_ip', 'ip_address'),
        Index('idx_audit_request', 'request_id'),
    )


class KnowledgeGraphEntity(Base):
    """Сущности в графе знаний"""
    __tablename__ = 'knowledge_graph_entities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Entity info
    entity_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Metadata
    properties = Column(JSON, default=dict)
    confidence_score = Column(Float, default=1.0)
    
    # Source
    source_document_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    relations_from = relationship('KnowledgeGraphRelation', 
                                  foreign_keys='KnowledgeGraphRelation.from_entity_id',
                                  back_populates='from_entity')
    relations_to = relationship('KnowledgeGraphRelation',
                                foreign_keys='KnowledgeGraphRelation.to_entity_id',
                                back_populates='to_entity')
    
    __table_args__ = (
        Index('idx_kg_entity_type', 'entity_type'),
        Index('idx_kg_entity_name', 'name'),
        Index('idx_kg_entity_source', 'source_document_id'),
    )


class KnowledgeGraphRelation(Base):
    """Связи в графе знаний"""
    __tablename__ = 'knowledge_graph_relations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Relation
    from_entity_id = Column(Integer, ForeignKey('knowledge_graph_entities.id', ondelete='CASCADE'))
    to_entity_id = Column(Integer, ForeignKey('knowledge_graph_entities.id', ondelete='CASCADE'))
    relation_type = Column(String(50), nullable=False, index=True)
    
    # Metadata
    properties = Column(JSON, default=dict)
    confidence_score = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_entity = relationship('KnowledgeGraphEntity', 
                               foreign_keys=[from_entity_id],
                               back_populates='relations_from')
    to_entity = relationship('KnowledgeGraphEntity',
                             foreign_keys=[to_entity_id],
                             back_populates='relations_to')
    
    __table_args__ = (
        Index('idx_kg_rel_from', 'from_entity_id'),
        Index('idx_kg_rel_to', 'to_entity_id'),
        Index('idx_kg_rel_type', 'relation_type'),
        UniqueConstraint('from_entity_id', 'to_entity_id', 'relation_type', name='uq_kg_relation'),
    )


class SearchQuery(Base):
    """История поисковых запросов"""
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query info
    query_text = Column(String(500), nullable=False)
    query_type = Column(String(20))  # semantic, keyword, etc.
    
    # User info
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    ip_address = Column(String(45))
    
    # Results
    results_count = Column(Integer, default=0)
    response_time_ms = Column(Float)
    
    # Metadata
    filters = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_search_user', 'user_id'),
        Index('idx_search_created', 'created_at'),
        Index('idx_search_type', 'query_type'),
    )


# Functions для создания таблиц
def create_all_tables(engine):
    """Создать все таблицы"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Удалить все таблицы"""
    Base.metadata.drop_all(engine)


def get_table_names():
    """Получить список всех таблиц"""
    return [table.name for table in Base.metadata.sorted_tables]
