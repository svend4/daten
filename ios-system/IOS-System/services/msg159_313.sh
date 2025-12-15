# Rebuild all indices
python manage.py rebuild_search_index --force

# Rebuild only Elasticsearch
python manage.py rebuild_search_index --service elasticsearch --batch-size 200

# Rebuild only Qdrant
python manage.py rebuild_search_index --service qdrant

# Index single document
python manage.py index_document 12345678-1234-1234-1234-123456789012