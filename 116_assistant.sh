Пользователь готов продолжить. Создам последние 2 runbooks:
- Scaling Operations
- Security Incident

После этого создам файл с team onboarding guide и завершу весь deployment guide.# 📦 PRODUCTION DEPLOYMENT GUIDE (ПРОДОЛЖЕНИЕ)

## RUNBOOK 9: Scaling Operations

### Symptoms
- High CPU/memory usage (>80%)
- Slow response times under load
- Queue depth growing
- Resource exhaustion warnings
- Traffic spike anticipated

### Impact
- **Severity:** Medium to High
- **User Impact:** Degraded performance
- **Business Impact:** Potential lost revenue

### Investigation Steps

**Step 1: Identify Resource Bottleneck**
```bash
# Check pod resource usage
kubectl top pods -n ios-production | sort -k3 -nr | head -10

# Check node resource usage
kubectl top nodes

# Check HPA status (if enabled)
kubectl get hpa -n ios-production

# Query Prometheus for resource trends
curl 'https://prometheus.ios-system.com/api/v1/query?query=avg(rate(container_cpu_usage_seconds_total{namespace="ios-production"}[5m]))*100'

# Check memory usage trend
curl 'https://prometheus.ios-system.com/api/v1/query?query=avg(container_memory_usage_bytes{namespace="ios-production"})/1024/1024'
```

**Step 2: Analyze Traffic Patterns**
```bash
# Current request rate
curl 'https://prometheus.ios-system.com/api/v1/query?query=sum(rate(http_requests_total[5m]))'

# Request rate by endpoint
curl 'https://prometheus.ios-system.com/api/v1/query?query=topk(10,sum(rate(http_requests_total[5m]))by(endpoint))'

# Check queue depth
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli LLEN task_queue

# Database connection usage
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) as total_connections,
           COUNT(*) FILTER (WHERE state = 'active') as active,
           COUNT(*) FILTER (WHERE state = 'idle') as idle
    FROM pg_stat_activity;
  "
```

**Step 3: Predict Scaling Needs**
```bash
# Calculate required replicas
CURRENT_REPLICAS=$(kubectl get deployment/ios-api -n ios-production -o jsonpath='{.spec.replicas}')
CURRENT_CPU=$(kubectl top pods -n ios-production | grep ios-api | awk '{sum+=$2} END {print sum}')
CURRENT_RPS=$(curl -s 'https://prometheus.ios-system.com/api/v1/query?query=sum(rate(http_requests_total[5m]))' | jq -r '.data.result[0].value[1]')

echo "Current replicas: $CURRENT_REPLICAS"
echo "Current CPU usage: ${CURRENT_CPU}m"
echo "Current RPS: $CURRENT_RPS"

# If expecting 2x traffic, recommend 2x replicas
RECOMMENDED_REPLICAS=$((CURRENT_REPLICAS * 2))
echo "Recommended replicas for 2x traffic: $RECOMMENDED_REPLICAS"
```

### Scaling Procedures

**Horizontal Pod Scaling (Manual)**
```bash
# Scale API pods
kubectl scale deployment/ios-api --replicas=10 -n ios-production

# Scale worker pods
kubectl scale deployment/ios-worker --replicas=5 -n ios-production

# Verify scaling
kubectl get deployment -n ios-production

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=ios-api \
  -n ios-production \
  --timeout=300s

# Monitor during scale-up
watch -n 5 'kubectl get pods -n ios-production | grep ios-api'

# Check if new pods are receiving traffic
kubectl logs -n ios-production deployment/ios-api --tail=20 | grep "Request received"
```

**Horizontal Pod Autoscaling (HPA) Setup**
```bash
# Create HPA for API
kubectl autoscale deployment ios-api \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  -n ios-production

# Or use YAML for more control:
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ios-api-hpa
  namespace: ios-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ios-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
EOF

# Verify HPA
kubectl get hpa -n ios-production

# Watch HPA in action
kubectl get hpa ios-api-hpa -n ios-production --watch

# Check HPA events
kubectl describe hpa ios-api-hpa -n ios-production
```

**Vertical Pod Scaling**
```bash
# Increase resource limits for existing pods

# Check current limits
kubectl get deployment/ios-api -n ios-production -o json | \
  jq '.spec.template.spec.containers[0].resources'

# Increase CPU and memory
kubectl set resources deployment/ios-api -n ios-production \
  --limits=cpu=2,memory=4Gi \
  --requests=cpu=1,memory=2Gi

# This will trigger rolling update
kubectl rollout status deployment/ios-api -n ios-production

# Verify new limits
kubectl get pods -n ios-production -l app=ios-api -o json | \
  jq '.items[0].spec.containers[0].resources'
```

