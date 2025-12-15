# scripts/security_scan.py

"""
Security scanning script
"""

import subprocess
import sys
import json

def run_command(cmd, description):
    """Run shell command and return output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run security scans"""
    
    print("\n" + "="*60)
    print("SECURITY SCAN - IOS SEARCH SYSTEM")
    print("="*60)
    
    all_passed = True
    
    # 1. Safety check (Python dependencies)
    print("\n[1/5] Checking Python dependencies for known vulnerabilities...")
    if not run_command(
        "safety check --json",
        "Safety - Dependency Vulnerability Check"
    ):
        all_passed = False
        print("⚠️  Found vulnerabilities in dependencies")
    else:
        print("✓ No known vulnerabilities")
    
    # 2. Bandit (Python code security)
    print("\n[2/5] Scanning Python code for security issues...")
    if not run_command(
        "bandit -r . -f json -o bandit-report.json",
        "Bandit - Python Security Scanner"
    ):
        all_passed = False
        print("⚠️  Found security issues in code")
    else:
        print("✓ No security issues found")
    
    # 3. Django security check
    print("\n[3/5] Running Django security checks...")
    if not run_command(
        "python manage.py check --deploy --fail-level WARNING",
        "Django Security Check"
    ):
        all_passed = False
        print("⚠️  Django security warnings found")
    else:
        print("✓ Django security checks passed")
    
    # 4. Secret scanning
    print("\n[4/5] Scanning for exposed secrets...")
    if not run_command(
        "detect-secrets scan --all-files --baseline .secrets.baseline",
        "Secret Detection"
    ):
        all_passed = False
        print("⚠️  Potential secrets found")
    else:
        print("✓ No secrets detected")
    
    # 5. OWASP Dependency Check
    print("\n[5/5] Running OWASP dependency check...")
    if not run_command(
        "pip list --format=json | python scripts/check_owasp.py",
        "OWASP Dependency Check"
    ):
        print("⚠️  OWASP check incomplete (optional)")
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL SECURITY CHECKS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("✗ SOME SECURITY CHECKS FAILED")
        print("="*60 + "\n")
        print("Please review the issues above and fix them before deployment.")
        sys.exit(1)

if __name__ == '__main__':
    main()