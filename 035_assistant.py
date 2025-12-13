Пользователь хочет продолжить с детализацией недель 7-16. Продолжу с той же степенью детализации, включая конкретные файлы, команды, чекпоинты.

Weeks 7-8: Production Deployment
Weeks 9-10: Monitoring & Security
Weeks 11-12: Advanced Features
Weeks 13-16: Polish & Release# ДЕТАЛИЗАЦИЯ WEEKS 7-16 (Продолжение)

---

## 📅 WEEKS 7-8: Production Deployment & Infrastructure

### WEEK 7: Docker & Container Orchestration

#### Day 43-45: Production Docker Setup

**Файл 18: `docker/Dockerfile.production`**
```dockerfile
# Multi-stage build for production

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 ios && \
    mkdir -p /app /data && \
    chown -R ios:ios /app /data

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels

# Install Python packages
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=ios:ios . .

# Switch to non-root user
USER ios

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    IOS_ROOT_PATH=/data/ios-root

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Файл 19: `docker-compose.production.yml`**
```yaml
version: '3.8'

services:
  # ========================================================================
  # IOS API Server
  # ========================================================================
  ios-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.production
      args:
        - BUILD_DATE=${BUILD_DATE}
        - VERSION=${VERSION}
    image: ios-system:${VERSION:-latest}
    container_name: ios-api
    restart: unless-stopped
    
    environment:
      - IOS_ROOT_PATH=/data/ios-root
      - DATABASE_URL=postgresql+asyncpg://ios_user:${DB_PASSWORD}@postgres:5432/ios_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    
    volumes:
      - ios-data:/data/ios-root
      - ios-uploads:/data/uploads
      - ios-exports:/data/exports
      - ./logs:/app/logs
    
    ports:
      - "8000:8000"
    
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    networks:
      - ios-network
    
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ========================================================================
  # PostgreSQL Database
  # ========================================================================
  postgres:
    image: postgres:15-alpine
    container_name: ios-postgres
    restart: unless-stopped
    
    environment:
      - POSTGRES_DB=ios_db
      - POSTGRES_USER=ios_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    
    ports:
      - "5432:5432"
    
    networks:
      - ios-network
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ios_user -d ios_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    command:
      - "postgres"
      - "-c" 
      - "shared_buffers=256MB"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "work_mem=16MB"

  # ========================================================================
  # Redis Cache
  # ========================================================================
  redis:
    image: redis:7-alpine
    container_name: ios-redis
    restart: unless-stopped
    
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    
    volumes:
      - redis-data:/data
    
    ports:
      - "6379:6379"
    
    networks:
      - ios-network
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ========================================================================
  # Nginx Reverse Proxy
  # ========================================================================
  nginx:
    image: nginx:alpine
    container_name: ios-nginx
    restart: unless-stopped
    
    volumes:
      - ./nginx/nginx.production.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ios-exports:/usr/share/nginx/html/exports:ro
      - ./nginx/logs:/var/log/nginx
    
    ports:
      - "80:80"
      - "443:443"
    
    depends_on:
      - ios-api
    
    networks:
      - ios-network
    
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================================================
  # Prometheus Monitoring
  # ========================================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: ios-prometheus
    restart: unless-stopped
    
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus-data:/prometheus
    
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    
    ports:
      - "9090:9090"
    
    networks:
      - ios-network

  # ========================================================================
  # Grafana Dashboards
  # ========================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: ios-grafana
    restart: unless-stopped
    
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=redis-datasource
      - GF_SERVER_ROOT_URL=http://localhost:3000
    
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    
    ports:
      - "3000:3000"
    
    networks:
      - ios-network
    
    depends_on:
      - prometheus

  # ========================================================================
  # Backup Service
  # ========================================================================
  backup:
    image: postgres:15-alpine
    container_name: ios-backup
    
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=ios_db
      - POSTGRES_USER=ios_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - BACKUP_SCHEDULE=0 2 * * *
    
    volumes:
      - ./backups:/backups
      - ./scripts/backup.sh:/backup.sh:ro
    
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        while true; do
          /backup.sh
          sleep 86400
        done
    
    networks:
      - ios-network
    
    depends_on:
      - postgres

# ============================================================================
# VOLUMES
# ============================================================================
volumes:
  ios-data:
    driver: local
  ios-uploads:
    driver: local
  ios-exports:
    driver: local
  postgres-data:
    driver: local
  redis-data:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local

