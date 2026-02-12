"""Initial CLI database schema.

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
    # Create reminders table
    op.create_table(
        'reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(length=1000), nullable=False),
        sa.Column('due_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('done_at', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('project_context', sa.String(length=500), nullable=True),
        sa.Column('ai_suggested_text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reminders_due_at'), 'reminders', ['due_at'], unique=False)
    op.create_index(op.f('ix_reminders_done_at'), 'reminders', ['done_at'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_reminders_done_at'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_due_at'), table_name='reminders')
    op.drop_table('reminders')
