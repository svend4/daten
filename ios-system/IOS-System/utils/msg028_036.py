# Создать persistence layer
# ios_system/models/document.py

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    document_type = Column(String)
    category = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    domain_name = Column(String, index=True)

# ios_system/repositories/document_repository.py

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def save(self, document: Document) -> DocumentModel:
        model = DocumentModel(
            id=document.id,
            title=document.title,
            content=document.content,
            # ...
        )
        self.session.add(model)
        await self.session.commit()
        return model
    
    async def find_by_id(self, doc_id: str) -> Optional[DocumentModel]:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == doc_id)
        )
        return result.scalar_one_or_none()