# ============================================================================
# NETWORKS
# ============================================================================
networks:
  ios-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Файл 20: `nginx/nginx.production.conf`**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

    # Upstream
    upstream ios_api {
        least_conn;
        server ios-api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTP server - redirect to HTTPS
    server {
        listen 80;
        server_name _;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;

        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
        ssl_prefer_server_ciphers off;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://ios_api;
            proxy_http_version 1.1;
            
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            proxy_busy_buffers_size 8k;
        }

        # Document upload (special rate limit)
        location /api/documents/upload {
            limit_req zone=upload_limit burst=5 nodelay;
            
            proxy_pass http://ios_api;
            proxy_http_version 1.1;
            
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Extended timeouts for uploads
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            client_max_body_size 100M;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://ios_api;
            proxy_http_version 1.1;
            
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket timeouts
            proxy_connect_timeout 7d;
            proxy_send_timeout 7d;
            proxy_read_timeout 7d;
        }

        # Static exports
        location /exports/ {
            alias /usr/share/nginx/html/exports/;
            autoindex on;
            
            # Cache control
            expires 1h;
            add_header Cache-Control "public, immutable";
        }

        # Health check (no logging)
        location /health {
            access_log off;
            proxy_pass http://ios_api;
        }

        # Documentation
        location /docs {
            proxy_pass http://ios_api;
        }

        # Metrics (protected)
        location /metrics {
            allow 172.20.0.0/16;  # Only from Docker network
            deny all;
            
            proxy_pass http://ios_api;
        }
    }
}
```

**Checkpoint Day 45:**
```bash
# Build production image
docker build -t ios-system:0.1.0 -f docker/Dockerfile.production .

# Test locally
export DB_PASSWORD=secure_password
export SECRET_KEY=$(openssl rand -hex 32)
export GRAFANA_PASSWORD=admin
export VERSION=0.1.0

docker-compose -f docker-compose.production.yml up -d

# Wait for services
sleep 30

# Health checks
curl http://localhost/health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana

