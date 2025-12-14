# Create namespace
kubectl create namespace ios-system

# Create secrets
kubectl create secret generic ios-secrets \
  --from-literal=db-password=$(openssl rand -hex 16) \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=grafana-password=$(openssl rand -hex 16) \
  -n ios-system

# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods -n ios-system
kubectl get svc -n ios-system
kubectl get ingress -n ios-system

# Logs
kubectl logs -f deployment/ios-api -n ios-system

# Scale
kubectl scale deployment/ios-api --replicas=5 -n ios-system