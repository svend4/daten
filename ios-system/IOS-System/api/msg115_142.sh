# Example: Product launch, Black Friday, major announcement

# 1 week before:
# - Review capacity planning
# - Test auto-scaling
# - Prepare runbooks

# 3 days before:
# - Scale up infrastructure
kubectl scale deployment/ios-api --replicas=15 -n ios-production
kubectl scale deployment/ios-worker --replicas=8 -n ios-production

# Add extra database read replicas
aws rds create-db-instance-read-replica \
  --db-instance-identifier ios-production-db-replica-2 \
  --source-db-instance-identifier ios-production-db

# Increase Redis memory
kubectl set resources statefulset/redis -n ios-production \
  --limits=memory=16Gi

# 1 day before:
# - Enable CloudFlare "I'm Under Attack" mode (preventive)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -d '{"value":"high"}'

# - Warm caches extensively
curl -X POST https://api.ios-system.com/api/admin/cache/warm \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"document_limit": 10000}'

# - Run load test
k6 run --vus 1000 --duration 30m tests/load/k6-api-load-test.js

# Day of event:
# - War room active
# - All hands on deck
# - Continuous monitoring

# After event (scale down gradually):
# Day 1 after: Scale to 80%
kubectl scale deployment/ios-api --replicas=12 -n ios-production

# Day 3 after: Scale to 60%
kubectl scale deployment/ios-api --replicas=9 -n ios-production

# Week after: Return to normal
kubectl scale deployment/ios-api --replicas=5 -n ios-production