# Check failed login attempts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*), ip_address, user_agent
    FROM audit_logs
    WHERE action = 'failed_login'
    AND created_at > NOW() - INTERVAL '1 hour'
    GROUP BY ip_address, user_agent
    ORDER BY COUNT(*) DESC
    LIMIT 20;
  "

# Check ModSecurity WAF logs
kubectl logs -n ios-production deploy/modsecurity | \
  grep -i "attack\|malicious\|blocked" | \
  tail -100

# Check suspicious API calls
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "401|403|SQL|script|eval|exec" | \
  tail -50

# Check for unusual user behavior
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, action, COUNT(*)
    FROM audit_logs
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id, action
    HAVING COUNT(*) > 100
    ORDER BY COUNT(*) DESC;
  "