# Test API
TOKEN=$(curl -X POST "http://localhost/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost/api/documents/

# Expected: All services running, API responding
```

#### Day 46-49: Kubernetes Deployment (Optional)

**Файл 21: `k8s/deployment.yaml`**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ios-system

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ios-config
  namespace: ios-system
data:
  IOS_ROOT_PATH: "/data/ios-root"
  DEBUG: "false"

---
apiVersion: v1
kind: Secret
metadata:
  name: ios-secrets
  namespace: ios-system
type: Opaque
stringData:
  db-password: "CHANGE_ME"
  secret-key: "CHANGE_ME"
  grafana-password: "CHANGE_ME"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ios-api
  namespace: ios-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ios-api
  template:
    metadata:
      labels:
        app: ios-api
    spec:
      containers:
      - name: ios-api
        image: ios-system:0.1.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - containerPort: 8000
          name: http
        
        env:
        - name: DATABASE_URL
          value: "postgresql+asyncpg://ios_user:$(DB_PASSWORD)@postgres:5432/ios_db"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ios-secrets
              key: secret-key
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ios-secrets
              key: db-password
        
        envFrom:
        - configMapRef:
            name: ios-config
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        volumeMounts:
        - name: ios-data
          mountPath: /data
      
      volumes:
      - name: ios-data
        persistentVolumeClaim:
          claimName: ios-data-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: ios-api
  namespace: ios-system
spec:
  selector:
    app: ios-api
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ios-ingress
  namespace: ios-system
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ios.yourdomain.com
    secretName: ios-tls
  rules:
  - host: ios.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ios-api
            port:
              number: 8000

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ios-data-pvc
  namespace: ios-system
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ios-api-hpa
  namespace: ios-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ios-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deploy to Kubernetes:**
```bash
# Create namespace
kubectl create namespace ios-system

# Create secrets
kubectl create secret generic ios-secrets \
  --from-literal=db-password=$(openssl rand -hex 16) \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=grafana-password=$(openssl rand -hex 16) \
  -n ios-system

# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods -n ios-system
kubectl get svc -n ios-system
kubectl get ingress -n ios-system

# Logs
kubectl logs -f deployment/ios-api -n ios-system

# Scale
kubectl scale deployment/ios-api --replicas=5 -n ios-system
```

---

### WEEK 8: CI/CD & Automated Deployment

#### Day 50-52: GitHub Actions Pipeline

**Файл 22: `.github/workflows/ci-cd.yml`**
```yaml
name: IOS System CI/CD

on:
  push:
    branches: [ main, develop ]
    tags:
      - 'v*'
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ========================================================================
  # LINT & FORMAT CHECK
  # ========================================================================
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install black isort mypy ruff
        pip install -r requirements.txt
    
    - name: Black check
      run: black --check .
    
    - name: isort check
      run: isort --check-only .
    
    - name: mypy check
      run: mypy ios_core/ api/
    
    - name: ruff check
      run: ruff check .

  # ========================================================================
  # UNIT TESTS
  # ========================================================================
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ios_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/ios_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/unit/ -v --cov=ios_core --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests

  # ========================================================================
  # INTEGRATION TESTS
  # ========================================================================
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ios_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/ios_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/integration/ -v --cov=api --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: integration

  # ========================================================================
  # BUILD DOCKER IMAGE
  # ========================================================================
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test, integration]
    
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: docker/Dockerfile.production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        build-args: |
          BUILD_DATE=${{ github.event.head_commit.timestamp }}
          VERSION=${{ github.sha }}

  # ========================================================================
  # SECURITY SCAN
  # ========================================================================
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # ========================================================================
  # DEPLOY TO STAGING
  # ========================================================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, security]
    if: github.ref == 'refs/heads/develop'
    
    environment:
      name: staging
      url: https://staging.ios-system.com
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_USER }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          cd /opt/ios-system
          git pull origin develop
          docker-compose -f docker-compose.production.yml pull
          docker-compose -f docker-compose.production.yml up -d
          docker-compose -f docker-compose.production.yml exec -T ios-api alembic upgrade head
    
    - name: Run smoke tests
      run: |
        sleep 30
        curl -f https://staging.ios-system.com/health || exit 1
        curl -f https://staging.ios-system.com/api/docs || exit 1

  # ========================================================================
  # DEPLOY TO PRODUCTION
  # ========================================================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, security]
    if: startsWith(github.ref, 'refs/tags/v')
    
    environment:
      name: production
      url: https://ios-system.com
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Create backup
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          /opt/ios-system/scripts/backup.sh
    
    - name: Deploy to production
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/ios-system
          git fetch --tags
          git checkout ${{ github.ref_name }}
          docker-compose -f docker-compose.production.yml pull
          docker-compose -f docker-compose.production.yml up -d
          docker-compose -f docker-compose.production.yml exec -T ios-api alembic upgrade head
    
    - name: Health check
      run: |
        sleep 60
        curl -f https://ios-system.com/health || exit 1
    
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      if: always()
      with:
        status: ${{ job.status }}
        text: 'Production deployment ${{ job.status }}'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}

  # ========================================================================
  # CREATE RELEASE
  # ========================================================================
  release:
    name: Create Release
    runs-on: ubuntu-latest
    needs: deploy-production
    if: startsWith(github.ref, 'refs/tags/v')
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Generate changelog
      id: changelog
      run: |
        echo "## Changes" > CHANGELOG.md
        git log --oneline --no-merges $(git describe --tags --abbrev=0 HEAD^)..HEAD >> CHANGELOG.md
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        body_path: CHANGELOG.md
        draft: false
        prerelease: false
```

**Checkpoint Day 52:**
```bash
# Test CI/CD locally with act
act -j test

# Push to trigger pipeline
git add .
git commit -m "Setup CI/CD pipeline"
git push origin develop

# Check GitHub Actions
# https://github.com/YOUR_USERNAME/ios-system/actions

# Expected:
# ✓ Lint passed
# ✓ Tests passed (unit + integration)
# ✓ Docker build successful
# ✓ Security scan passed
# ✓ Deployed to staging
```

#### Day 53-56: Monitoring Setup

**Файл 23: `monitoring/grafana/dashboards/ios-overview.json`**
```json
{
  "dashboard": {
    "title": "IOS System Overview",
    "panels": [
      {
        "id": 1,
        "title": "API Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "id": 2,
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          }
        ],
        "type": "graph"
      },
      {
        "id": 3,
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "type": "graph"
      },
      {
        "id": 4,
        "title": "Documents Processed",
        "targets": [
          {
            "expr": "ios_documents_total",
            "legendFormat": "{{domain}}"
          }
        ],
        "type": "stat"
      },
      {
        "id": 5,
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active"
          }
        ],
        "type": "graph"
      },
      {
        "id": 6,
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))",
            "legendFormat": "Hit Rate"
          }
        ],
        "type": "gauge"
      }
    ]
  }
}
```

**Alerts configuration:**
```yaml
# monitoring/alerts.yml

