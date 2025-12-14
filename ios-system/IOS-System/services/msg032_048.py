"""
Validate imported data
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from ios_core.models import DocumentModel, EntityModel, DomainModel
from ios_core.config import settings


async def validate():
    """Validate imported data"""
    
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Count documents
        result = await session.execute(
            select(func.count(DocumentModel.id))
        )
        doc_count = result.scalar_one()
        
        # Count entities
        result = await session.execute(
            select(func.count(EntityModel.id))
        )
        entity_count = result.scalar_one()
        
        # Count by type
        result = await session.execute(
            select(
                DocumentModel.document_type,
                func.count(DocumentModel.id)
            ).group_by(DocumentModel.document_type)
        )
        type_counts = dict(result.all())
        
        # Count entities by type
        result = await session.execute(
            select(
                EntityModel.type,
                func.count(EntityModel.id)
            ).group_by(EntityModel.type)
        )
        entity_type_counts = dict(result.all())
        
        # Print report
        print("="*80)
        print("DATA VALIDATION REPORT")
        print("="*80)
        print(f"\nTotal Documents: {doc_count}")
        print("\nDocuments by Type:")
        for doc_type, count in type_counts.items():
            print(f"  {doc_type}: {count}")
        
        print(f"\nTotal Entities: {entity_count}")
        print("\nEntities by Type:")
        for entity_type, count in entity_type_counts.items():
            print(f"  {entity_type}: {count}")
        
        # Verify data quality
        print("\n" + "="*80)
        print("QUALITY CHECKS")
        print("="*80)
        
        checks = []
        
        # Check 1: All documents have classification
        result = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.document_type.is_(None))
        )
        unclassified = result.scalar_one()
        checks.append(("Documents without classification", unclassified, 0))
        
        # Check 2: Documents have entities
        result = await session.execute(
            select(DocumentModel.id, func.count(EntityModel.id))
            .outerjoin(EntityModel)
            .group_by(DocumentModel.id)
            .having(func.count(EntityModel.id) == 0)
        )
        docs_without_entities = len(result.all())
        checks.append(("Documents without entities", docs_without_entities, 0))
        
        # Check 3: Classification confidence
        result = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.classification_confidence < 0.7)
        )
        low_confidence = result.scalar_one()
        checks.append(("Low confidence classifications (<0.7)", low_confidence, doc_count * 0.1))
        
        # Print results
        all_passed = True
        for check_name, actual, expected in checks:
            status = "✓" if actual <= expected else "✗"
            print(f"{status} {check_name}: {actual} (expected <= {expected})")
            if actual > expected:
                all_passed = False
        
        if all_passed:
            print("\n✓ All quality checks passed!")
        else:
            print("\n✗ Some quality checks failed!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(validate())