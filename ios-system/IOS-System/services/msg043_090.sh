# Обновить requirements.txt
cat >> requirements.txt << 'EOF'

# Elasticsearch
elasticsearch[async]==8.11.3
EOF

# Установить
pip install -r requirements.txt

# Обновить .env
cat >> .env << 'EOF'

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_PASSWORD=changeme
ELASTIC_PASSWORD=changeme
EOF