"""Add authentication fields to User model

Revision ID: 002
Revises: 001
Create Date: 2025-09-05 06:59:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def column_exists(connection, table_name, column_name):
    """Check if a column exists in a table"""
    result = connection.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.scalar() > 0


def upgrade() -> None:
    # Get connection to check existing columns
    connection = op.get_bind()
    
    # Add columns only if they don't exist
    if not column_exists(connection, 'users', 'hashed_password'):
        op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    
    if not column_exists(connection, 'users', 'full_name'):
        op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    
    if not column_exists(connection, 'users', 'is_active'):
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    if not column_exists(connection, 'users', 'is_admin'):
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    if not column_exists(connection, 'users', 'is_verified'):
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Get connection to check existing columns
    connection = op.get_bind()
    
    # Drop columns only if they exist
    if column_exists(connection, 'users', 'is_verified'):
        op.drop_column('users', 'is_verified')
    
    if column_exists(connection, 'users', 'is_admin'):
        op.drop_column('users', 'is_admin')
    
    if column_exists(connection, 'users', 'is_active'):
        op.drop_column('users', 'is_active')
    
    if column_exists(connection, 'users', 'full_name'):
        op.drop_column('users', 'full_name')
    
    if column_exists(connection, 'users', 'hashed_password'):
        op.drop_column('users', 'hashed_password')
