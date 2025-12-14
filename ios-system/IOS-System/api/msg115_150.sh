# 1. Rotate API keys
python scripts/security/rotate_api_keys.py --all

# 2. Rotate database passwords
vault write database/rotate-root/postgres

# Force all apps to get new credentials
kubectl rollout restart deployment/ios-api -n ios-production

# 3. Rotate JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 32)
kubectl create secret generic jwt-secret \
  --from-literal=secret=$NEW_JWT_SECRET \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# This invalidates all existing tokens
kubectl rollout restart deployment/ios-api -n ios-production

# 4. Rotate SSL/TLS certificates
certbot renew --force-renewal

# 5. Notify users to change passwords
curl -X POST https://api.ios-system.com/api/admin/force-password-reset \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"all_users": true}'