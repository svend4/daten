#!/bin/bash
# check_certificates.sh
# Run daily via cron

DOMAINS="api.ios-system.com www.ios-system.com grafana.ios-system.com"
WARN_DAYS=30

for domain in $DOMAINS; do
    expiry=$(echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
        openssl x509 -noout -enddate | sed 's/notAfter=//')
    
    expiry_epoch=$(date -d "$expiry" +%s)
    now_epoch=$(date +%s)
    days_left=$(( ($expiry_epoch - $now_epoch) / 86400 ))
    
    echo "$domain: $days_left days until expiration"
    
    if [ $days_left -lt $WARN_DAYS ]; then
        # Send alert
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"⚠️ Certificate Warning: $domain expires in $days_left days\"
            }"
    fi
done