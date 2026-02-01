"""Fix NULL owner_id values in existing boards

Revision ID: 006
Revises: 005
Create Date: 2025-09-05 23:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Assign existing boards with NULL owner_id to the first available user
    # This ensures existing boards don't vanish
    op.execute("""
        UPDATE boards 
        SET owner_id = (SELECT id FROM users ORDER BY id LIMIT 1) 
        WHERE owner_id IS NULL
    """)
    
    # Make owner_id non-nullable now that all boards have owners
    op.alter_column('boards', 'owner_id', nullable=False)


def downgrade() -> None:
    # Make owner_id nullable again
    op.alter_column('boards', 'owner_id', nullable=True)
