# 1. Enable additional logging
kubectl set env deployment/ios-api -n ios-production \
  LOG_LEVEL=DEBUG \
  SECURITY_LOGGING=true

# 2. Add temporary security rules
kubectl exec -n ios-production deploy/modsecurity -- \
  bash -c "cat >> /etc/modsecurity/custom-rules.conf <<EOF
# Temporary enhanced security
SecRule REQUEST_URI \"@rx /(admin|api)\" \\
  \"id:9001,phase:1,log,auditlog,msg:'Admin/API access monitored'\"
EOF"

# 3. Enable anomaly detection
kubectl set env deployment/ios-api -n ios-production \
  ANOMALY_DETECTION_ENABLED=true \
  ANOMALY_THRESHOLD=0.5