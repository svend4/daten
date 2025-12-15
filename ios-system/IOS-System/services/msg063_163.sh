#!/bin/bash
# Performance optimization script

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         PERFORMANCE OPTIMIZATION                           ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}[1/5] Warming up caches...${NC}"

# Warm up Redis cache
python3 << 'EOF'
import asyncio
from ios_core.optimization.cache_manager import cache_manager

async def warmup():
    await cache_manager.initialize()
    print("✓ Cache warmed up")

asyncio.run(warmup())
EOF

echo -e "${GREEN}✓ Caches ready${NC}"

echo -e "\n${YELLOW}[2/5] Pre-indexing common queries...${NC}"

# Index common search queries
python3 << 'EOF'
import asyncio
from ios_core.ml.embeddings import embedding_service

async def preindex():
    await embedding_service.initialize()
    
    common_queries = [
        "Persönliches Budget",
        "Widerspruch gegen Bescheid",
        "Antrag auf Eingliederungshilfe",
        "Leistungen der Pflegeversicherung"
    ]
    
    for query in common_queries:
        # Pre-compute embeddings
        results = await embedding_service.search_similar(query, limit=5)
        print(f"✓ Pre-indexed: {query}")

asyncio.run(preindex())
EOF

echo -e "${GREEN}✓ Common queries indexed${NC}"

echo -e "\n${YELLOW}[3/5] Optimizing database...${NC}"

# Database optimization
psql $DATABASE_URL << 'SQL'
-- Vacuum and analyze
VACUUM ANALYZE documents;
VACUUM ANALYZE search_logs;

-- Update statistics
ANALYZE;

-- Reindex
REINDEX TABLE documents;
SQL

echo -e "${GREEN}✓ Database optimized${NC}"

echo -e "\n${YELLOW}[4/5] Optimizing Elasticsearch...${NC}"

# ES optimization
curl -s -X POST "localhost:9200/ios_documents/_forcemerge?max_num_segments=1" > /dev/null
curl -s -X POST "localhost:9200/_cache/clear" > /dev/null

echo -e "${GREEN}✓ Elasticsearch optimized${NC}"

echo -e "\n${YELLOW}[5/5] Testing performance...${NC}"

# Performance test
python3 << 'EOF'
import asyncio
import time
from ios_core.search.neural_search import neural_search

async def test_performance():
    queries = [
        "Persönliches Budget",
        "Widerspruch",
        "Antrag"
    ]
    
    times = []
    
    for query in queries:
        start = time.time()
        await neural_search.search(query=query, limit=10)
        duration = (time.time() - start) * 1000
        times.append(duration)
        print(f"  {query}: {duration:.0f}ms")
    
    avg = sum(times) / len(times)
    print(f"\n  Average: {avg:.0f}ms")
    
    if avg < 200:
        print("  ✓ Performance: Excellent")
    elif avg < 500:
        print("  ✓ Performance: Good")
    else:
        print("  ⚠ Performance: Needs improvement")

asyncio.run(test_performance())
EOF

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            OPTIMIZATION COMPLETE                           ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}System optimized for production!${NC}"