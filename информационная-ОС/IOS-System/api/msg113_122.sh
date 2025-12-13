# Check recent deployments
kubectl rollout history deployment/ios-api -n ios-production

# Get deployment details
kubectl describe deployment/ios-api -n ios-production | grep -A 5 "Events"

# Check when metrics started degrading
curl 'https://prometheus.ios-system.com/api/v1/query_range?query=api:http_errors:rate5m&start='$(date -d '2 hours ago' +%s)'&end='$(date +%s)'&step=60' | \
  jq '.data.result[0].values[] | select(.[1] | tonumber > 0.01)'