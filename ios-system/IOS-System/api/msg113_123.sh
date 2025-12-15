# Current version
kubectl get deployment/ios-api -n ios-production -o json | \
  jq '.spec.template.spec.containers[0].image'

# Previous version
kubectl rollout history deployment/ios-api -n ios-production --revision=1

# Check what changed
git diff v1.0.0 v1.1.0 --stat