**Cluster Scaling (Add Nodes)**
```bash
# AWS EKS - scale node group
aws eks update-nodegroup-config \
  --cluster-name ios-production-cluster \
  --nodegroup-name ios-production-nodes \
  --scaling-config minSize=5,maxSize=15,desiredSize=10

# GKE - scale node pool
gcloud container clusters resize ios-production-cluster \
  --node-pool default-pool \
  --num-nodes 10 \
  --region us-east1

# Azure AKS - scale node pool
az aks nodepool scale \
  --cluster-name ios-production-cluster \
  --name nodepool1 \
  --node-count 10 \
  --resource-group ios-production

# Verify new nodes
kubectl get nodes

# Wait for nodes to be ready
kubectl wait --for=condition=ready node --all --timeout=600s

# Check node resources
kubectl top nodes
```

**Database Scaling**
```bash
# Vertical scaling - increase instance size
# AWS RDS
aws rds modify-db-instance \
  --db-instance-identifier ios-production-db \
  --db-instance-class db.r5.2xlarge \
  --apply-immediately

# Check modification status
aws rds describe-db-instances \
  --db-instance-identifier ios-production-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Horizontal scaling - add read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier ios-production-db-replica-1 \
  --source-db-instance-identifier ios-production-db \
  --db-instance-class db.r5.xlarge \
  --publicly-accessible

# Configure app to use read replica
kubectl set env deployment/ios-api -n ios-production \
  DATABASE_READ_URL="postgresql://user:pass@replica-endpoint:5432/ios_production"

# Connection pooling - increase pool size
kubectl set env deployment/ios-api -n ios-production \
  DB_POOL_SIZE=50 \
  DB_MAX_OVERFLOW=20
```

**Redis Scaling**
```bash
# Increase Redis memory
kubectl set resources statefulset/redis -n ios-production \
  --limits=memory=8Gi \
  --requests=memory=4Gi

# Or scale to Redis Cluster
# Deploy Redis Cluster (6 nodes: 3 masters, 3 replicas)
kubectl apply -f kubernetes/redis-cluster.yaml

# Migrate data to cluster
redis-cli --cluster import \
  redis-cluster-0.redis-cluster:6379 \
  --cluster-from redis.ios-production:6379 \
  --cluster-copy \
  --cluster-replace

# Update application to use Redis Cluster
kubectl set env deployment/ios-api -n ios-production \
  REDIS_CLUSTER=true \
  REDIS_NODES="redis-cluster-0:6379,redis-cluster-1:6379,redis-cluster-2:6379"
```

**Load Balancer Scaling**
```bash
# Nginx - increase worker processes
kubectl set env deployment/nginx -n ios-production \
  WORKER_PROCESSES=8 \
  WORKER_CONNECTIONS=4096

# Or switch to cloud load balancer for better scaling
# AWS ALB
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ios-api-lb
  namespace: ios-production
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: ios-api
  ports:
  - port: 443
    targetPort: 8000
    protocol: TCP
EOF
```

### Pre-Planned Scaling (Events)

**Before Major Event**
```bash
# Example: Product launch, Black Friday, major announcement

# 1 week before:
# - Review capacity planning
# - Test auto-scaling
# - Prepare runbooks

# 3 days before:
# - Scale up infrastructure
kubectl scale deployment/ios-api --replicas=15 -n ios-production
kubectl scale deployment/ios-worker --replicas=8 -n ios-production

# Add extra database read replicas
aws rds create-db-instance-read-replica \
  --db-instance-identifier ios-production-db-replica-2 \
  --source-db-instance-identifier ios-production-db

# Increase Redis memory
kubectl set resources statefulset/redis -n ios-production \
  --limits=memory=16Gi

# 1 day before:
# - Enable CloudFlare "I'm Under Attack" mode (preventive)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -d '{"value":"high"}'

# - Warm caches extensively
curl -X POST https://api.ios-system.com/api/admin/cache/warm \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"document_limit": 10000}'

# - Run load test
k6 run --vus 1000 --duration 30m tests/load/k6-api-load-test.js

# Day of event:
# - War room active
# - All hands on deck
# - Continuous monitoring

# After event (scale down gradually):
# Day 1 after: Scale to 80%
kubectl scale deployment/ios-api --replicas=12 -n ios-production

# Day 3 after: Scale to 60%
kubectl scale deployment/ios-api --replicas=9 -n ios-production

# Week after: Return to normal
kubectl scale deployment/ios-api --replicas=5 -n ios-production
```