groups:
  - name: ios_alerts
    interval: 30s
    rules:
      # API Health
      - alert: APIDown
        expr: up{job="ios-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "IOS API is down"
          description: "API has been down for more than 1 minute"
      
      # Performance
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "95th percentile response time is {{ $value }}s"
      
      # Error Rate
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m])
            /
            rate(http_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # Database
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "{{ $value }} active connections"
      
      # Resources
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="ios-api"} / container_spec_memory_limit_bytes{name="ios-api"} > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
      
      # Business Metrics
      - alert: LowClassificationConfidence
        expr: avg(ios_classification_confidence) < 0.7
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "Low classification confidence"
          description: "Average confidence is {{ $value }}"
```

**Checkpoint Day 56:**
```bash
# Access Grafana
open http://localhost:3000
# Login: admin / (check GRAFANA_PASSWORD in .env)

# Import dashboards
# Settings -> Data Sources -> Add Prometheus
# Dashboards -> Import -> Upload ios-overview.json

# Check alerts
open http://localhost:9090/alerts

# Test alert
# Stop API container
docker-compose stop ios-api
# Wait 1 minute
# Check alert fires in Prometheus

# Restart
docker-compose start ios-api

# Verify alert resolves

git commit -m "Week 7-8 complete: Production deployment + monitoring"
git tag v0.1.0-week8
```

---

## 📅 WEEKS 9-10: Security & Advanced Features

### WEEK 9: Security Hardening

#### Day 57-59: Security Audit & Fixes

**Файл 24: `scripts/security_scan.sh`**
```bash
#!/bin/bash
# Comprehensive security scan

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              IOS SYSTEM SECURITY SCAN                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Dependency vulnerabilities
echo -e "\n${YELLOW}[1/6] Checking Python dependencies for vulnerabilities...${NC}"
pip install safety
safety check --json > security_report_deps.json
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ No known vulnerabilities in dependencies${NC}"
else
    echo -e "${RED}✗ Vulnerabilities found in dependencies${NC}"
    cat security_report_deps.json
fi

# 2. Docker image scanning
echo -e "\n${YELLOW}[2/6] Scanning Docker image...${NC}"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image ios-system:latest \
    --severity HIGH,CRITICAL \
    --format json > security_report_docker.json

CRITICAL_COUNT=$(cat security_report_docker.json | jq '[.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL")] | length')
if [ "$CRITICAL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No critical vulnerabilities in Docker image${NC}"
else
    echo -e "${RED}✗ Found $CRITICAL_COUNT critical vulnerabilities${NC}"
fi

# 3. Secrets scanning
echo -e "\n${YELLOW}[3/6] Scanning for exposed secrets...${NC}"
pip install detect-secrets
detect-secrets scan --all-files > .secrets.baseline
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ No secrets detected${NC}"
else
    echo -e "${RED}✗ Potential secrets found${NC}"
fi

# 4. Code security analysis
echo -e "\n${YELLOW}[4/6] Running Bandit security analysis...${NC}"
pip install bandit
bandit -r ios_core/ api/ -f json -o security_report_bandit.json

HIGH_SEVERITY=$(cat security_report_bandit.json | jq '[.results[] | select(.issue_severity=="HIGH")] | length')
if [ "$HIGH_SEVERITY" -eq 0 ]; then
    echo -e "${GREEN}✓ No high-severity issues found${NC}"
else
    echo -e "${RED}✗ Found $HIGH_SEVERITY high-severity issues${NC}"
fi

# 5. SQL injection check
echo -e "\n${YELLOW}[5/6] Checking for SQL injection vulnerabilities...${NC}"
grep -r "execute(.*%s" ios_core/ api/ || echo -e "${GREEN}✓ No obvious SQL injection patterns${NC}"

# 6. Check for hardcoded secrets
echo -e "\n${YELLOW}[6/6] Checking for hardcoded secrets...${NC}"
HARDCODED=$(grep -r -i "password\|secret\|api_key" ios_core/ api/ --include="*.py" | grep -v "# " | grep -v "\.pyc" | wc -l)
if [ "$HARDCODED" -eq 0 ]; then
    echo -e "${GREEN}✓ No hardcoded secrets found${NC}"
else
    echo -e "${YELLOW}⚠ Found $HARDCODED potential hardcoded values (review manually)${NC}"
fi

# Summary
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo -e "║                    SECURITY SCAN COMPLETE                      ║"
echo -e "╚════════════════════════════════════════════════════════════════╝"
echo -e "\nReports generated:"
echo "  - security_report_deps.json"
echo "  - security_report_docker.json"
echo "  - security_report_bandit.json"
echo "  - .secrets.baseline"
```

**Run security scan:**
```bash
chmod +x scripts/security_scan.sh
./scripts/security_scan.sh

# Fix any found issues
# Common fixes:
# 1. Update vulnerable dependencies
# 2. Remove hardcoded secrets
# 3. Add input validation
# 4. Fix SQL injection risks
```

#### Day 60-63: Implement Advanced Security

**Файл 25: `ios_core/security/encryption.py`**
```python
"""
Data encryption at rest
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

from ..config import settings


class EncryptionManager:
    """Manage encryption/decryption of sensitive data"""
    
    def __init__(self):
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher from key"""
        # Derive key from secret
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ios_system_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.secret_key.encode())
        )
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt file"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.cipher.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_file(self, encrypted_path: str, output_path: str):
        """Decrypt file"""
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.cipher.decrypt(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)


