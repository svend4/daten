chmod +x scripts/security_scan.sh
./scripts/security_scan.sh

# Fix any found issues
# Common fixes:
# 1. Update vulnerable dependencies
# 2. Remove hardcoded secrets
# 3. Add input validation
# 4. Fix SQL injection risks