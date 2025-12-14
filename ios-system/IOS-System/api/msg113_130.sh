# Check certificate expiration
echo | openssl s_client -connect api.ios-system.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# Check days until expiration
echo | openssl s_client -connect api.ios-system.com:443 2>/dev/null | \
  openssl x509 -noout -enddate | \
  sed 's/notAfter=//' | \
  xargs -I {} date -d {} +%s | \
  awk '{print ($1 - systime()) / 86400 " days until expiration"}'

# Check all domains
for domain in api.ios-system.com www.ios-system.com grafana.ios-system.com; do
  echo "=== $domain ==="
  echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
    openssl x509 -noout -dates
done

# Check Kubernetes secrets
kubectl get secret -n ios-production tls-certificate -o json | \
  jq -r '.data["tls.crt"]' | \
  base64 -d | \
  openssl x509 -noout -dates