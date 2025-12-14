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