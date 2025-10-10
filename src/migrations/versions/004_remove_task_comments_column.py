"""Remove deprecated comments column from tasks table

Revision ID: 004_remove_task_comments_column
Revises: 003_add_task_comments_table
Create Date: 2025-09-06 16:42:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004_remove_task_comments_column"
down_revision = "003_add_task_comments_table"
branch_labels = None
depends_on = None


def upgrade():
    """Remove the deprecated comments column from tasks table."""
    # Remove the comments column
    op.drop_column("tasks", "comments")


def downgrade():
    """Add back the comments column to tasks table."""
    # Add back the comments column
    op.add_column("tasks", sa.Column("comments", sa.Text(), nullable=True))
