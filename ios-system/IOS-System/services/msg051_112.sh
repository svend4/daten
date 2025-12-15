#!/bin/bash
# Setup ML services

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ML SERVICES SETUP                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}[1/6] Creating ML directories...${NC}"
mkdir -p ml_services/bert
mkdir -p ml_services/qdrant
mkdir -p data/models
mkdir -p data/qdrant

echo -e "${GREEN}✓ Directories created${NC}"

echo -e "\n${YELLOW}[2/6] Installing Python dependencies...${NC}"
pip install -r ml_services/bert/requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "\n${YELLOW}[3/6] Downloading BERT models...${NC}"

python3 << 'EOF'
from transformers import AutoTokenizer, AutoModel

# Download German BERT
print("Downloading deepset/gbert-large...")
tokenizer = AutoTokenizer.from_pretrained("deepset/gbert-large")
model = AutoModel.from_pretrained("deepset/gbert-large")
print("✓ GBERT model downloaded")

# Download sentence transformers
print("\nDownloading sentence-transformers/paraphrase-multilingual-mpnet-base-v2...")
from sentence_transformers import SentenceTransformer
st_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
print("✓ Sentence transformer downloaded")

print("\nAll models downloaded successfully!")
EOF

echo -e "${GREEN}✓ Models downloaded${NC}"

echo -e "\n${YELLOW}[4/6] Starting ML services...${NC}"

# Start services
docker-compose -f docker-compose.ml.yml up -d

echo -e "${GREEN}✓ Services started${NC}"

echo -e "\n${YELLOW}[5/6] Waiting for services to be ready...${NC}"

# Wait for BERT server
echo "Waiting for BERT server..."
for i in {1..30}; do
    if curl -sf http://localhost:8001/health > /dev/null; then
        echo -e "${GREEN}✓ BERT server ready${NC}"
        break
    fi
    sleep 2
done

# Wait for Qdrant
echo "Waiting for Qdrant..."
for i in {1..30}; do
    if curl -sf http://localhost:6333/healthz > /dev/null; then
        echo -e "${GREEN}✓ Qdrant ready${NC}"
        break
    fi
    sleep 2
done

echo -e "\n${YELLOW}[6/6] Running database migrations...${NC}"
alembic upgrade head

echo -e "${GREEN}✓ Migrations applied${NC}"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            ML SERVICES READY                               ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}Services running:${NC}"
echo "  • BERT Server:           http://localhost:8001"
echo "  • Qdrant:                http://localhost:6333"
echo "  • Sentence Transformers: http://localhost:8003"

echo -e "\n${GREEN}Next steps:${NC}"
echo "  1. Test BERT API:        curl http://localhost:8001/health"
echo "  2. Index documents:      python scripts/index_documents.py"
echo "  3. Try semantic search:  curl http://localhost:8000/api/semantic/search"

echo -e "\n${GREEN}Done!${NC}"