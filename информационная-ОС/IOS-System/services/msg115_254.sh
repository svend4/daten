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