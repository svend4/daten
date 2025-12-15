# 1. Создать .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# Environment
.env
.env.*
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
EOF

# 2. Создать .env.example
cat > .env.example << 'EOF'
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=ios_db
DB_USER=ios_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTIC_PASSWORD=your-password

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=
GRAFANA_PASSWORD=admin
EOF

# 3. Скопировать в .env
cp .env.example .env
# Отредактировать .env с реальными значениями