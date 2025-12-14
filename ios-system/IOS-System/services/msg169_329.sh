# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=ios_db
DB_USER=ios_user
DB_PASSWORD=secure-password
DB_HOST=postgres
DB_PORT=5432

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Redis
REDIS_URL=redis://redis:6379/0

# Search Configuration
SEARCH_PAGE_SIZE=20
SEARCH_MAX_RESULTS=1000
FUSION_ALGORITHM=rrf
FUSION_K=60