#!/bin/bash
# Setup observability stack

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         OBSERVABILITY STACK SETUP                          ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"

mkdir -p observability/logstash/pipeline
mkdir -p observability/logstash/config
mkdir -p observability/filebeat
mkdir -p observability/kibana/dashboards

echo -e "${GREEN}✓ Directories created${NC}"

# Generate secrets
echo -e "\n${YELLOW}Generating secrets...${NC}"

if [ ! -f .env.observability ]; then
    cat > .env.observability << EOF
# Observability Stack Configuration
SENTRY_SECRET_KEY=$(openssl rand -hex 32)
SENTRY_DB_PASSWORD=$(openssl rand -hex 16)

# Jaeger
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831

# Elasticsearch
ES_JAVA_OPTS=-Xms2g -Xmx2g

# Environment
ENVIRONMENT=production
VERSION=1.1.0
SERVICE_NAME=ios-system
EOF

    echo -e "${GREEN}✓ Secrets generated in .env.observability${NC}"
else
    echo -e "${YELLOW}⚠ .env.observability already exists${NC}"
fi

# Create Logstash config
cat > observability/logstash/config/logstash.yml << 'EOF'
http.host: "0.0.0.0"
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.hosts: ["http://elasticsearch:9200"]
EOF

# Start observability stack
echo -e "\n${YELLOW}Starting observability stack...${NC}"

docker-compose -f docker-compose.observability.yml up -d

# Wait for services
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"

sleep 30

# Check Elasticsearch
echo -e "\n${YELLOW}Checking Elasticsearch...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null; then
        echo -e "${GREEN}✓ Elasticsearch ready${NC}"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Check Kibana
echo -e "\n${YELLOW}Checking Kibana...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:5601/api/status > /dev/null; then
        echo -e "${GREEN}✓ Kibana ready${NC}"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Create Kibana index patterns
echo -e "\n${YELLOW}Creating Kibana index patterns...${NC}"

curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/ios-logs" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "title": "ios-logs-*",
      "timeFieldName": "@timestamp"
    }
  }' 2>/dev/null && echo -e "${GREEN}✓ Index pattern created${NC}" || echo -e "${YELLOW}⚠ Index pattern may already exist${NC}"

# Setup Sentry
echo -e "\n${YELLOW}Setting up Sentry...${NC}"

# Run Sentry upgrade
docker-compose -f docker-compose.observability.yml run --rm sentry upgrade --noinput

echo -e "\n${GREEN}✓ Sentry configured${NC}"

# Print summary
echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            OBSERVABILITY STACK READY                       ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}Access URLs:${NC}"
echo "  Jaeger UI:        http://localhost:16686"
echo "  Kibana:           http://localhost:5601"
echo "  Elasticsearch:    http://localhost:9200"
echo "  Sentry:           http://localhost:9000"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Configure Sentry: http://localhost:9000"
echo "  2. Import Kibana dashboards"
echo "  3. Update application config with Sentry DSN"
echo "  4. Restart IOS System to enable tracing"

echo -e "\n${GREEN}Done!${NC}"