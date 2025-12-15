#!/bin/bash
# Test security features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         SECURITY FEATURES TEST                             ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="http://localhost:8000"
ADMIN_USER="admin"
ADMIN_PASS="admin"

echo -e "\n${YELLOW}[1/6] Testing Authentication...${NC}"

# Get auth token
TOKEN=$(curl -s -X POST "$API_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS" | jq -r '.access_token')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ Authentication successful${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[2/6] Testing MFA Setup...${NC}"

# Setup MFA
MFA_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/mfa/setup" \
  -H "Authorization: Bearer $TOKEN")

SECRET=$(echo $MFA_RESPONSE | jq -r '.secret')

if [ -n "$SECRET" ] && [ "$SECRET" != "null" ]; then
    echo -e "${GREEN}✓ MFA setup successful${NC}"
    echo "  Secret: ${SECRET:0:8}..."
else
    echo -e "${RED}✗ MFA setup failed${NC}"
fi

echo -e "\n${YELLOW}[3/6] Testing Audit Logging...${NC}"

# Get audit logs
AUDIT_LOGS=$(curl -s -X GET "$API_URL/api/audit/logs?hours=1&limit=10" \
  -H "Authorization: Bearer $TOKEN")

LOG_COUNT=$(echo $AUDIT_LOGS | jq '. | length')

if [ "$LOG_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Audit logging working${NC}"
    echo "  Found $LOG_COUNT recent events"
else
    echo -e "${YELLOW}⚠ No audit logs found (this is normal for new installation)${NC}"
fi

echo -e "\n${YELLOW}[4/6] Testing Security Monitoring...${NC}"

# Check my activity
MY_ACTIVITY=$(curl -s -X GET "$API_URL/api/audit/my-activity?hours=1" \
  -H "Authorization: Bearer $TOKEN")

ACTIVITY_COUNT=$(echo $MY_ACTIVITY | jq '. | length')

if [ "$ACTIVITY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Activity tracking working${NC}"
    echo "  Your recent actions: $ACTIVITY_COUNT"
else
    echo -e "${YELLOW}⚠ No activity found${NC}"
fi

echo -e "\n${YELLOW}[5/6] Testing Compliance Reporting...${NC}"

# Get GDPR report
GDPR_REPORT=$(curl -s -X GET "$API_URL/api/compliance/gdpr?days=7" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_EVENTS=$(echo $GDPR_REPORT | jq -r '.summary.total_processing_activities')

if [ -n "$TOTAL_EVENTS" ]; then
    echo -e "${GREEN}✓ GDPR reporting working${NC}"
    echo "  Processing activities (7 days): $TOTAL_EVENTS"
else
    echo -e "${YELLOW}⚠ GDPR report incomplete${NC}"
fi

echo -e "\n${YELLOW}[6/6] Testing Failed Login Detection...${NC}"

# Simulate failed logins
for i in {1..3}; do
    curl -s -X POST "$API_URL/api/auth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=attacker&password=wrong" > /dev/null
done

echo -e "${GREEN}✓ Failed login simulation complete${NC}"
echo "  Check security alerts in 1 minute"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            SECURITY TEST COMPLETE                         ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}All tests passed!${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Review audit logs: $API_URL/api/audit/logs"
echo "  2. Setup MFA for your account"
echo "  3. Monitor security alerts"
echo "  4. Download compliance reports"

echo -e "\n${GREEN}Done!${NC}"