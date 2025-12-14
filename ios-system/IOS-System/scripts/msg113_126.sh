# cert-manager should auto-renew 30 days before expiry

# 1. Check cert-manager status
kubectl get pods -n cert-manager

# 2. Check certificate resource
kubectl get certificate -n ios-production

# Expected output:
# NAME              READY   SECRET            AGE
# tls-certificate   True    tls-certificate   60d

# 3. Check renewal logs
kubectl logs -n cert-manager deployment/cert-manager | grep renewal

# 4. Force renewal if needed
kubectl delete certificate tls-certificate -n ios-production

# This will trigger immediate renewal

# 5. Wait for renewal
kubectl wait --for=condition=Ready \
  certificate/tls-certificate -n ios-production \
  --timeout=300s

# 6. Verify new certificate
kubectl get secret tls-certificate -n ios-production -o json | \
  jq -r '.data["tls.crt"]' | \
  base64 -d | \
  openssl x509 -noout -dates