**Scaling Checklist**
```markdown
## Pre-Scaling Checklist
- [ ] Identify bottleneck (CPU, memory, I/O, network)
- [ ] Check current utilization metrics
- [ ] Estimate required capacity
- [ ] Review cost implications
- [ ] Notify team of scaling operation
- [ ] Prepare rollback plan

## During Scaling
- [ ] Execute scaling command
- [ ] Monitor pod/node status
- [ ] Verify new resources receiving traffic
- [ ] Check error rates (should not increase)
- [ ] Monitor latency (should improve)
- [ ] Watch resource utilization

## Post-Scaling
- [ ] Verify metrics improved
- [ ] Document scaling action
- [ ] Update capacity planning
- [ ] Review if auto-scaling should be adjusted
- [ ] Schedule scale-down if temporary
```

### Scale Down Procedures

**Graceful Scale Down**
```bash
# Don't just scale to 0 replicas immediately

# 1. Reduce gradually (20% at a time)
CURRENT_REPLICAS=$(kubectl get deployment/ios-api -n ios-production -o jsonpath='{.spec.replicas}')
NEW_REPLICAS=$((CURRENT_REPLICAS * 80 / 100))

kubectl scale deployment/ios-api --replicas=$NEW_REPLICAS -n ios-production

# 2. Wait and monitor (10 minutes)
sleep 600

# 3. Check metrics
kubectl top pods -n ios-production | grep ios-api

# 4. Repeat if safe
# Continue reducing by 20% until desired level

# 5. For complete shutdown (maintenance):
# First, enable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"true"}}'

# Then scale down
kubectl scale deployment/ios-api --replicas=0 -n ios-production
```

**Remove Nodes**
```bash
# 1. Cordon node (prevent new pods)
kubectl cordon node-to-remove

# 2. Drain node (evict existing pods)
kubectl drain node-to-remove --ignore-daemonsets --delete-emptydir-data

# 3. Verify pods moved
kubectl get pods -o wide | grep node-to-remove

# 4. Delete node from cluster
kubectl delete node node-to-remove

# 5. Terminate instance in cloud provider
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

### Cost Optimization

**Right-Sizing**
```bash
# Analyze actual resource usage
kubectl top pods -n ios-production --containers | \
  awk '{if(NR>1) print $1,$3,$4}' | \
  while read pod cpu mem; do
    echo "Pod: $pod"
    echo "  CPU: $cpu"
    echo "  Memory: $mem"
    
    # Get requests/limits
    kubectl get pod $pod -n ios-production -o json | \
      jq '.spec.containers[0].resources'
  done

# Identify over-provisioned pods (usage < 50% of requests)
# Recommend: Reduce resource requests

# Identify under-provisioned pods (usage > 80% of limits)
# Recommend: Increase resource limits or scale horizontally
```

**Spot Instances for Workers**
```bash
# Use spot instances for worker nodes (non-critical workloads)

# AWS - create spot node group
aws eks create-nodegroup \
  --cluster-name ios-production-cluster \
  --nodegroup-name ios-production-spot-workers \
  --scaling-config minSize=2,maxSize=10,desiredSize=3 \
  --capacity-type SPOT \
  --instance-types t3.large,t3a.large,t2.large

# Label spot nodes
kubectl label nodes -l eks.amazonaws.com/capacityType=SPOT \
  node-type=spot

# Configure workers to prefer spot nodes
kubectl patch deployment ios-worker -n ios-production -p \
  '{"spec":{"template":{"spec":{"nodeSelector":{"node-type":"spot"},"tolerations":[{"key":"spot","operator":"Exists"}]}}}}'
```

### Prevention
- [ ] Enable HPA for all deployments
- [ ] Set up cluster autoscaler
- [ ] Regular capacity planning reviews
- [ ] Load testing in CI/CD
- [ ] Resource usage dashboards
- [ ] Cost monitoring and alerts

### Escalation
- **Resource exhaustion imminent:** Immediate scaling
- **Cost concerns:** Get approval for >50% scale up
- **Major event:** CTO approval for significant scaling

---

## RUNBOOK 10: Security Incident

### Symptoms
- Unauthorized access detected
- Data breach suspected
- DDoS attack
- Malware detected
- Suspicious user activity
- Security scan findings

### Impact
- **Severity:** Critical
- **User Impact:** Potential data compromise
- **Business Impact:** Legal, financial, reputation

### Investigation Steps

**Step 1: Confirm Security Incident**
```bash
# Check failed login attempts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*), ip_address, user_agent
    FROM audit_logs
    WHERE action = 'failed_login'
    AND created_at > NOW() - INTERVAL '1 hour'
    GROUP BY ip_address, user_agent
    ORDER BY COUNT(*) DESC
    LIMIT 20;
  "

