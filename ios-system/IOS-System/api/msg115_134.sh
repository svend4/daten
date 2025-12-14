# Check pod resource usage
kubectl top pods -n ios-production | sort -k3 -nr | head -10

# Check node resource usage
kubectl top nodes

# Check HPA status (if enabled)
kubectl get hpa -n ios-production

# Query Prometheus for resource trends
curl 'https://prometheus.ios-system.com/api/v1/query?query=avg(rate(container_cpu_usage_seconds_total{namespace="ios-production"}[5m]))*100'

# Check memory usage trend
curl 'https://prometheus.ios-system.com/api/v1/query?query=avg(container_memory_usage_bytes{namespace="ios-production"})/1024/1024'