# Current request rate
curl 'https://prometheus.ios-system.com/api/v1/query?query=sum(rate(http_requests_total[5m]))'

# Request rate by endpoint
curl 'https://prometheus.ios-system.com/api/v1/query?query=topk(10,sum(rate(http_requests_total[5m]))by(endpoint))'

# Check queue depth
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli LLEN task_queue

# Database connection usage
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) as total_connections,
           COUNT(*) FILTER (WHERE state = 'active') as active,
           COUNT(*) FILTER (WHERE state = 'idle') as idle
    FROM pg_stat_activity;
  "