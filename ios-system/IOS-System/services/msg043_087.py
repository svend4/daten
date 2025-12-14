"""
Migration script: Whoosh → Elasticsearch
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.search.migration import SearchMigration
from ios_core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run migration"""
    
    print("="*80)
    print("ELASTICSEARCH MIGRATION")
    print("="*80)
    print()
    
    # Initialize Elasticsearch
    logger.info("Initializing Elasticsearch...")
    es = ElasticsearchService()
    await es.initialize()
    
    # Check cluster health
    health = await es.get_cluster_health()
    logger.info(f"Cluster health: {health['status']}")
    
    if health['status'] == 'red':
        logger.error("Cluster is unhealthy, aborting migration")
        return 1
    
    # Initialize migration
    migration = SearchMigration(es)
    
    # Confirm migration
    print()
    print("This will migrate all documents from Whoosh to Elasticsearch.")
    print("The Whoosh index will NOT be deleted (for rollback).")
    print()
    confirm = input("Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Migration cancelled")
        return 0
    
    print()
    
    # Run migration
    logger.info("Starting migration...")
    stats = await migration.migrate_all(batch_size=500)
    
    print()
    print("="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print(f"Total documents: {stats['total']}")
    print(f"Successfully indexed: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Batches processed: {stats['batches']}")
    print()
    
    # Verify migration
    logger.info("Verifying migration...")
    verification = await migration.verify_migration()
    
    print()
    print("="*80)
    print("VERIFICATION")
    print("="*80)
    print(f"Database count: {verification['database_count']}")
    print(f"Elasticsearch count: {verification['elasticsearch_count']}")
    print(f"Match: {'✓ Yes' if verification['match'] else '✗ No'}")
    print()
    
    # Sample checks
    print("Sample checks:")
    for check in verification['sample_checks']:
        status = "✓" if check['found'] and check['title_match'] else "✗"
        print(f"  {status} {check['id']}")
    
    print()
    
    # Index statistics
    index_stats = await es.get_index_stats()
    print("="*80)
    print("INDEX STATISTICS")
    print("="*80)
    print(f"Total documents: {index_stats['total_docs']}")
    print(f"Total size: {index_stats['total_size_bytes'] / 1024 / 1024:.2f} MB")
    print(f"Shards: {index_stats['shards']}")
    print()
    
    # Close ES connection
    await es.close()
    
    if verification['match']:
        print("✓ Migration successful!")
        print()
        print("Next steps:")
        print("1. Update application config to use Elasticsearch")
        print("2. Test search functionality")
        print("3. Monitor performance")
        print("4. After verification, Whoosh index can be deleted")
        return 0
    else:
        print("✗ Migration verification failed!")
        print()
        print("Run rollback:")
        print("  python scripts/rollback_elasticsearch.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)