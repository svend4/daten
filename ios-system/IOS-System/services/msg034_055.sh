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