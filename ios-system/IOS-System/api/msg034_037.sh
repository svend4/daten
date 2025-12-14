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