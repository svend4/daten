# Renew internal service certificates via Vault

# 1. Check current certificate
vault read pki/cert/<serial_number>

# 2. Generate new certificate
vault write pki/issue/ios-system \
  common_name="ios-api.ios-production.svc.cluster.local" \
  ttl="8760h"  # 1 year

# 3. Save certificate and key
vault read -field=certificate pki/issue/ios-system > tls.crt
vault read -field=private_key pki/issue/ios-system > tls.key

# 4. Update Kubernetes secret
kubectl create secret tls internal-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart affected services
kubectl rollout restart deployment/ios-api -n ios-production