"""Add comments field to tasks table

Revision ID: 007
Revises: 006
Create Date: 2025-09-06 15:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add comments column to tasks table."""
    op.add_column('tasks', sa.Column('comments', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove comments column from tasks table."""
    op.drop_column('tasks', 'comments')
