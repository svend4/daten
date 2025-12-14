"""
Add embedding tracking fields

Revision ID: 007
Revises: 006
"""

from alembic import op
import sqlalchemy as sa


revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add embedding fields to documents table"""
    
    op.add_column(
        'documents',
        sa.Column('embedding_indexed', sa.Boolean(), nullable=False, server_default='false')
    )
    
    op.add_column(
        'documents',
        sa.Column('embedding_updated_at', sa.DateTime(), nullable=True)
    )
    
    # Add index for pending embeddings
    op.create_index(
        'idx_embedding_pending',
        'documents',
        ['embedding_indexed', 'updated_at']
    )


def downgrade():
    """Remove embedding fields"""
    
    op.drop_index('idx_embedding_pending', table_name='documents')
    op.drop_column('documents', 'embedding_updated_at')
    op.drop_column('documents', 'embedding_indexed')