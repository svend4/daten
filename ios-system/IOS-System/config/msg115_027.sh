# 1. Cordon node (prevent new pods)
kubectl cordon node-to-remove

# 2. Drain node (evict existing pods)
kubectl drain node-to-remove --ignore-daemonsets --delete-emptydir-data

# 3. Verify pods moved
kubectl get pods -o wide | grep node-to-remove

# 4. Delete node from cluster
kubectl delete node node-to-remove

# 5. Terminate instance in cloud provider
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0