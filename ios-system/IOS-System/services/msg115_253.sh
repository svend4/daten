# Nginx - increase worker processes
kubectl set env deployment/nginx -n ios-production \
  WORKER_PROCESSES=8 \
  WORKER_CONNECTIONS=4096

# Or switch to cloud load balancer for better scaling
# AWS ALB
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ios-api-lb
  namespace: ios-production
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: ios-api
  ports:
  - port: 443
    targetPort: 8000
    protocol: TCP
EOF