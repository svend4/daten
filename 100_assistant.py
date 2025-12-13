Пользователь готов продолжить с Week 27-28: Security Hardening & Penetration Testing. Это будет фокусироваться на:

1. Penetration Testing - автоматизированное и ручное тестирование безопасности
2. WAF Implementation - Web Application Firewall
3. Secrets Management - HashiCorp Vault
4. Security Compliance - GDPR, HIPAA, SOC 2

Начну с Day 141-142: Penetration Testing & Vulnerability Assessment# 🔒 WEEK 27-28: SECURITY HARDENING & PENETRATION TESTING

## 📋 ЦЕЛЬ

Усиление безопасности IOS System до enterprise-уровня:
- **Penetration Testing** - тестирование на проникновение
- **Vulnerability Scanning** - сканирование уязвимостей
- **WAF Implementation** - Web Application Firewall
- **Secrets Management** - управление секретами (Vault)
- **Security Compliance** - соответствие стандартам
- **Zero-Trust Architecture** - архитектура нулевого доверия

---

## DAY 141-142: PENETRATION TESTING & VULNERABILITY ASSESSMENT

---

## ФАЙЛ 1: `security/pentest/automated_security_scan.py`

```python
#!/usr/bin/env python3
"""
Automated Security Scanning Suite
Runs multiple security tools and aggregates results

Tools integrated:
- OWASP ZAP (web vulnerability scanner)
- Bandit (Python security linter)
- Safety (dependency vulnerability checker)
- Trivy (container security scanner)
- SQLMap (SQL injection detector)
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityScanner:
    """
    Orchestrates security scanning tools
    """
    
    def __init__(self, target_url: str, output_dir: str = "./security_reports"):
        self.target_url = target_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_all_scans(self) -> Dict:
        """Run all security scans"""
        logger.info("Starting comprehensive security scan...")
        
        # Static analysis
        self.results['bandit'] = self.run_bandit()
        self.results['safety'] = self.run_safety()
        
        # Container security
        self.results['trivy'] = self.run_trivy()
        
        # Web vulnerability scanning
        self.results['zap'] = self.run_zap_scan()
        
        # SQL injection testing
        self.results['sqlmap'] = self.run_sqlmap()
        
        # Generate summary report
        self.generate_summary_report()
        
        logger.info(f"Security scan completed. Report: {self.output_dir}/summary_{self.timestamp}.json")
        
        return self.results
    
    def run_bandit(self) -> Dict:
        """
        Run Bandit - Python security linter
        
        Finds common security issues in Python code
        """
        logger.info("Running Bandit security linter...")
        
        output_file = self.output_dir / f"bandit_{self.timestamp}.json"
        
        try:
            result = subprocess.run(
                [
                    'bandit',
                    '-r', 'ios_core',
                    '-f', 'json',
                    '-o', str(output_file),
                    '--severity-level', 'medium'
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Load results
            with open(output_file) as f:
                data = json.load(f)
            
            issues = data.get('results', [])
            
            return {
                'status': 'completed',
                'issues_found': len(issues),
                'high_severity': len([i for i in issues if i.get('issue_severity') == 'HIGH']),
                'medium_severity': len([i for i in issues if i.get('issue_severity') == 'MEDIUM']),
                'report': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_safety(self) -> Dict:
        """
        Run Safety - checks dependencies for known vulnerabilities
        """
        logger.info("Running Safety vulnerability checker...")
        
        output_file = self.output_dir / f"safety_{self.timestamp}.json"
        
        try:
            result = subprocess.run(
                ['safety', 'check', '--json', '--output', str(output_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            with open(output_file) as f:
                data = json.load(f)
            
            vulnerabilities = data if isinstance(data, list) else []
            
            return {
                'status': 'completed',
                'vulnerabilities_found': len(vulnerabilities),
                'report': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_trivy(self) -> Dict:
        """
        Run Trivy - container security scanner
        """
        logger.info("Running Trivy container scanner...")
        
        output_file = self.output_dir / f"trivy_{self.timestamp}.json"
        
        try:
            result = subprocess.run(
                [
                    'trivy',
                    'image',
                    '--format', 'json',
                    '--output', str(output_file),
                    '--severity', 'HIGH,CRITICAL',
                    'ios-system/api:latest'
                ],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            with open(output_file) as f:
                data = json.load(f)
            
            # Count vulnerabilities
            vulnerabilities = []
            for result in data.get('Results', []):
                vulnerabilities.extend(result.get('Vulnerabilities', []))
            
            critical = len([v for v in vulnerabilities if v.get('Severity') == 'CRITICAL'])
            high = len([v for v in vulnerabilities if v.get('Severity') == 'HIGH'])
            
            return {
                'status': 'completed',
                'vulnerabilities_found': len(vulnerabilities),
                'critical': critical,
                'high': high,
                'report': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Trivy scan failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_zap_scan(self) -> Dict:
        """
        Run OWASP ZAP - web vulnerability scanner
        
        Performs active scanning for web vulnerabilities
        """
        logger.info("Running OWASP ZAP scan...")
        
        output_file = self.output_dir / f"zap_{self.timestamp}.json"
        
        try:
            # Start ZAP in daemon mode and run baseline scan
            result = subprocess.run(
                [
                    'docker', 'run',
                    '--rm',
                    '-v', f"{self.output_dir}:/zap/wrk:rw",
                    'owasp/zap2docker-stable',
                    'zap-baseline.py',
                    '-t', self.target_url,
                    '-J', f"zap_{self.timestamp}.json",
                    '-r', f"zap_{self.timestamp}.html"
                ],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            # Parse results
            with open(output_file) as f:
                data = json.load(f)
            
            alerts = data.get('site', [{}])[0].get('alerts', [])
            
            high = len([a for a in alerts if a.get('riskcode') == '3'])
            medium = len([a for a in alerts if a.get('riskcode') == '2'])
            low = len([a for a in alerts if a.get('riskcode') == '1'])
            
            return {
                'status': 'completed',
                'alerts_found': len(alerts),
                'high': high,
                'medium': medium,
                'low': low,
                'report': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"ZAP scan failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_sqlmap(self) -> Dict:
        """
        Run SQLMap - SQL injection vulnerability scanner
        
        Tests common endpoints for SQL injection
        """
        logger.info("Running SQLMap SQL injection tests...")
        
        output_file = self.output_dir / f"sqlmap_{self.timestamp}.txt"
        
        # Test endpoints
        test_endpoints = [
            f"{self.target_url}/api/documents?id=1",
            f"{self.target_url}/api/users?email=test@example.com",
            f"{self.target_url}/api/search?q=test"
        ]
        
        findings = []
        
        try:
            for endpoint in test_endpoints:
                logger.info(f"Testing endpoint: {endpoint}")
                
                result = subprocess.run(
                    [
                        'sqlmap',
                        '-u', endpoint,
                        '--batch',
                        '--level=3',
                        '--risk=2',
                        '--technique=BEUSTQ'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Check if injection was found
                if 'sqlmap identified the following injection' in result.stdout:
                    findings.append({
                        'endpoint': endpoint,
                        'vulnerable': True,
                        'details': 'SQL injection found'
                    })
                else:
                    findings.append({
                        'endpoint': endpoint,
                        'vulnerable': False
                    })
            
            # Save results
            with open(output_file, 'w') as f:
                json.dump(findings, f, indent=2)
            
            vulnerable_count = len([f for f in findings if f.get('vulnerable')])
            
            return {
                'status': 'completed',
                'endpoints_tested': len(test_endpoints),
                'vulnerabilities_found': vulnerable_count,
                'report': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"SQLMap scan failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        
        summary = {
            'timestamp': self.timestamp,
            'target': self.target_url,
            'scans': self.results,
            'overall_status': self._calculate_overall_status(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save summary
        summary_file = self.output_dir / f"summary_{self.timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate human-readable report
        self._generate_html_report(summary)
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall security status"""
        
        # Count critical/high severity issues
        critical_count = 0
        high_count = 0
        
        # Bandit
        if 'bandit' in self.results:
            high_count += self.results['bandit'].get('high_severity', 0)
        
        # Trivy
        if 'trivy' in self.results:
            critical_count += self.results['trivy'].get('critical', 0)
            high_count += self.results['trivy'].get('high', 0)
        
        # ZAP
        if 'zap' in self.results:
            high_count += self.results['zap'].get('high', 0)
        
        # SQLMap
        if 'sqlmap' in self.results:
            critical_count += self.results['sqlmap'].get('vulnerabilities_found', 0)
        
        if critical_count > 0:
            return 'CRITICAL'
        elif high_count > 5:
            return 'HIGH'
        elif high_count > 0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings"""
        
        recommendations = []
        
        # Check Bandit results
        if 'bandit' in self.results:
            if self.results['bandit'].get('high_severity', 0) > 0:
                recommendations.append(
                    "Fix high-severity Python security issues identified by Bandit"
                )
        
        # Check Safety results
        if 'safety' in self.results:
            if self.results['safety'].get('vulnerabilities_found', 0) > 0:
                recommendations.append(
                    "Update vulnerable dependencies to latest secure versions"
                )
        
        # Check Trivy results
        if 'trivy' in self.results:
            if self.results['trivy'].get('critical', 0) > 0:
                recommendations.append(
                    "Update container base image to fix critical vulnerabilities"
                )
        
        # Check ZAP results
        if 'zap' in self.results:
            if self.results['zap'].get('high', 0) > 0:
                recommendations.append(
                    "Address web application vulnerabilities identified by ZAP"
                )
        
        # Check SQLMap results
        if 'sqlmap' in self.results:
            if self.results['sqlmap'].get('vulnerabilities_found', 0) > 0:
                recommendations.append(
                    "CRITICAL: Fix SQL injection vulnerabilities immediately"
                )
        
        if not recommendations:
            recommendations.append("No critical issues found. Continue regular security audits.")
        
        return recommendations
    
    def _generate_html_report(self, summary: Dict):
        """Generate HTML summary report"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .status-critical {{ color: red; font-weight: bold; }}
        .status-high {{ color: orange; font-weight: bold; }}
        .status-medium {{ color: yellow; font-weight: bold; }}
        .status-low {{ color: green; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <h1>Security Scan Report</h1>
    <p><strong>Timestamp:</strong> {self.timestamp}</p>
    <p><strong>Target:</strong> {self.target_url}</p>
    <p><strong>Overall Status:</strong> <span class="status-{summary['overall_status'].lower()}">{summary['overall_status']}</span></p>
    
    <h2>Scan Results</h2>
    <table>
        <tr>
            <th>Tool</th>
            <th>Status</th>
            <th>Issues Found</th>
            <th>Details</th>
        </tr>
"""
        
        for tool, result in summary['scans'].items():
            status = result.get('status', 'unknown')
            
            if tool == 'bandit':
                issues = result.get('issues_found', 0)
                details = f"High: {result.get('high_severity', 0)}, Medium: {result.get('medium_severity', 0)}"
            elif tool == 'safety':
                issues = result.get('vulnerabilities_found', 0)
                details = f"{issues} vulnerable dependencies"
            elif tool == 'trivy':
                issues = result.get('vulnerabilities_found', 0)
                details = f"Critical: {result.get('critical', 0)}, High: {result.get('high', 0)}"
            elif tool == 'zap':
                issues = result.get('alerts_found', 0)
                details = f"High: {result.get('high', 0)}, Medium: {result.get('medium', 0)}"
            elif tool == 'sqlmap':
                issues = result.get('vulnerabilities_found', 0)
                details = f"{issues} SQL injection vulnerabilities"
            else:
                issues = 0
                details = "N/A"
            
            html += f"""
        <tr>
            <td>{tool.upper()}</td>
            <td>{status}</td>
            <td>{issues}</td>
            <td>{details}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Recommendations</h2>
"""
        
        for rec in summary['recommendations']:
            html += f'    <div class="recommendation">{rec}</div>\n'
        
        html += """
</body>
</html>
"""
        
        # Save HTML report
        html_file = self.output_dir / f"report_{self.timestamp}.html"
        with open(html_file, 'w') as f:
            f.write(html)
        
        logger.info(f"HTML report generated: {html_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated security scanning suite"
    )
    parser.add_argument(
        '--target',
        default='http://localhost:8000',
        help='Target URL to scan'
    )
    parser.add_argument(
        '--output',
        default='./security_reports',
        help='Output directory for reports'
    )
    
    args = parser.parse_args()
    
    scanner = SecurityScanner(
        target_url=args.target,
        output_dir=args.output
    )
    
    results = scanner.run_all_scans()
    
    print("\n" + "=" * 80)
    print("SECURITY SCAN COMPLETED")
    print("=" * 80)
    print(f"\nOverall Status: {results}")
    print(f"\nReports saved to: {args.output}")


if __name__ == "__main__":
    main()
```

