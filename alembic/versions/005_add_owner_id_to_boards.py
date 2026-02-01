"""Add owner_id to boards table

Revision ID: 005_add_owner_id_to_boards
Revises: 004_make_password_nullable
Create Date: 2025-09-05 22:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add owner_id column to boards table (nullable initially)
    op.add_column('boards', sa.Column('owner_id', sa.Integer(), nullable=True))
    
    # Assign existing boards to the first available user
    # This ensures existing boards don't vanish
    op.execute("""
        UPDATE boards 
        SET owner_id = (SELECT id FROM users ORDER BY id LIMIT 1) 
        WHERE owner_id IS NULL
    """)
    
    # Make owner_id non-nullable now that all boards have owners
    op.alter_column('boards', 'owner_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_boards_owner_id', 
        'boards', 
        'users', 
        ['owner_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    
    # Create index for performance
    op.create_index('ix_boards_owner_id', 'boards', ['owner_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_boards_owner_id', 'boards')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_boards_owner_id', 'boards', type_='foreignkey')
    
    # Drop column
    op.drop_column('boards', 'owner_id')
