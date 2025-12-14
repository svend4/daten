#!/bin/bash
# Setup enhanced security features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         SECURITY ENHANCEMENT SETUP                         ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}[1/5] Creating database migrations...${NC}"

# Create Alembic migration for audit logs
cat > alembic/versions/004_add_security_tables.py << 'EOF'
"""Add security tables (audit logs, MFA)

Revision ID: 004
Revises: 003
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True, index=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('success', sa.String(10), nullable=False),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_timestamp_action', 'audit_logs', ['timestamp', 'action'])
    op.create_index('ix_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_severity', 'audit_logs', ['severity', 'timestamp'])
    
    # MFA secrets table
    op.create_table(
        'mfa_secrets',
        sa.Column('user_id', sa.String(100), primary_key=True),
        sa.Column('secret', sa.String(32), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=False, nullable=False),
        sa.Column('backup_codes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_table('mfa_secrets')
    op.drop_table('audit_logs')
EOF

echo -e "${GREEN}✓ Migration created${NC}"

echo -e "\n${YELLOW}[2/5] Running migrations...${NC}"

alembic upgrade head

echo -e "${GREEN}✓ Migrations applied${NC}"

echo -e "\n${YELLOW}[3/5] Installing dependencies...${NC}"

pip install pyotp qrcode pillow --quiet

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "\n${YELLOW}[4/5] Testing audit logging...${NC}"

python -c "
import asyncio
from ios_core.security.audit_log import audit_logger, AuditAction

async def test():
    await audit_logger.log(
        action=AuditAction.SECURITY_ALERT,
        user_id='system',
        details={'test': 'Security setup complete'},
        success=True
    )
    print('Audit log test successful')

asyncio.run(test())
"

echo -e "${GREEN}✓ Audit logging works${NC}"

echo -e "\n${YELLOW}[5/5] Testing MFA...${NC}"

python -c "
import asyncio
from ios_core.security.mfa import mfa_manager

async def test():
    result = await mfa_manager.setup_mfa('test_user', 'test@example.com')
    print(f'MFA setup successful. Secret: {result[\"secret\"][:8]}...')

asyncio.run(test())
"

echo -e "${GREEN}✓ MFA works${NC}"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            SECURITY ENHANCEMENT COMPLETE                   ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}Features enabled:${NC}"
echo "  ✓ Comprehensive audit logging"
echo "  ✓ Two-factor authentication (2FA)"
echo "  ✓ Security monitoring"
echo "  ✓ Compliance tracking"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Restart IOS API server"
echo "  2. Enable MFA for admin users"
echo "  3. Review audit logs in Kibana"
echo "  4. Configure security alerts"

echo -e "\n${GREEN}Done!${NC}"