# Global instance
encryption_manager = EncryptionManager()
```

**Файл 26: `ios_core/security/rbac.py`**
```python
"""
Role-Based Access Control
"""

from enum import Enum
from typing import List, Set
from functools import wraps
from fastapi import HTTPException, status


class Permission(Enum):
    """System permissions"""
    
    # Document permissions
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    
    # Domain permissions
    DOMAIN_CREATE = "domain:create"
    DOMAIN_READ = "domain:read"
    DOMAIN_UPDATE = "domain:update"
    DOMAIN_DELETE = "domain:delete"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"


class Role(Enum):
    """System roles"""
    
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.DOCUMENT_READ,
        Permission.DOMAIN_READ,
    },
    Role.CONTRIBUTOR: {
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOMAIN_READ,
    },
    Role.ADMIN: {
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOMAIN_CREATE,
        Permission.DOMAIN_READ,
        Permission.DOMAIN_UPDATE,
        Permission.ADMIN_USERS,
    },
    Role.SUPERADMIN: set(Permission),  # All permissions
}


class RBACManager:
    """RBAC manager"""
    
    @staticmethod
    def has_permission(user_role: str, permission: Permission) -> bool:
        """Check if role has permission"""
        try:
            role = Role(user_role)
            return permission in ROLE_PERMISSIONS[role]
        except (ValueError, KeyError):
            return False
    
    @staticmethod
    def get_user_permissions(user_role: str) -> Set[Permission]:
        """Get all permissions for role"""
        try:
            role = Role(user_role)
            return ROLE_PERMISSIONS[role]
        except ValueError:
            return set()