---

## ФАЙЛ 2: `security/pentest/manual_pentest_checklist.md`

```markdown
# Manual Penetration Testing Checklist

## 🎯 Overview

This checklist covers manual penetration testing procedures for IOS System.

**Tester:** [Name]  
**Date:** [Date]  
**Version:** [App Version]  
**Environment:** [Staging/Production]

---

## 🔐 AUTHENTICATION & SESSION MANAGEMENT

### Login Security

- [ ] **Brute Force Protection**
  - Attempt 10+ failed logins
  - Verify account lockout after X attempts
  - Check for CAPTCHA after N failures
  - Test: `for i in {1..20}; do curl -X POST /api/auth/login -d '{"username":"admin","password":"wrong"}'; done`

- [ ] **Password Policy**
  - Try weak passwords (123456, password, etc.)
  - Verify minimum length (8+ characters)
  - Check complexity requirements
  - Test password history (can't reuse last 5)

- [ ] **MFA Bypass**
  - Try accessing protected resources without MFA
  - Test MFA code expiration (should expire after 5 min)
  - Attempt MFA code reuse
  - Test backup codes

- [ ] **Session Security**
  - Check session token randomness (entropy)
  - Verify HttpOnly flag on cookies
  - Verify Secure flag on cookies (HTTPS only)
  - Check SameSite attribute
  - Test session fixation vulnerability
  - Test concurrent session limits

- [ ] **Logout**
  - Verify session invalidation on logout
  - Check token revocation
  - Test "logout everywhere" functionality

### OAuth Security

- [ ] **OAuth Flow**
  - Verify state parameter validation (CSRF protection)
  - Check redirect_uri whitelist
  - Test authorization code reuse (should fail)
  - Verify PKCE implementation

- [ ] **Token Security**
  - Check access token expiration (15 min)
  - Check refresh token expiration (30 days)
  - Verify token rotation on refresh
  - Test token revocation

---

## 🛡️ AUTHORIZATION & ACCESS CONTROL

### RBAC Testing

- [ ] **Horizontal Privilege Escalation**
  - User A tries to access User B's documents
  - Test: `curl /api/documents/USER_B_DOC_ID -H "Authorization: Bearer USER_A_TOKEN"`
  - Expected: 403 Forbidden

- [ ] **Vertical Privilege Escalation**
  - Regular user tries admin endpoints
  - Test: `curl /api/admin/users -H "Authorization: Bearer USER_TOKEN"`
  - Expected: 403 Forbidden

- [ ] **Direct Object Reference**
  - Test sequential ID enumeration
  - Try accessing documents by guessing IDs
  - Verify UUID/random ID usage

- [ ] **API Endpoint Protection**
  - List all endpoints: `curl /api/docs`
  - Verify authentication required
  - Check role-based access

### Permission Testing

- [ ] **Document Permissions**
  - Create document as User A
  - Try to edit as User B (should fail)
  - Try to delete as User B (should fail)
  - Test sharing permissions

- [ ] **Domain Permissions**
  - Try creating domain without permission
  - Try modifying domain hierarchy
  - Test cascade permissions

---

## 💉 INJECTION ATTACKS

### SQL Injection

- [ ] **Authentication Bypass**
  - Username: `admin' OR '1'='1`
  - Password: `' OR '1'='1`
  - Expected: Login fails

- [ ] **Search Injection**
  - Query: `'; DROP TABLE documents; --`
  - Query: `' UNION SELECT * FROM users --`
  - Expected: Query sanitized, no execution

