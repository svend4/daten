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