# Check ModSecurity WAF logs
kubectl logs -n ios-production deploy/modsecurity | \
  grep -i "attack\|malicious\|blocked" | \
  tail -100

# Check suspicious API calls
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "401|403|SQL|script|eval|exec" | \
  tail -50

# Check for unusual user behavior
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, action, COUNT(*)
    FROM audit_logs
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id, action
    HAVING COUNT(*) > 100
    ORDER BY COUNT(*) DESC;
  "
```

**Step 2: Identify Attack Vector**
```bash
# Check for SQL injection attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -i "union\|select\|drop\|insert\|update\|delete" | \
  grep -v "SELECT.*FROM.*WHERE" | \
  tail -50

# Check for XSS attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -i "script\|onerror\|onload\|alert" | \
  tail -50

# Check for path traversal
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "\.\./|\.\.\\\\|/etc/passwd|/etc/shadow" | \
  tail -50

# Check for RCE attempts
kubectl logs -n ios-production deployment/ios-api | \
  grep -E "eval\(|exec\(|system\(|passthru\(|shell_exec" | \
  tail -50

# Check network connections
kubectl exec -n ios-production deployment/ios-api -- \
  netstat -an | grep ESTABLISHED
```

**Step 3: Assess Impact**
```bash
# Check for compromised accounts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT id, email, last_login, is_active
    FROM users
    WHERE last_login > NOW() - INTERVAL '1 hour'
    AND is_active = true
    ORDER BY last_login DESC;
  "

# Check for unauthorized data access
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, action, resource_type, COUNT(*)
    FROM audit_logs
    WHERE action IN ('read', 'download', 'export')
    AND created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id, action, resource_type
    ORDER BY COUNT(*) DESC
    LIMIT 20;
  "

# Check for data exfiltration
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, SUM(bytes_transferred) as total_bytes
    FROM api_requests
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY user_id
    HAVING SUM(bytes_transferred) > 100000000
    ORDER BY total_bytes DESC;
  "
```

### Immediate Response (0-15 minutes)

**Step 1: Contain the Incident**
```bash
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
```

**Step 2: Preserve Evidence**
```bash
# 1. Capture logs immediately (before rotation)
mkdir -p /incident-evidence/$(date +%Y%m%d_%H%M%S)
cd /incident-evidence/$(date +%Y%m%d_%H%M%S)

# API logs
kubectl logs -n ios-production deployment/ios-api --all-containers > api-logs.txt

# Database logs
kubectl logs -n ios-production statefulset/postgresql > db-logs.txt

# WAF logs
kubectl logs -n ios-production deployment/modsecurity > waf-logs.txt

# Audit logs
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    COPY (SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours')
    TO STDOUT CSV HEADER
  " > audit-logs.csv

# 2. Capture current state
kubectl get all -n ios-production -o yaml > kubernetes-state.yaml
kubectl describe pods -n ios-production > pod-details.txt
kubectl top pods -n ios-production > resource-usage.txt

# 3. Network capture (if still active)
kubectl exec -n ios-production deployment/ios-api -- \
  tcpdump -i eth0 -w /tmp/capture.pcap -c 10000 &

# 4. Memory dump (if malware suspected)
kubectl exec -n ios-production deployment/ios-api -- \
  cat /proc/kcore > /tmp/memory.dump

# 5. Create tarball
tar czf incident-evidence-$(date +%Y%m%d_%H%M%S).tar.gz .
```

**Step 3: Notify Stakeholders**
```bash
# Send incident notification
cat <<EOF | mail -s "SECURITY INCIDENT - $(date)" security@ios-system.com
SECURITY INCIDENT DETECTED

Time: $(date)
Severity: CRITICAL
Type: [Unauthorized Access / Data Breach / DDoS / etc]

Summary:
[Brief description of what was detected]

Actions Taken:
- Attacker IP(s) blocked
- Compromised accounts disabled
- Evidence preserved
- Investigation ongoing

Incident Commander: [Name]
War Room: https://meet.google.com/xxx-xxxx-xxx

Updates will be provided every 30 minutes.
EOF

# Post to Slack
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "🚨 SECURITY INCIDENT - CRITICAL",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*SECURITY INCIDENT DETECTED*\n\nType: Unauthorized Access\nStatus: Contained\nInvestigation: Ongoing\n\nWar Room: https://meet.google.com/xxx-xxxx-xxx"
        }
      }
    ]
  }'

