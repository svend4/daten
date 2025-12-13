#!/bin/bash
# Security Hardening Automation Script
# Applies security best practices to IOS System

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

# ============================================
# System Hardening
# ============================================

harden_os() {
    log "Hardening operating system..."
    
    # Disable unused services
    systemctl disable bluetooth.service || warning "Bluetooth already disabled"
    systemctl disable cups.service || warning "CUPS already disabled"
    
    # Set secure file permissions
    chmod 644 /etc/passwd
    chmod 600 /etc/shadow
    chmod 644 /etc/group
    chmod 600 /etc/gshadow
    
    # Configure firewall
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp  # SSH
    ufw allow 80/tcp  # HTTP
    ufw allow 443/tcp # HTTPS
    ufw --force enable
    
    # Disable root login
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl restart sshd
    
    # Configure automatic security updates
    apt-get install -y unattended-upgrades
    dpkg-reconfigure -plow unattended-upgrades
    
    log "OS hardening completed"
}

# ============================================
# Docker Security
# ============================================

harden_docker() {
    log "Hardening Docker configuration..."
    
    # Enable user namespaces
    echo '{"userns-remap": "default"}' > /etc/docker/daemon.json
    
    # Set resource limits
    cat >> /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
EOF
    
    systemctl restart docker
    
    log "Docker hardening completed"
}

# ============================================
# Application Security
# ============================================

harden_application() {
    log "Hardening application configuration..."
    
    # Generate strong secret key
    SECRET_KEY=$(openssl rand -base64 32)
    
    # Update environment variables
    cat > /etc/ios-system/security.env <<EOF
SECRET_KEY=${SECRET_KEY}
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
CSRF_COOKIE_SECURE=true
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
X_FRAME_OPTIONS=DENY
EOF
    
    chmod 600 /etc/ios-system/security.env
    
    log "Application hardening completed"
}

# ============================================
# Database Security
# ============================================

harden_database() {
    log "Hardening database configuration..."
    
    # Configure PostgreSQL
    cat >> /etc/postgresql/*/main/postgresql.conf <<EOF
# Security Settings
ssl = on
password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
EOF
    
    # Restrict network access
    cat > /etc/postgresql/*/main/pg_hba.conf <<EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
hostssl all             all             0.0.0.0/0               scram-sha-256
EOF
    
    systemctl restart postgresql
    
    log "Database hardening completed"
}

# ============================================
# Redis Security
# ============================================

harden_redis() {
    log "Hardening Redis configuration..."
    
    # Set password
    REDIS_PASSWORD=$(openssl rand -base64 32)
    
    cat >> /etc/redis/redis.conf <<EOF
# Security Settings
requirepass ${REDIS_PASSWORD}
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
bind 127.0.0.1
protected-mode yes
EOF
    
    # Save password
    echo "REDIS_PASSWORD=${REDIS_PASSWORD}" >> /etc/ios-system/security.env
    
    systemctl restart redis
    
    log "Redis hardening completed"
}

# ============================================
# Nginx Security
# ============================================

harden_nginx() {
    log "Hardening Nginx configuration..."
    
    cat > /etc/nginx/conf.d/security.conf <<EOF
# Security Headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Hide version
server_tokens off;

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_status 429;

# SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
EOF
    
    nginx -t && systemctl reload nginx
    
    log "Nginx hardening completed"
}

# ============================================
# Audit Configuration
# ============================================

configure_auditing() {
    log "Configuring audit logging..."
    
    # Install auditd
    apt-get install -y auditd audispd-plugins
    
    # Configure audit rules
    cat > /etc/audit/rules.d/ios-system.rules <<EOF
# Monitor authentication
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/sudoers -p wa -k sudoers_changes

# Monitor system calls
-a always,exit -F arch=b64 -S execve -k exec_commands

# Monitor file access
-w /var/www/ -p wa -k webroot_changes
-w /etc/nginx/ -p wa -k nginx_config
-w /etc/postgresql/ -p wa -k postgres_config

# Monitor network
-a always,exit -F arch=b64 -S socket -S connect -k network_activity
EOF
    
    systemctl restart auditd
    
    log "Audit configuration completed"
}

# ============================================
# Security Scanning
# ============================================

run_security_scans() {
    log "Running security scans..."
    
    # Run Lynis security audit
    if command -v lynis &> /dev/null; then
        lynis audit system --quick
    else
        warning "Lynis not installed, skipping system audit"
    fi
    
    # Scan for rootkits
    if command -v rkhunter &> /dev/null; then
        rkhunter --check --skip-keypress
    else
        warning "rkhunter not installed, skipping rootkit scan"
    fi
    
    # Check for vulnerabilities
    if command -v trivy &> /dev/null; then
        trivy image ios-system/api:latest
    else
        warning "Trivy not installed, skipping container scan"
    fi
    
    log "Security scans completed"
}

# ============================================
# Main Execution
# ============================================

main() {
    log "Starting security hardening..."
    log "=========================================="
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
    
    # Create security config directory
    mkdir -p /etc/ios-system
    
    # Run hardening procedures
    harden_os
    harden_docker
    harden_application
    harden_database
    harden_redis
    harden_nginx
    configure_auditing
    
    # Run security scans
    run_security_scans
    
    log "=========================================="
    log "Security hardening completed successfully!"
    log ""
    log "IMPORTANT: Review the following files:"
    log "  - /etc/ios-system/security.env (contains secrets)"
    log "  - /var/log/audit/audit.log (audit logs)"
    log ""
    log "Next steps:"
    log "  1. Backup security.env to secure location"
    log "  2. Restart all services"
    log "  3. Test application functionality"
    log "  4. Schedule regular security scans"
}

main "$@"