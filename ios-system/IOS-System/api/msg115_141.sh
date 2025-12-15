# Increase Redis memory
kubectl set resources statefulset/redis -n ios-production \
  --limits=memory=8Gi \
  --requests=memory=4Gi

# Or scale to Redis Cluster
# Deploy Redis Cluster (6 nodes: 3 masters, 3 replicas)
kubectl apply -f kubernetes/redis-cluster.yaml

# Migrate data to cluster
redis-cli --cluster import \
  redis-cluster-0.redis-cluster:6379 \
  --cluster-from redis.ios-production:6379 \
  --cluster-copy \
  --cluster-replace

# Update application to use Redis Cluster
kubectl set env deployment/ios-api -n ios-production \
  REDIS_CLUSTER=true \
  REDIS_NODES="redis-cluster-0:6379,redis-cluster-1:6379,redis-cluster-2:6379"