- [ ] **Blind SQL Injection**
  - Query: `test' AND 1=1 --` (should return results)
  - Query: `test' AND 1=2 --` (should return no results)
  - If different results → vulnerable

### NoSQL Injection

- [ ] **MongoDB Injection**
  - Test: `{"username": {"$ne": null}, "password": {"$ne": null}}`
  - Test: `{"username": {"$gt": ""}, "password": {"$gt": ""}}`

### Command Injection

- [ ] **OS Command Injection**
  - Test file upload with: `; ls -la`
  - Test export filename: `report.pdf; cat /etc/passwd`
  - Test webhook URL: `http://evil.com; curl evil.com`

### LDAP Injection

- [ ] **LDAP Query Injection** (if LDAP used)
  - Username: `*)(uid=*))(|(uid=*`
  - Test: `admin*` (wildcard)

---

## 🔓 AUTHENTICATION VULNERABILITIES

### Password Reset

- [ ] **Reset Token Security**
  - Check token randomness (should be UUID)
  - Test token expiration (should expire in 15 min)
  - Try reusing token (should fail)
  - Test token enumeration

- [ ] **Account Enumeration**
  - Reset with valid email: "Reset link sent"
  - Reset with invalid email: Should show same message
  - Verify timing is consistent

### Account Recovery

