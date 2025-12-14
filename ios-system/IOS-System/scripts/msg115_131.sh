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