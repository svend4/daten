"""
Migration from Whoosh to Elasticsearch
"""

import logging
from typing import List
from pathlib import Path
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DocumentModel, EntityModel
from .elasticsearch_service import ElasticsearchService
from ..database import async_session

logger = logging.getLogger(__name__)


class SearchMigration:
    """Migrate search from Whoosh to Elasticsearch"""
    
    def __init__(self, es_service: ElasticsearchService):
        self.es = es_service
    
    async def migrate_all(self, batch_size: int = 500) -> Dict:
        """
        Migrate all documents from database to Elasticsearch
        
        Args:
            batch_size: Documents per batch
        
        Returns:
            Migration statistics
        """
        
        logger.info("Starting search migration to Elasticsearch")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "batches": 0
        }
        
        async with async_session() as session:
            # Count total documents
            result = await session.execute(
                select(func.count(DocumentModel.id))
            )
            total = result.scalar_one()
            stats["total"] = total
            
            logger.info(f"Migrating {total} documents")
            
            # Migrate in batches
            offset = 0
            while offset < total:
                # Fetch batch
                result = await session.execute(
                    select(DocumentModel)
                    .limit(batch_size)
                    .offset(offset)
                )
                documents = result.scalars().all()
                
                if not documents:
                    break
                
                # Index batch
                batch_stats = await self.es.bulk_index(documents, batch_size)
                
                stats["success"] += batch_stats["success"]
                stats["failed"] += batch_stats["failed"]
                stats["batches"] += 1
                
                offset += batch_size
                
                logger.info(
                    f"Progress: {offset}/{total} "
                    f"({offset/total*100:.1f}%)"
                )
                
                # Small delay to avoid overwhelming ES
                await asyncio.sleep(0.1)
        
        # Refresh index
        await self.es.client.indices.refresh(index=self.es.index_name)
        
        logger.info(f"Migration complete: {stats}")
        return stats
    
    async def verify_migration(self) -> Dict:
        """
        Verify migration was successful
        
        Returns:
            Verification results
        """
        
        logger.info("Verifying migration")
        
        results = {
            "database_count": 0,
            "elasticsearch_count": 0,
            "match": False,
            "sample_checks": []
        }
        
        async with async_session() as session:
            # Count in database
            result = await session.execute(
                select(func.count(DocumentModel.id))
            )
            db_count = result.scalar_one()
            results["database_count"] = db_count
            
            # Count in Elasticsearch
            es_stats = await self.es.get_index_stats()
            es_count = es_stats["total_docs"]
            results["elasticsearch_count"] = es_count
            
            # Check if counts match
            results["match"] = (db_count == es_count)
            
            # Sample random documents
            result = await session.execute(
                select(DocumentModel)
                .order_by(func.random())
                .limit(10)
            )
            sample_docs = result.scalars().all()
            
            # Verify each sample in ES
            for doc in sample_docs:
                try:
                    es_doc = await self.es.client.get(
                        index=self.es.index_name,
                        id=doc.id
                    )
                    
                    check = {
                        "id": doc.id,
                        "found": True,
                        "title_match": es_doc["_source"]["title"] == doc.title
                    }
                except:
                    check = {
                        "id": doc.id,
                        "found": False,
                        "title_match": False
                    }
                
                results["sample_checks"].append(check)
        
        # Log results
        logger.info(f"Verification results: {results}")
        
        if results["match"]:
            logger.info("✓ Migration verified successfully")
        else:
            logger.warning("✗ Migration verification failed")
        
        return results
    
    async def rollback(self):
        """Rollback migration (delete ES index)"""
        
        logger.warning("Rolling back migration")
        
        try:
            await self.es.client.indices.delete(index=self.es.index_name)
            logger.info(f"Deleted index: {self.es.index_name}")
        except Exception as e:
            logger.error(f"Rollback error: {e}")