- [ ] **Security Questions**
  - If used, test weak questions
  - Check for brute force protection
  - Verify lockout mechanism

---

## 🌐 WEB VULNERABILITIES

### Cross-Site Scripting (XSS)

- [ ] **Reflected XSS**
  - Search: `<script>alert('XSS')</script>`
  - URL param: `?name=<img src=x onerror=alert(1)>`
  - Expected: Input sanitized

- [ ] **Stored XSS**
  - Document content: `<script>alert(document.cookie)</script>`
  - Comment: `<svg onload=alert(1)>`
  - Username: `<img src=x onerror=alert(1)>`

- [ ] **DOM-based XSS**
  - Check client-side JavaScript
  - Test: `#<script>alert(1)</script>`

### Cross-Site Request Forgery (CSRF)

- [ ] **CSRF Token Validation**
  - Remove CSRF token from request
  - Use token from another session
  - Change request method (POST → GET)

- [ ] **State-Changing Operations**
  - Test password change without token
  - Test document delete without token
  - Test profile update without token

### Clickjacking

- [ ] **X-Frame-Options Header**
  - Check header: `X-Frame-Options: DENY`
  - Try embedding in iframe
  - Test `Content-Security-Policy: frame-ancestors 'none'`

### Security Headers

- [ ] **HTTP Security Headers**
  ```bash
  curl -I https://api.ios-system.com
  ```
  - [ ] `Strict-Transport-Security: max-age=31536000`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Content-Security-Policy: ...`
  - [ ] `Referrer-Policy: no-referrer-when-downgrade`
  - [ ] `Permissions-Policy: ...`

---

## 📤 FILE UPLOAD VULNERABILITIES

### Malicious File Upload

- [ ] **File Type Validation**
  - Upload .php file (should be rejected)
  - Upload .exe file (should be rejected)
  - Upload double extension: `image.jpg.php`

- [ ] **File Content Validation**
  - Rename malicious file to .jpg
  - Check MIME type validation
  - Test polyglot files (valid image + code)

- [ ] **Path Traversal**
  - Filename: `../../../../etc/passwd`
  - Filename: `..\..\..\..\windows\system32\config\sam`

- [ ] **File Size Limits**
  - Upload 100MB file (should be rejected)
  - Test ZIP bomb
  - Test resource exhaustion

### File Download Vulnerabilities

- [ ] **Path Traversal**
  - Download: `/api/files/../../etc/passwd`
  - Download: `/api/files/..%2F..%2Fetc%2Fpasswd`

- [ ] **Access Control**
  - Try downloading other user's files
  - Test: `/api/files/USER_B_FILE_ID`

---

## 🔍 INFORMATION DISCLOSURE

### Error Messages

- [ ] **Verbose Errors**
  - Trigger 500 error
  - Check for stack traces
  - Look for database errors
  - Test: `curl /api/documents/INVALID_ID`

### Debug Information

- [ ] **Debug Endpoints**
  - Try: `/debug`, `/phpinfo`, `/info`
  - Check: `/.git`, `/.env`, `/config`
  - Test: `/.well-known/`

### API Information

- [ ] **API Documentation**
  - Check `/api/docs` accessibility
  - Verify authentication required
  - Test Swagger/OpenAPI exposure

### Server Information

- [ ] **Server Headers**
  ```bash
  curl -I https://api.ios-system.com | grep Server
  ```
  - Server version should be hidden
  - Check `X-Powered-By` (should not exist)

---

## 🚀 BUSINESS LOGIC VULNERABILITIES

### Rate Limiting

- [ ] **API Rate Limits**
  - Send 1000 requests in 1 minute
  - Check for `429 Too Many Requests`
  - Test different endpoints

- [ ] **Search Rate Limiting**
  - Perform 100 searches rapidly
  - Check for rate limit

### Input Validation

- [ ] **Integer Overflow**
  - Price: `999999999999999999999`
  - Quantity: `-1`
  - Limit: `9999999`

- [ ] **Business Rule Bypass**
  - Try negative prices
  - Test zero prices
  - Check minimum/maximum limits

---

## 🔐 CRYPTOGRAPHY

### Password Storage

- [ ] **Password Hashing**
  - Check database: passwords should be bcrypt/argon2
  - Verify salt is unique per password
  - Check work factor (bcrypt cost ≥ 12)

### Data Encryption

- [ ] **Sensitive Data**
  - Check database encryption (field-level)
  - Verify TLS/SSL for data in transit
  - Test encryption key management

### SSL/TLS

- [ ] **Certificate Validation**
  - Check certificate expiration
  - Verify certificate chain
  - Test: `openssl s_client -connect api.ios-system.com:443`

- [ ] **SSL Configuration**
  - Test: https://www.ssllabs.com/ssltest/
  - Target grade: A or A+
  - No weak ciphers (RC4, 3DES)

---

## 📝 REPORTING TEMPLATE

### Critical Vulnerability Report

**Title:** [Vulnerability Name]

**Severity:** Critical/High/Medium/Low

**CVSS Score:** [Calculate at https://www.first.org/cvss/calculator/3.1]

**Description:**
[Detailed description]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Proof of Concept:**
```
[Code/Screenshots]
```

**Impact:**
[What can an attacker do?]

**Affected Component:**
[API/Web/Database/etc.]

**Remediation:**
[How to fix]

**References:**
- [CWE-XXX](https://cwe.mitre.org/)
- [OWASP Link]

---

## ✅ SIGN-OFF

- [ ] All tests completed
- [ ] Results documented
- [ ] Report generated
- [ ] Development team notified
- [ ] Retesting scheduled

**Tester Signature:** _______________  
**Date:** _______________
```

