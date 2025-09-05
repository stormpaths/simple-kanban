#!/bin/bash
set -e

echo "Starting Simple Kanban application..."

# Wait for database to be ready
echo "Waiting for database connection..."
export DATABASE_URL="${DATABASE_URL:-postgresql://kanban:kanban@simple-kanban-postgres-postgresql.apps.svc.cluster.local:5432/simple_kanban}"
echo "Using DATABASE_URL: $DATABASE_URL"

python -c "
import time
import sys
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
print(f'Connecting to: {DATABASE_URL}')

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database connection successful!')
        break
    except Exception as e:
        retry_count += 1
        print(f'Database connection attempt {retry_count}/{max_retries} failed: {str(e)[:200]}')
        if retry_count >= max_retries:
            print('Failed to connect to database after maximum retries')
            sys.exit(1)
        time.sleep(2)
"

# Handle database schema setup
echo "Setting up database schema..."

python -c "
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if users table exists and what columns it has
    users_exists = conn.execute(text('''
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        )
    ''')).scalar()
    
    if users_exists:
        print('Users table exists, checking columns...')
        
        # Get existing columns
        existing_cols = conn.execute(text('''
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users'
        ''')).fetchall()
        existing_column_names = [row[0] for row in existing_cols]
        print(f'Existing columns: {existing_column_names}')
        
        # Add missing auth columns
        auth_columns = {
            'hashed_password': 'VARCHAR',
            'full_name': 'VARCHAR', 
            'is_active': 'BOOLEAN DEFAULT true',
            'is_admin': 'BOOLEAN DEFAULT false',
            'is_verified': 'BOOLEAN DEFAULT false'
        }
        
        for col_name, col_type in auth_columns.items():
            if col_name not in existing_column_names:
                print(f'Adding missing column: {col_name}')
                try:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'))
                    conn.commit()
                except Exception as e:
                    print(f'Error adding column {col_name}: {e}')
            else:
                print(f'Column {col_name} already exists')
    else:
        print('Users table does not exist, will create via alembic')
    
    # Ensure alembic version table is properly set up
    alembic_exists = conn.execute(text('''
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        )
    ''')).scalar()
    
    if not alembic_exists:
        print('Creating alembic_version table')
        conn.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
        conn.execute(text('INSERT INTO alembic_version (version_num) VALUES (\'002\')'))
        conn.commit()
    else:
        # Update to latest version if we manually added columns
        if users_exists:
            conn.execute(text('UPDATE alembic_version SET version_num = \'002\''))
            conn.commit()
"

# Run alembic upgrade (should be a no-op if we're already at latest version)
echo "Running alembic upgrade..."
alembic upgrade head

echo "Database migrations completed successfully!"

# Start the application
echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