# Page on-call
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "'$PAGERDUTY_KEY'",
    "event_action": "trigger",
    "payload": {
      "summary": "CRITICAL: Security Incident Detected",
      "severity": "critical",
      "source": "ios-system-production"
    }
  }'
```

### Investigation Phase (15-60 minutes)

**Step 1: Root Cause Analysis**
```bash
# Timeline reconstruction
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      created_at,
      user_id,
      action,
      resource_type,
      ip_address,
      user_agent
    FROM audit_logs
    WHERE created_at > NOW() - INTERVAL '6 hours'
    ORDER BY created_at
  " > timeline.csv

# Analyze access patterns
python3 <<EOF
import pandas as pd
df = pd.read_csv('timeline.csv')

# Group by IP and count actions
ip_analysis = df.groupby('ip_address').agg({
    'action': 'count',
    'user_id': 'nunique'
}).sort_values('action', ascending=False)

print("Top IPs by activity:")
print(ip_analysis.head(20))

# Unusual patterns
unusual = df[
    (df['action'].isin(['admin_access', 'export_data'])) &
    (df['created_at'] > pd.Timestamp.now() - pd.Timedelta(hours=6))
]
print("\nUnusual administrative actions:")
print(unusual)
EOF

# Check for privilege escalation
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      u.id,
      u.email,
      u.is_admin,
      u.updated_at,
      al.action,
      al.created_at
    FROM users u
    JOIN audit_logs al ON al.user_id = u.id
    WHERE u.is_admin = true
    AND u.updated_at > NOW() - INTERVAL '6 hours'
    AND al.action = 'update_user_permissions'
    ORDER BY u.updated_at DESC;
  "
```

**Step 2: Identify Affected Data**
```bash
# What data was accessed by attacker?
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT DISTINCT
      resource_type,
      resource_id,
      action,
      created_at
    FROM audit_logs
    WHERE user_id IN (SELECT id FROM compromised_users)
    OR ip_address IN ('1.2.3.4', '5.6.7.8')
    ORDER BY created_at;
  " > accessed-data.csv

# Export affected user data for GDPR breach notification
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      u.id,
      u.email,
      u.full_name,
      COUNT(DISTINCT d.id) as documents_accessed
    FROM users u
    LEFT JOIN documents d ON d.id IN (
      SELECT resource_id::int FROM audit_logs
      WHERE action = 'read'
      AND user_id IN (SELECT id FROM compromised_users)
      AND resource_type = 'document'
    )
    WHERE u.id IN (SELECT user_id FROM documents WHERE ...)
    GROUP BY u.id
  " > affected-users.csv
```

### Remediation Phase (1-4 hours)

**Step 1: Patch Vulnerability**
```bash
# If vulnerability identified, apply patch immediately

# 1. Emergency patch
git checkout -b security-patch-$(date +%Y%m%d)
# Apply fix
git commit -m "SECURITY: Fix [vulnerability description]"
git push

# 2. Build new image
docker build -t ios-system/api:security-patch-$(date +%Y%m%d) .
docker push ios-system/api:security-patch-$(date +%Y%m%d)

# 3. Deploy immediately
kubectl set image deployment/ios-api -n ios-production \
  api=ios-system/api:security-patch-$(date +%Y%m%d)

# 4. Verify patch
./scripts/security/verify-patch.sh
```

**Step 2: Rotate All Credentials**
```bash
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
```

**Step 3: Enhanced Monitoring**
```bash
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
```

### Post-Incident (4+ hours)

**Step 1: User Notification (GDPR)**
```bash
# If personal data breached, notify within 72 hours

# Prepare notification email
cat <<EOF > breach-notification.html
Subject: Important Security Notice

Dear [User],

We are writing to inform you of a security incident that may have affected your account.

What Happened:
On [Date], we detected unauthorized access to our systems. We immediately 
took action to secure our systems and investigate the incident.

What Information Was Involved:
- Email addresses
- [Other data types]

