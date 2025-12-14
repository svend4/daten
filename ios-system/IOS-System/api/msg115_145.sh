# Check for SQL injection attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -i "union\|select\|drop\|insert\|update\|delete" | \
  grep -v "SELECT.*FROM.*WHERE" | \
  tail -50

# Check for XSS attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -i "script\|onerror\|onload\|alert" | \
  tail -50

# Check for path traversal
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "\.\./|\.\.\\\\|/etc/passwd|/etc/shadow" | \
  tail -50

# Check for RCE attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "eval\(|exec\(|system\(|passthru\(|shell_exec" | \
  tail -50

# Check network connections
kubectl exec -n ios-production deployment/ios-api -- \
  netstat -an | grep ESTABLISHED