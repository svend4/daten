"""
Bulk import documents into IOS system
"""

import asyncio
import sys
from pathlib import Path
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ios_core.system import IOSSystem
from ios_core.models import Base
from ios_core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def bulk_import(directory: str, domain_name: str = "SGB-IX"):
    """
    Import all documents from directory
    
    Args:
        directory: Path to directory with documents
        domain_name: Domain to import into
    """
    
    # Setup database
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize IOS
    async with async_session() as session:
        ios = IOSSystem(db_session=session)
        
        # Find all documents
        doc_dir = Path(directory)
        documents = list(doc_dir.glob("**/*.txt")) + \
                   list(doc_dir.glob("**/*.pdf")) + \
                   list(doc_dir.glob("**/*.docx"))
        
        logger.info(f"Found {len(documents)} documents to import")
        
        # Process each document
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for doc_path in documents:
            try:
                logger.info(f"Processing: {doc_path.name}")
                
                result = await ios.process_document(
                    file_path=str(doc_path),
                    domain_name=domain_name,
                    title=doc_path.stem
                )
                
                logger.info(
                    f"  ✓ {result['classification']['type']} "
                    f"(confidence: {result['classification']['confidence']:.2f})"
                )
                logger.info(f"  Entities: {result['entities_count']}")
                
                results["success"] += 1
                
            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}")
                results["failed"] += 1
                results["errors"].append({
                    "file": str(doc_path),
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"Total documents: {len(documents)}")
        print(f"Successfully imported: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error['file']}: {error['error']}")
    
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bulk_import.py <directory> [domain_name]")
        sys.exit(1)
    
    directory = sys.argv[1]
    domain_name = sys.argv[2] if len(sys.argv) > 2 else "SGB-IX"
    
    asyncio.run(bulk_import(directory, domain_name))