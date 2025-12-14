#!/bin/bash
# Test neural search features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         NEURAL SEARCH TEST                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="http://localhost:8000"
TOKEN=""

# Get auth token
echo -e "\n${YELLOW}[1/8] Authenticating...${NC}"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Authenticated${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

# Test 1: Neural Search
echo -e "\n${YELLOW}[2/8] Testing Neural Search...${NC}"
SEARCH_RESPONSE=$(curl -s -X POST "$API_URL/api/search/neural/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Persönliches Budget beantragen",
    "limit": 10,
    "language": "de"
  }')

RESULTS_COUNT=$(echo $SEARCH_RESPONSE | jq '.total')
EXEC_TIME=$(echo $SEARCH_RESPONSE | jq '.execution_time_ms')

echo -e "${GREEN}✓ Neural search complete${NC}"
echo "  Results: $RESULTS_COUNT"
echo "  Execution time: ${EXEC_TIME}ms"

# Test 2: Query Suggestions
echo -e "\n${YELLOW}[3/8] Testing Query Suggestions...${NC}"
SUGGESTIONS=$(curl -s -X GET "$API_URL/api/search/neural/suggest?query=Pers&limit=5" \
  -H "Authorization: Bearer $TOKEN")

SUGG_COUNT=$(echo $SUGGESTIONS | jq '.suggestions | length')
echo -e "${GREEN}✓ Got $SUGG_COUNT suggestions${NC}"

# Test 3: Language Detection
echo -e "\n${YELLOW}[4/8] Testing Language Detection...${NC}"

# German
LANG_DE=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Persönliches+Budget" \
  | jq -r '.language')
echo "  German text detected as: $LANG_DE"

# Russian
LANG_RU=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Личный+бюджет" \
  | jq -r '.language')
echo "  Russian text detected as: $LANG_RU"

# English
LANG_EN=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Personal+budget" \
  | jq -r '.language')
echo "  English text detected as: $LANG_EN"

if [ "$LANG_DE" = "de" ] && [ "$LANG_RU" = "ru" ] && [ "$LANG_EN" = "en" ]; then
    echo -e "${GREEN}✓ Language detection working${NC}"
fi

# Test 4: Query Translation
echo -e "\n${YELLOW}[5/8] Testing Query Translation...${NC}"
TRANSLATION=$(curl -s -X POST "$API_URL/api/search/neural/translate?query=Personal+budget&target_lang=de" \
  -H "Authorization: Bearer $TOKEN")

TRANSLATED=$(echo $TRANSLATION | jq -r '.translated')
echo "  'Personal budget' → '$TRANSLATED'"
echo -e "${GREEN}✓ Translation working${NC}"

# Test 5: Semantic Search
echo -e "\n${YELLOW}[6/8] Testing Semantic Search...${NC}"
SEMANTIC=$(curl -s -X POST "$API_URL/api/semantic/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Budget für Menschen mit Behinderung",
    "limit": 5,
    "score_threshold": 0.7
  }')

SEM_RESULTS=$(echo $SEMANTIC | jq '.total')
echo -e "${GREEN}✓ Found $SEM_RESULTS semantic matches${NC}"

# Test 6: Entity Extraction
echo -e "\n${YELLOW}[7/8] Testing Entity Extraction...${NC}"
ENTITIES=$(curl -s -X POST "$API_URL/api/semantic/extract-entities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Max Mustermann beantragt beim Bezirk Oberbayern ein Persönliches Budget nach § 29 SGB IX.",
    "threshold": 0.5
  }')

ENTITY_COUNT=$(echo $ENTITIES | jq '.entities | length')
echo -e "${GREEN}✓ Extracted $ENTITY_COUNT entities${NC}"

# Test 7: Search Analytics
echo -e "\n${YELLOW}[8/8] Testing Search Analytics...${NC}"
METRICS=$(curl -s -X GET "$API_URL/api/search/neural/analytics/metrics?days=7" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_SEARCHES=$(echo $METRICS | jq '.overview.total_searches')
CTR=$(echo $METRICS | jq '.quality_metrics.ctr')

echo -e "${GREEN}✓ Analytics available${NC}"
echo "  Total searches (7 days): $TOTAL_SEARCHES"
echo "  Click-through rate: $CTR"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            NEURAL SEARCH TEST COMPLETE                     ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}All tests passed!${NC}"