What We Are Doing:
- We have secured the vulnerability
- We have enhanced our security measures
- We are offering [credit monitoring/other services]
- We have notified appropriate authorities

What You Should Do:
1. Change your password immediately
2. Enable two-factor authentication
3. Monitor your account for suspicious activity
4. Be cautious of phishing emails

We sincerely apologize for this incident and are committed to protecting 
your data.

For more information: https://ios-system.com/security-incident
Support: security@ios-system.com

[Company Name]
EOF

# Send to affected users
python scripts/notifications/send_breach_notification.py \
  --template breach-notification.html \
  --recipients affected-users.csv
```

**Step 2: Regulatory Notification**
```bash
# GDPR - notify supervisory authority within 72 hours
# Prepare breach notification form

cat <<EOF > gdpr-breach-notification.txt
Data Breach Notification to Supervisory Authority

Date of Breach: 2025-01-15
Date of Discovery: 2025-01-15
Date of Notification: 2025-01-15

Data Controller: IOS System GmbH
Contact: dpo@ios-system.com

Nature of Breach:
[Description]

Categories of Data:
- Personal data (email, name)
- [Other categories]

Number of Affected Individuals: ~1,500

Likely Consequences:
[Assessment]

Measures Taken:
- Immediate containment
- Vulnerability patched
- Credentials rotated
- Enhanced monitoring

Measures for Individuals:
- Password reset required
- 2FA enforcement
- Account monitoring
EOF

# Submit to supervisory authority
# (Manual process - varies by jurisdiction)
```

**Step 3: Post-Mortem**
```markdown
# Security Incident Post-Mortem

**Date:** 2025-01-15
**Duration:** 6 hours 23 minutes
**Severity:** Critical

## Executive Summary
[Brief overview of incident]

## Timeline
- 14:00 UTC - Suspicious activity detected
- 14:15 UTC - Incident confirmed
- 14:20 UTC - Attacker IPs blocked
- 14:30 UTC - Evidence preserved
- 15:00 UTC - Root cause identified
- 16:00 UTC - Patch deployed
- 18:00 UTC - Credentials rotated
- 20:23 UTC - Incident closed

## Root Cause
[Detailed technical explanation]

## Impact Assessment
- **Users Affected:** 1,523
- **Data Compromised:** Email addresses, usernames
- **Financial Impact:** €25,000 (estimated)
- **Downtime:** 0 minutes (no service interruption)

## What Went Well
- Quick detection (15 minutes)
- Effective containment
- Evidence properly preserved
- Good team coordination

## What Could Be Improved
- Earlier vulnerability detection
- Faster patch deployment
- Better automated response

## Action Items
1. **Immediate (0-7 days):**
   - [ ] Deploy additional security measures
   - [ ] Complete user notifications
   - [ ] Enhance monitoring
   
2. **Short-term (1-4 weeks):**
   - [ ] Security audit by third party
   - [ ] Penetration testing
   - [ ] Security training for team
   
3. **Long-term (1-6 months):**
   - [ ] Implement bug bounty program
   - [ ] SOC 2 certification
   - [ ] Zero-trust architecture

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]
3. [Lesson 3]

## Sign-off
- Security Lead: ________________
- Engineering Lead: ________________
- CTO: ________________
- Legal: ________________
```

### Prevention
- [ ] Regular security audits
- [ ] Penetration testing (quarterly)
- [ ] Security training (monthly)
- [ ] Bug bounty program
- [ ] WAF rules updated regularly
- [ ] Intrusion detection system
- [ ] Security incident drills

### Escalation
- **Incident suspected:** Immediate alert to Security team
- **Incident confirmed:** CTO, Legal, PR
- **Data breach:** CEO, Board, Authorities (72 hours)
- **Major breach:** Law enforcement

---

## 📋 RUNBOOKS SUMMARY

**10 Operational Runbooks Created:**
1. ✅ API Down
2. ✅ High Error Rate
3. ✅ Database Issues
4. ✅ Performance Degradation
5. ✅ Cache Problems
6. ✅ Deployment Rollback
7. ✅ Database Backup & Restore
8. ✅ Certificate Renewal
9. ✅ Scaling Operations
10. ✅ Security Incident

**Each runbook includes:**
- Symptoms identification
- Impact assessment
- Investigation procedures
- Resolution steps
- Prevention measures
- Escalation paths

---

**Продолжение следует...**

Все 10 runbooks созданы! Следующий файл:
- Team Onboarding Guide

**Готовы создать onboarding guide?**