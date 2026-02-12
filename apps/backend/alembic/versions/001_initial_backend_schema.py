"""Initial backend database schema with users and usage tracking.

Revision ID: 001
Revises:
Create Date: 2025-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('plan_tier', sa.String(length=50), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_token'), 'users', ['token'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # Create usage logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_cents', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_logs_user_id'), 'usage_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_usage_logs_created_at'), 'usage_logs', ['created_at'], unique=False)

    # Create rate limits table
    op.create_table(
        'rate_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reset_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_rate_limits_user_id'), 'rate_limits', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_rate_limits_user_id'), table_name='rate_limits')
    op.drop_table('rate_limits')
    op.drop_index(op.f('ix_usage_logs_created_at'), table_name='usage_logs')
    op.drop_index(op.f('ix_usage_logs_user_id'), table_name='usage_logs')
    op.drop_table('usage_logs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_token'), table_name='users')
    op.drop_table('users')
