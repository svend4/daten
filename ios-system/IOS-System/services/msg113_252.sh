# ⚠️ Only use in emergency - will cause browser warnings

# 1. Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key \
  -out tls.crt \
  -subj "/CN=api.ios-system.com/O=IOS System"

# 2. Create Kubernetes secret
kubectl create secret tls emergency-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Update ingress
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["api.ios-system.com"],"secretName":"emergency-tls"}]}}'

# 4. Service is now accessible (with browser warning)

# 5. Immediately renew proper certificate
# Follow manual renewal procedure above

# 6. Replace emergency cert with proper cert
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["api.ios-system.com"],"secretName":"tls-certificate"}]}}'