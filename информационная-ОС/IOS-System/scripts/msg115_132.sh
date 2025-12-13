# Timeline reconstruction
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      created_at,
      user_id,
      action,
      resource_type,
      ip_address,
      user_agent
    FROM audit_logs
    WHERE created_at > NOW() - INTERVAL '6 hours'
    ORDER BY created_at
  " > timeline.csv

# Analyze access patterns
python3 <<EOF
import pandas as pd
df = pd.read_csv('timeline.csv')

# Group by IP and count actions
ip_analysis = df.groupby('ip_address').agg({
    'action': 'count',
    'user_id': 'nunique'
}).sort_values('action', ascending=False)

print("Top IPs by activity:")
print(ip_analysis.head(20))

# Unusual patterns
unusual = df[
    (df['action'].isin(['admin_access', 'export_data'])) &
    (df['created_at'] > pd.Timestamp.now() - pd.Timedelta(hours=6))
]
print("\nUnusual administrative actions:")
print(unusual)
EOF

# Check for privilege escalation
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      u.id,
      u.email,
      u.is_admin,
      u.updated_at,
      al.action,
      al.created_at
    FROM users u
    JOIN audit_logs al ON al.user_id = u.id
    WHERE u.is_admin = true
    AND u.updated_at > NOW() - INTERVAL '6 hours'
    AND al.action = 'update_user_permissions'
    ORDER BY u.updated_at DESC;
  "