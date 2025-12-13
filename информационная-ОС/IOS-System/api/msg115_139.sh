# Increase resource limits for existing pods

# Check current limits
kubectl get deployment/ios-api -n ios-production -o json | \
  jq '.spec.template.spec.containers[0].resources'

# Increase CPU and memory
kubectl set resources deployment/ios-api -n ios-production \
  --limits=cpu=2,memory=4Gi \
  --requests=cpu=1,memory=2Gi

# This will trigger rolling update
kubectl rollout status deployment/ios-api -n ios-production

# Verify new limits
kubectl get pods -n ios-production -l app=ios-api -o json | \
  jq '.items[0].spec.containers[0].resources'