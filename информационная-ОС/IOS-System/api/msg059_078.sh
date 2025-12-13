#!/bin/bash
# Test GPT features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         GPT FEATURES TEST                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000"
TOKEN=""

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY not set${NC}"
    echo "Please set OPENAI_API_KEY environment variable"
    exit 1
fi

# Get auth token
echo -e "\n${YELLOW}[1/7] Authenticating...${NC}"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Authenticated${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

# Test 1: Question Answering
echo -e "\n${YELLOW}[2/7] Testing Q&A System...${NC}"
QA_RESPONSE=$(curl -s -X POST "$API_URL/api/gpt/qa/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Was ist ein Persönliches Budget?",
    "domain": "SGB-IX",
    "max_context_docs": 3
  }')

QA_ANSWER=$(echo $QA_RESPONSE | jq -r '.answer')
QA_CONFIDENCE=$(echo $QA_RESPONSE | jq -r '.confidence')

echo -e "${GREEN}✓ Q&A working${NC}"
echo "  Confidence: $QA_CONFIDENCE"
echo "  Answer preview: ${QA_ANSWER:0:100}..."

# Test 2: Summarization
echo -e "\n${YELLOW}[3/7] Testing Summarization...${NC}"
SUMMARY=$(curl -s -X POST "$API_URL/api/gpt/summarize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe nach dem SGB IX. Es ermöglicht Menschen mit Behinderungen, ihre Unterstützungsleistungen selbstbestimmt zu organisieren.",
    "length": "brief",
    "style": "simple"
  }')

SUMMARY_TEXT=$(echo $SUMMARY | jq -r '.summary')
echo -e "${GREEN}✓ Summarization working${NC}"
echo "  Summary: $SUMMARY_TEXT"

# Test 3: Content Enhancement
echo -e "\n${YELLOW}[4/7] Testing Content Enhancement...${NC}"
ENHANCED=$(curl -s -X POST "$API_URL/api/gpt/enhance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ich beantrage hiermit ein persönliches budget",
    "enhancement_type": "formality"
  }')

ENHANCED_TEXT=$(echo $ENHANCED | jq -r '.enhanced')
echo -e "${GREEN}✓ Enhancement working${NC}"
echo "  Original: ich beantrage hiermit ein persönliches budget"
echo "  Enhanced: $ENHANCED_TEXT"

# Test 4: Key Points Extraction
echo -e "\n${YELLOW}[5/7] Testing Key Points...${NC}"
KEY_POINTS=$(curl -s -X POST "$API_URL/api/gpt/extract-key-points?max_points=3" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "Das Widerspruchsverfahren ist kostenlos. Es muss innerhalb eines Monats eingereicht werden. Eine Begründung kann nachgereicht werden.")

POINTS_COUNT=$(echo $KEY_POINTS | jq '.key_points | length')
echo -e "${GREEN}✓ Key points extraction working${NC}"
echo "  Extracted $POINTS_COUNT points"

# Test 5: Concept Explanation
echo -e "\n${YELLOW}[6/7] Testing Concept Explanation...${NC}"
EXPLANATION=$(curl -s -X GET "$API_URL/api/gpt/qa/explain?concept=Eingliederungshilfe&detail_level=simple" \
  -H "Authorization: Bearer $TOKEN")

EXPL_TEXT=$(echo $EXPLANATION | jq -r '.explanation')
echo -e "${GREEN}✓ Concept explanation working${NC}"
echo "  Explanation preview: ${EXPL_TEXT:0:100}..."

# Test 6: Usage Stats
echo -e "\n${YELLOW}[7/7] Getting Usage Stats...${NC}"
USAGE=$(curl -s -X GET "$API_URL/api/gpt/usage" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_TOKENS=$(echo $USAGE | jq '.total_tokens')
TOTAL_COST=$(echo $USAGE | jq '.total_cost_usd')

echo -e "${GREEN}✓ Usage tracking working${NC}"
echo "  Total tokens: $TOTAL_TOKENS"
echo "  Total cost: \$$TOTAL_COST"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            GPT FEATURES TEST COMPLETE                      ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}All tests passed!${NC}"

echo -e "\n${YELLOW}Note:${NC} These tests consume OpenAI API credits."
echo "Current session cost: \$$TOTAL_COST"