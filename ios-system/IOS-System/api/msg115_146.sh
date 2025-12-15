# Check for compromised accounts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT id, email, last_login, is_active
    FROM users
    WHERE last_login > NOW() - INTERVAL '1 hour'
    AND is_active = true
    ORDER BY last_login DESC;
  "

# Check for unauthorized data access
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, action, resource_type, COUNT(*)
    FROM audit_logs
    WHERE action IN ('read', 'download', 'export')
    AND created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id, action, resource_type
    ORDER BY COUNT(*) DESC
    LIMIT 20;
  "

# Check for data exfiltration
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, SUM(bytes_transferred) as total_bytes
    FROM api_requests
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id
    HAVING SUM(bytes_transferred) > 100000000
    ORDER BY total_bytes DESC;
  "