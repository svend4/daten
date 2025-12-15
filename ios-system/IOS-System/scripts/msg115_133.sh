# What data was accessed by attacker?
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT DISTINCT
      resource_type,
      resource_id,
      action,
      created_at
    FROM audit_logs
    WHERE user_id IN (SELECT id FROM compromised_users)
    OR ip_address IN ('1.2.3.4', '5.6.7.8')
    ORDER BY created_at;
  " > accessed-data.csv

# Export affected user data for GDPR breach notification
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      u.id,
      u.email,
      u.full_name,
      COUNT(DISTINCT d.id) as documents_accessed
    FROM users u
    LEFT JOIN documents d ON d.id IN (
      SELECT resource_id::int FROM audit_logs
      WHERE action = 'read'
      AND user_id IN (SELECT id FROM compromised_users)
      AND resource_type = 'document'
    )
    WHERE u.id IN (SELECT user_id FROM documents WHERE ...)
    GROUP BY u.id
  " > affected-users.csv