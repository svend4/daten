"""
Background tasks for document processing
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..system import IOSSystem
from ..config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document_async(self, file_path: str, domain_name: str, **kwargs):
    """
    Process document in background
    
    This allows API to return immediately while processing happens async
    """
    try:
        # Setup database connection
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession)
        
        async def _process():
            async with async_session() as session:
                ios = IOSSystem(db_session=session)
                
                result = await ios.process_document(
                    file_path=file_path,
                    domain_name=domain_name,
                    **kwargs
                )
                
                logger.info(f"Document processed: {result['document_id']}")
                return result
        
        # Run async function
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_process())
        
        await engine.dispose()
        
        return result
        
    except Exception as exc:
        logger.error(f"Error processing document: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def batch_process_documents(file_paths: list, domain_name: str):
    """
    Process multiple documents in batch
    """
    results = []
    
    for file_path in file_paths:
        task = process_document_async.delay(file_path, domain_name)
        results.append(task.id)
    
    return {
        'total': len(file_paths),
        'task_ids': results
    }


@celery_app.task
def reindex_domain(domain_name: str):
    """
    Reindex all documents in domain
    """
    # TODO: Implement reindexing
    logger.info(f"Reindexing domain: {domain_name}")
    pass


@celery_app.task
def rebuild_knowledge_graph(domain_name: str):
    """
    Rebuild knowledge graph for domain
    """
    # TODO: Implement graph rebuilding
    logger.info(f"Rebuilding graph for: {domain_name}")
    pass