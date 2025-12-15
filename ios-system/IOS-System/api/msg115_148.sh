# 1. Capture logs immediately (before rotation)
mkdir -p /incident-evidence/$(date +%Y%m%d_%H%M%S)
cd /incident-evidence/$(date +%Y%m%d_%H%M%S)

# API logs
kubectl logs -n ios-production deployment/ios-api --all-containers > api-logs.txt

# Database logs
kubectl logs -n ios-production statefulset/postgresql > db-logs.txt

# WAF logs
kubectl logs -n ios-production deployment/modsecurity > waf-logs.txt

# Audit logs
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    COPY (SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours')
    TO STDOUT CSV HEADER
  " > audit-logs.csv

# 2. Capture current state
kubectl get all -n ios-production -o yaml > kubernetes-state.yaml
kubectl describe pods -n ios-production > pod-details.txt
kubectl top pods -n ios-production > resource-usage.txt

# 3. Network capture (if still active)
kubectl exec -n ios-production deployment/ios-api -- \
  tcpdump -i eth0 -w /tmp/capture.pcap -c 10000 &

# 4. Memory dump (if malware suspected)
kubectl exec -n ios-production deployment/ios-api -- \
  cat /proc/kcore > /tmp/memory.dump

# 5. Create tarball
tar czf incident-evidence-$(date +%Y%m%d_%H%M%S).tar.gz .