"""
Add search logs table

Revision ID: 008
Revises: 007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Create search_logs table"""
    
    op.create_table(
        'search_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('semantic_weight', sa.Float(), nullable=False),
        sa.Column('keyword_weight', sa.Float(), nullable=False),
        sa.Column('clicked_results', JSON, nullable=True),
        sa.Column('clicked_position', sa.Integer(), nullable=True),
        sa.Column('time_to_click_ms', sa.Integer(), nullable=True),
        sa.Column('query_info', JSON, nullable=True),
        sa.Column('had_results', sa.Integer(), nullable=False),
        sa.Column('user_satisfied', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_search_logs_timestamp', 'search_logs', ['timestamp'])
    op.create_index('idx_search_logs_user_id', 'search_logs', ['user_id'])
    op.create_index('idx_search_logs_query', 'search_logs', ['query'])
    op.create_index('idx_search_logs_had_results', 'search_logs', ['had_results'])


def downgrade():
    """Drop search_logs table"""
    
    op.drop_index('idx_search_logs_had_results', table_name='search_logs')
    op.drop_index('idx_search_logs_query', table_name='search_logs')
    op.drop_index('idx_search_logs_user_id', table_name='search_logs')
    op.drop_index('idx_search_logs_timestamp', table_name='search_logs')
    op.drop_table('search_logs')