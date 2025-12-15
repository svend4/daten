# AWS EKS - scale node group
aws eks update-nodegroup-config \
  --cluster-name ios-production-cluster \
  --nodegroup-name ios-production-nodes \
  --scaling-config minSize=5,maxSize=15,desiredSize=10

# GKE - scale node pool
gcloud container clusters resize ios-production-cluster \
  --node-pool default-pool \
  --num-nodes 10 \
  --region us-east1

# Azure AKS - scale node pool
az aks nodepool scale \
  --cluster-name ios-production-cluster \
  --name nodepool1 \
  --node-count 10 \
  --resource-group ios-production

# Verify new nodes
kubectl get nodes

# Wait for nodes to be ready
kubectl wait --for=condition=ready node --all --timeout=600s

# Check node resources
kubectl top nodes