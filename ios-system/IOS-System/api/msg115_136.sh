# Calculate required replicas
CURRENT_REPLICAS=$(kubectl get deployment/ios-api -n ios-production -o jsonpath='{.spec.replicas}')
CURRENT_CPU=$(kubectl top pods -n ios-production | grep ios-api | awk '{sum+=$2} END {print sum}')
CURRENT_RPS=$(curl -s 'https://prometheus.ios-system.com/api/v1/query?query=sum(rate(http_requests_total[5m]))' | jq -r '.data.result[0].value[1]')

echo "Current replicas: $CURRENT_REPLICAS"
echo "Current CPU usage: ${CURRENT_CPU}m"
echo "Current RPS: $CURRENT_RPS"

# If expecting 2x traffic, recommend 2x replicas
RECOMMENDED_REPLICAS=$((CURRENT_REPLICAS * 2))
echo "Recommended replicas for 2x traffic: $RECOMMENDED_REPLICAS"