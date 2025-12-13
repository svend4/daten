# IOS System Production Environment Variables
# Copy to .env.production and fill in values

# ============================================
# Application
# ============================================
APP_ENV=production
APP_NAME="IOS System"
APP_VERSION=1.0.0
LOG_LEVEL=info
DEBUG=false

# ============================================
# Database
# ============================================
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
DATABASE_URL=postgresql+asyncpg://ios:${DB_PASSWORD}@postgres:5432/ios_production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# ============================================
# Redis
# ============================================
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_URL=redis://redis:6379/1

# ============================================
# Elasticsearch
# ============================================
ELASTICSEARCH_URL=http://elasticsearch:9200

# ============================================
# Qdrant
# ============================================
QDRANT_URL=http://qdrant:6333

# ============================================
# Security
# ============================================
JWT_SECRET_KEY=CHANGE_ME_RANDOM_STRING_64_CHARS
JWT_REFRESH_SECRET_KEY=CHANGE_ME_RANDOM_STRING_64_CHARS
ENCRYPTION_KEY=CHANGE_ME_32_BYTES_BASE64

# ============================================
# OAuth Providers
# ============================================
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# ============================================
# External Services
# ============================================
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@ios-system.com

# ============================================
# Monitoring
# ============================================
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
PROMETHEUS_ENABLED=true

GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_STRONG_PASSWORD

# ============================================
# Backup
# ============================================
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=ios-system-backups
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# ============================================
# URLs
# ============================================
APP_URL=https://api.ios-system.com
FRONTEND_URL=https://ios-system.com