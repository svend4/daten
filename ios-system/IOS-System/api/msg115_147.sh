# 1. Block attacker IP(s)
ATTACKER_IP="1.2.3.4"

# Block in Redis (rate limiting)
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli SET "blocked_ip:${ATTACKER_IP}" 1 EX 86400

# Block in WAF
kubectl exec -n ios-production deploy/modsecurity -- \
  bash -c "echo 'SecRule REMOTE_ADDR \"@streq ${ATTACKER_IP}\" \"id:9999,phase:1,deny,status:403\"' >> /etc/modsecurity/custom-rules.conf"

# Block in CloudFlare
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/access_rules/rules" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "block",
    "configuration": {
      "target": "ip",
      "value": "'${ATTACKER_IP}'"
    },
    "notes": "Blocked due to security incident"
  }'

# 2. Force logout all sessions
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli FLUSHDB

# 3. Disable compromised accounts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    UPDATE users
    SET is_active = false
    WHERE id IN (SELECT DISTINCT user_id FROM suspicious_activity);
  "