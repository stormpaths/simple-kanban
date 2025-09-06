"""Make hashed_password nullable for OIDC users

Revision ID: 004
Revises: 003
Create Date: 2025-09-05 19:13:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Make hashed_password column nullable to support OIDC-only users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=True)


def downgrade():
    # Revert hashed_password column to not nullable
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=False)
