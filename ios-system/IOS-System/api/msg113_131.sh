# If automatic renewal fails

# 1. Install certbot
apt-get install -y certbot

# 2. Stop nginx temporarily (if using standalone)
kubectl scale deployment/nginx --replicas=0 -n ios-production

# 3. Generate new certificate
certbot certonly --standalone \
  -d api.ios-system.com \
  -d www.ios-system.com \
  -d grafana.ios-system.com \
  --non-interactive \
  --agree-tos \
  --email admin@ios-system.com

# 4. Create Kubernetes secret
kubectl create secret tls tls-certificate \
  --cert=/etc/letsencrypt/live/api.ios-system.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.ios-system.com/privkey.pem \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart nginx
kubectl scale deployment/nginx --replicas=3 -n ios-production

# 6. Verify
curl -I https://api.ios-system.com