# Create HPA for API
kubectl autoscale deployment ios-api \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  -n ios-production

# Or use YAML for more control:
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ios-api-hpa
  namespace: ios-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ios-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
EOF

# Verify HPA
kubectl get hpa -n ios-production

# Watch HPA in action
kubectl get hpa ios-api-hpa -n ios-production --watch

# Check HPA events
kubectl describe hpa ios-api-hpa -n ios-production