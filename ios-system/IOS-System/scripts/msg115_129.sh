# Analyze actual resource usage
kubectl top pods -n ios-production --containers | \
  awk '{if(NR>1) print $1,$3,$4}' | \
  while read pod cpu mem; do
    echo "Pod: $pod"
    echo "  CPU: $cpu"
    echo "  Memory: $mem"
    
    # Get requests/limits
    kubectl get pod $pod -n ios-production -o json | \
      jq '.spec.containers[0].resources'
  done

# Identify over-provisioned pods (usage < 50% of requests)
# Recommend: Reduce resource requests

# Identify under-provisioned pods (usage > 80% of limits)
# Recommend: Increase resource limits or scale horizontally