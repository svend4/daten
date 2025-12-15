# Scale API pods
kubectl scale deployment/ios-api --replicas=10 -n ios-production

# Scale worker pods
kubectl scale deployment/ios-worker --replicas=5 -n ios-production

# Verify scaling
kubectl get deployment -n ios-production

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=ios-api \
  -n ios-production \
  --timeout=300s

# Monitor during scale-up
watch -n 5 'kubectl get pods -n ios-production | grep ios-api'

# Check if new pods are receiving traffic
kubectl logs -n ios-production deployment/ios-api --tail=20 | grep "Request received"