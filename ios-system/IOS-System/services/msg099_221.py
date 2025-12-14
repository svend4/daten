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