---

## ФАЙЛ 3: `security/waf/modsecurity_rules.conf`

```apache
# ModSecurity WAF Rules for IOS System
# OWASP Core Rule Set + Custom Rules

# ============================================
# Basic Configuration
# ============================================

# Enable ModSecurity
SecRuleEngine On

# Request body access
SecRequestBodyAccess On
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072

# Response body access
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html text/xml application/json

# Audit logging
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/modsec_audit.log

# Debug log
SecDebugLog /var/log/modsec_debug.log
SecDebugLogLevel 0

# ============================================
# OWASP CRS Inclusion
# ============================================

Include /etc/modsecurity/owasp-crs/crs-setup.conf
Include /etc/modsecurity/owasp-crs/rules/*.conf

# ============================================
# Custom Rules for IOS System
# ============================================

# Rule 100001: Block SQL Injection in Query Params
SecRule ARGS "@detectSQLi" \
    "id:100001,\
    phase:2,\
    block,\
    log,\
    msg:'SQL Injection Detected',\
    logdata:'Matched Data: %{MATCHED_VAR}',\
    severity:'CRITICAL',\
    tag:'application-multi',\
    tag:'language-multi',\
    tag:'platform-multi',\
    tag:'attack-sqli'"

# Rule 100002: Block XSS in Request Body
SecRule REQUEST_BODY "@detectXSS" \
    "id:100002,\
    phase:2,\
    block,\
    log,\
    msg:'XSS Attack Detected in Request Body',\
    logdata:'Matched Data: %{MATCHED_VAR}',\
    severity:'CRITICAL',\
    tag:'application-multi',\
    tag:'language-multi',\
    tag:'attack-xss'"

# Rule 100003: Rate Limiting - Max 100 requests per minute
SecAction \
    "id:100003,\
    phase:1,\
    nolog,\
    pass,\
    initcol:ip=%{REMOTE_ADDR},\
    setvar:ip.requests_per_minute=+1,\
    expirevar:ip.requests_per_minute=60"

SecRule IP:REQUESTS_PER_MINUTE "@gt 100" \
    "id:100004,\
    phase:1,\
    block,\
    log,\
    msg:'Rate Limit Exceeded - More than 100 requests per minute',\
    logdata:'IP: %{REMOTE_ADDR}, Requests: %{IP.REQUESTS_PER_MINUTE}',\
    severity:'WARNING',\
    tag:'rate-limiting'"

# Rule 100005: Block Common Attack Patterns
SecRule REQUEST_URI|ARGS|REQUEST_BODY "@rx (\.\./|\.\.\\|/etc/passwd|cmd\.exe)" \
    "id:100005,\
    phase:2,\
    block,\
    log,\
    msg:'Path Traversal or Command Injection Attempt',\
    severity:'CRITICAL'"

# Rule 100006: Enforce Strong Content-Type
SecRule REQUEST_HEADERS:Content-Type "!@rx ^(application/json|application/x-www-form-urlencoded|multipart/form-data)" \
    "id:100006,\
    phase:1,\
    block,\
    log,\
    msg:'Invalid Content-Type',\
    chain"
    SecRule REQUEST_METHOD "@streq POST" \
        "t:none"

# Rule 100007: Block Suspicious User-Agents
SecRule REQUEST_HEADERS:User-Agent "@rx (sqlmap|nikto|nmap|masscan|acunetix)" \
    "id:100007,\
    phase:1,\
    block,\
    log,\
    msg:'Suspicious User-Agent Detected',\
    severity:'WARNING'"

# Rule 100008: Protect Authentication Endpoints
SecRule REQUEST_URI "@beginsWith /api/auth/" \
    "id:100008,\
    phase:1,\
    pass,\
    nolog,\
    chain"
    SecRule IP:AUTH_ATTEMPTS "@gt 5" \
        "block,\
        log,\
        msg:'Too many authentication attempts',\
        severity:'WARNING',\
        setvar:ip.auth_block=1,\
        expirevar:ip.auth_block=300"

SecAction \
    "id:100009,\
    phase:1,\
    pass,\
    nolog,\
    initcol:ip=%{REMOTE_ADDR},\
    setvar:ip.auth_attempts=+1,\
    expirevar:ip.auth_attempts=60"

# Rule 100010: Block if Previous Auth Block Active
SecRule IP:AUTH_BLOCK "@eq 1" \
    "id:100010,\
    phase:1,\
    block,\
    log,\
    msg:'Authentication blocked due to previous violations',\
    severity:'WARNING'"

# Rule 100011: Enforce HTTPS
SecRule REQUEST_SCHEME "!@streq https" \
    "id:100011,\
    phase:1,\
    redirect:https://%{HTTP_HOST}%{REQUEST_URI},\
    log,\
    msg:'HTTP Request Redirected to HTTPS'"

# Rule 100012: Block Large Payloads
SecRule REQUEST_BODY_LENGTH "@gt 10485760" \
    "id:100012,\
    phase:2,\
    block,\
    log,\
    msg:'Request Body Too Large (>10MB)',\
    severity:'WARNING'"

# Rule 100013: Validate JSON Content
SecRule REQUEST_HEADERS:Content-Type "@streq application/json" \
    "id:100013,\
    phase:2,\
    pass,\
    nolog,\
    chain"
    SecRule REQUEST_BODY "!@validateByteRange 0-255" \
        "block,\
        log,\
        msg:'Invalid JSON Characters',\
        severity:'WARNING'"

# Rule 100014: API Key Validation
SecRule REQUEST_HEADERS:Authorization "!@rx ^Bearer [A-Za-z0-9_-]{20,}$" \
    "id:100014,\
    phase:1,\
    block,\
    log,\
    msg:'Invalid or Missing Authorization Header',\
    severity:'WARNING',\
    chain"
    SecRule REQUEST_URI "!@beginsWith /api/auth/"

# Rule 100015: Protect Admin Endpoints
SecRule REQUEST_URI "@beginsWith /api/admin/" \
    "id:100015,\
    phase:1,\
    pass,\
    log,\
    msg:'Admin Endpoint Access',\
    severity:'INFO',\
    tag:'admin-access'"

# ============================================
# Response Headers Security
# ============================================

# Add security headers to all responses
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "no-referrer-when-downgrade"
Header always set Content-Security-Policy "default-src 'self'"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

# Remove server information
Header unset Server
Header unset X-Powered-By

# ============================================
# Anomaly Scoring
# ============================================

SecAction \
    "id:900000,\
    phase:1,\
    nolog,\
    pass,\
    t:none,\
    setvar:tx.anomaly_score_threshold=5"

# Block if anomaly score exceeds threshold
SecRule TX:ANOMALY_SCORE "@ge %{tx.anomaly_score_threshold}" \
    "id:900001,\
    phase:2,\
    block,\
    log,\
    msg:'Anomaly Score Exceeded',\
    logdata:'Anomaly Score: %{TX.ANOMALY_SCORE}'"

# ============================================
# IP Reputation
# ============================================

# Block known malicious IPs (integrate with threat intelligence)
SecRule REMOTE_ADDR "@ipMatchFromFile /etc/modsecurity/blacklist.txt" \
    "id:900100,\
    phase:1,\
    block,\
    log,\
    msg:'IP in Blacklist',\
    severity:'CRITICAL'"

# Whitelist trusted IPs
SecRule REMOTE_ADDR "@ipMatchFromFile /etc/modsecurity/whitelist.txt" \
    "id:900101,\
    phase:1,\
    pass,\
    nolog,\
    ctl:ruleEngine=Off"
```

---

**Продолжение следует...**

Создано:
- ✅ Automated security scanning suite (OWASP ZAP, Bandit, Safety, Trivy, SQLMap)
- ✅ Comprehensive manual penetration testing checklist
- ✅ ModSecurity WAF rules (OWASP CRS + custom)

**Следующие файлы:**
- HashiCorp Vault integration
- Secrets management
- Security compliance documentation
- Incident response procedures

**Готовы продолжить?**