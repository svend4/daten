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