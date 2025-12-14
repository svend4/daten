# 1. Announce rollback
# Post to #incidents channel

# 2. Rollback deployment
kubectl rollout undo deployment/ios-api -n ios-production
kubectl rollout undo deployment/ios-worker -n ios-production

# 3. Wait for rollout
kubectl rollout status deployment/ios-api -n ios-production --timeout=300s

# 4. Verify health
curl https://api.ios-system.com/health

# 5. Check error rate
watch -n 10 'curl -s "https://prometheus.ios-system.com/api/v1/query?query=api:http_errors:rate5m"'

# 6. Clear application cache
kubectl exec -n ios-production deploy/redis -c redis -- redis-cli FLUSHDB

# 7. Announce rollback complete