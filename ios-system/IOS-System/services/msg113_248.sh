# If new feature causing issues, disable via feature flag

# 1. Disable problematic feature
kubectl set env deployment/ios-api -n ios-production \
  FEATURE_NEW_SEARCH_ENABLED=false

# 2. Restart pods to pick up change
kubectl rollout restart deployment/ios-api -n ios-production

# 3. Verify feature disabled
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.ios-system.com/api/admin/features

# 4. Monitor error rate
watch -n 10 'curl -s "https://prometheus.ios-system.com/api/v1/query?query=api:http_errors:rate5m"'

# This allows keeping new deployment while disabling broken feature