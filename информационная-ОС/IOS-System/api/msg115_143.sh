# Don't just scale to 0 replicas immediately

# 1. Reduce gradually (20% at a time)
CURRENT_REPLICAS=$(kubectl get deployment/ios-api -n ios-production -o jsonpath='{.spec.replicas}')
NEW_REPLICAS=$((CURRENT_REPLICAS * 80 / 100))

kubectl scale deployment/ios-api --replicas=$NEW_REPLICAS -n ios-production

# 2. Wait and monitor (10 minutes)
sleep 600

# 3. Check metrics
kubectl top pods -n ios-production | grep ios-api

# 4. Repeat if safe
# Continue reducing by 20% until desired level

# 5. For complete shutdown (maintenance):
# First, enable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"true"}}'

# Then scale down
kubectl scale deployment/ios-api --replicas=0 -n ios-production