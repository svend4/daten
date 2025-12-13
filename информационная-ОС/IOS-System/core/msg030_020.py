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