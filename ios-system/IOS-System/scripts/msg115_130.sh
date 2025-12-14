# Use spot instances for worker nodes (non-critical workloads)

# AWS - create spot node group
aws eks create-nodegroup \
  --cluster-name ios-production-cluster \
  --nodegroup-name ios-production-spot-workers \
  --scaling-config minSize=2,maxSize=10,desiredSize=3 \
  --capacity-type SPOT \
  --instance-types t3.large,t3a.large,t2.large

# Label spot nodes
kubectl label nodes -l eks.amazonaws.com/capacityType=SPOT \
  node-type=spot

# Configure workers to prefer spot nodes
kubectl patch deployment ios-worker -n ios-production -p \
  '{"spec":{"template":{"spec":{"nodeSelector":{"node-type":"spot"},"tolerations":[{"key":"spot","operator":"Exists"}]}}}}'