# For *.ios-system.com

# 1. Use DNS challenge (required for wildcard)
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d '*.ios-system.com' \
  -d ios-system.com \
  --non-interactive \
  --agree-tos \
  --email admin@ios-system.com

# 2. CloudFlare credentials file (~/.secrets/cloudflare.ini):
# dns_cloudflare_email = admin@ios-system.com
# dns_cloudflare_api_key = YOUR_API_KEY

# 3. Update Kubernetes secret
kubectl create secret tls wildcard-tls \
  --cert=/etc/letsencrypt/live/ios-system.com/fullchain.pem \
  --key=/etc/letsencrypt/live/ios-system.com/privkey.pem \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Update ingress to use wildcard cert
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["*.ios-system.com"],"secretName":"wildcard-tls"}]}}'