def require_permission(permission: Permission):
    """Decorator to require permission"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict, **kwargs):
            user_role = current_user.get('role', 'viewer')
            
            if not RBACManager.has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator
```

**Use RBAC in API:**
```python
# api/routes/documents.py

from ios_core.security.rbac import require_permission, Permission

@router.post("/upload")
@require_permission(Permission.DOCUMENT_CREATE)
async def upload_document(
    current_user: dict = Depends(get_current_active_user),
    ...
):
    ...

@router.delete("/{document_id}")
@require_permission(Permission.DOCUMENT_DELETE)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    ...
):
    ...
```

**Checkpoint Day 63:**
```bash
# Run security scan again
./scripts/security_scan.sh

# Expected improvements:
# - No critical vulnerabilities
# - RBAC implemented
# - Encryption available
# - Input validation enhanced
# - SQL injection risks eliminated

# Commit security improvements
git commit -m "Security hardening: RBAC, encryption, vulnerability fixes"
```

---

### WEEK 10: Advanced Features

#### Day 64-66: Background Task Processing

**Файл 27: `ios_core/tasks/celery_app.py`**
```python
"""
Celery application for background tasks
"""

from celery import Celery
from ios_core.config import settings

# Create Celery app
celery_app = Celery(
    'ios_tasks',
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=['ios_core.tasks.document_tasks', 'ios_core.tasks.maintenance_tasks']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    'ios_core.tasks.document_tasks.*': {'queue': 'documents'},
    'ios_core.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
}
```

**Файл 28: `ios_core/tasks/document_tasks.py`**
```python
"""
Background tasks for document processing
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..system import IOSSystem
from ..config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document_async(self, file_path: str, domain_name: str, **kwargs):
    """
    Process document in background
    
    This allows API to return immediately while processing happens async
    """
    try:
        # Setup database connection
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession)
        
        async def _process():
            async with async_session() as session:
                ios = IOSSystem(db_session=session)
                
                result = await ios.process_document(
                    file_path=file_path,
                    domain_name=domain_name,
                    **kwargs
                )
                
                logger.info(f"Document processed: {result['document_id']}")
                return result
        
        # Run async function
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_process())
        
        await engine.dispose()
        
        return result
        
    except Exception as exc:
        logger.error(f"Error processing document: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def batch_process_documents(file_paths: list, domain_name: str):
    """
    Process multiple documents in batch
    """
    results = []
    
    for file_path in file_paths:
        task = process_document_async.delay(file_path, domain_name)
        results.append(task.id)
    
    return {
        'total': len(file_paths),
        'task_ids': results
    }


@celery_app.task
def reindex_domain(domain_name: str):
    """
    Reindex all documents in domain
    """
    # TODO: Implement reindexing
    logger.info(f"Reindexing domain: {domain_name}")
    pass


@celery_app.task
def rebuild_knowledge_graph(domain_name: str):
    """
    Rebuild knowledge graph for domain
    """
    # TODO: Implement graph rebuilding
    logger.info(f"Rebuilding graph for: {domain_name}")
    pass
```

**Update API to use background tasks:**
```python
# api/routes/documents.py

from ios_core.tasks.document_tasks import process_document_async

@router.post("/upload/async", status_code=status.HTTP_202_ACCEPTED)
async def upload_document_async(
    file: UploadFile = File(...),
    domain_name: str = Query(...),
    ...
):
    """
    Upload document and process asynchronously
    
    Returns task ID immediately, processing happens in background
    """
    
    # Save file
    file_path = await save_upload_file(file, domain_name)
    
    # Start background task
    task = process_document_async.delay(
        file_path=str(file_path),
        domain_name=domain_name,
        title=title,
        author=author,
        tags=tags
    )
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Document upload accepted, processing in background"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of background task
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'progress': task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    
    return response
```

**Start Celery worker:**
```bash
# Add to docker-compose.production.yml

  celery-worker:
    image: ios-system:${VERSION:-latest}
    container_name: ios-celery-worker
    command: celery -A ios_core.tasks.celery_app worker --loglevel=info --concurrency=4
    
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    
    volumes:
      - ios-data:/data/ios-root
    
    depends_on:
      - redis
      - postgres
    
    networks:
      - ios-network

  celery-beat:
    image: ios-system:${VERSION:-latest}
    container_name: ios-celery-beat
    command: celery -A ios_core.tasks.celery_app beat --loglevel=info
    
    environment:
      - REDIS_URL=redis://redis:6379/0
    
    depends_on:
      - redis
    
    networks:
      - ios-network
```

#### Day 67-70: Websocket Enhancements & Admin Dashboard

**Enhanced WebSocket with real-time progress:**
```python
# api/websocket.py - Enhanced

from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_tasks: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
    
    async def send_task_progress(self, user_id: str, task_id: str, progress: dict):
        """Send task progress to user"""
        if user_id in self.active_connections:
            message = {
                'type': 'task.progress',
                'task_id': task_id,
                'data': progress
            }
            
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)
    
    async def send_task_complete(self, user_id: str, task_id: str, result: dict):
        """Send task completion"""
        if user_id in self.active_connections:
            message = {
                'type': 'task.complete',
                'task_id': task_id,
                'result': result
            }
            
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)


manager = ConnectionManager()
```

**Checkpoint Day 70:**
```bash
# Test background tasks
curl -X POST "http://localhost/api/documents/upload/async" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_document.pdf" \
  -F "domain_name=SGB-IX"

# Response:
# {
#   "task_id": "abc-123-def",
#   "status": "processing"
# }

# Check task status
curl "http://localhost/api/tasks/abc-123-def" \
  -H "Authorization: Bearer $TOKEN"

# Commit
git commit -m "Week 9-10 complete: Security + Advanced features"
git tag v0.2.0-week10
```

---

*Продолжить с Weeks 11-16 (Final polish, documentation, release)?*