"""
Database Models - UPDATED with embedding fields
"""

# ... (existing imports and code)

class DocumentModel(Base):
    """Document model - UPDATED"""
    
    __tablename__ = "documents"
    
    # ... (existing fields)
    
    # NEW: Embedding tracking
    embedding_indexed = Column(Boolean, default=False, nullable=False)
    embedding_updated_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_embedding_pending', 'embedding_indexed', 'updated_at'),
        # ... (existing indexes)
    )