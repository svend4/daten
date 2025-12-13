"""
Database optimization script
"""

from sqlalchemy import text
import asyncio
from ios_core.database import engine


async def create_indexes():
    """Create additional indexes for performance"""
    
    indexes = [
        # Documents
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_domain_created ON documents(domain_name, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_type_domain ON documents(document_type, domain_name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_created ON documents(created_at DESC)",
        
        # Entities
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_type_domain ON entities(type, domain_name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_name ON entities(name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_source ON entities(source_document_id)",
        
        # Relations
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_source ON relations(source_entity_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_target ON relations(target_entity_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_relations_type ON relations(type)",
        
        # Full-text search on title and content
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_docs_title_gin ON documents USING gin(to_tsvector('german', title))",
    ]
    
    async with engine.begin() as conn:
        for index_sql in indexes:
            print(f"Creating index: {index_sql[:80]}...")
            await conn.execute(text(index_sql))
            print("  ✓ Created")
    
    print("\n✓ All indexes created")


async def analyze_tables():
    """Run ANALYZE on all tables"""
    
    tables = ['documents', 'entities', 'relations', 'domains']
    
    async with engine.begin() as conn:
        for table in tables:
            print(f"Analyzing table: {table}")
            await conn.execute(text(f"ANALYZE {table}"))
            print("  ✓ Done")
    
    print("\n✓ All tables analyzed")


async def vacuum_database():
    """Run VACUUM on database"""
    
    async with engine.begin() as conn:
        print("Running VACUUM...")
        await conn.execute(text("VACUUM ANALYZE"))
        print("✓ VACUUM complete")


if __name__ == "__main__":
    asyncio.run(create_indexes())
    asyncio.run(analyze_tables())
    asyncio.run(vacuum_database())