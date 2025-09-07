#!/bin/bash
set -e

echo "Starting Simple Kanban application..."

# Wait for database to be ready
echo "Waiting for database connection..."
# Construct DATABASE_URL from environment variables
POSTGRES_HOST=${POSTGRES_HOST:-simple-kanban-postgres-postgresql.apps.svc.cluster.local}
POSTGRES_USER=${POSTGRES_USER:-kanban}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-kanban}
POSTGRES_DB=${POSTGRES_DB:-simple_kanban}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
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
    # Check if this is a fresh database (no tables except alembic_version)
    tables = conn.execute(text('''
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name != 'alembic_version'
    ''')).fetchall()
    
    if not tables:
        print('Fresh database detected, clearing alembic version for clean migration')
        # Clear any existing alembic version entries
        conn.execute(text('DELETE FROM alembic_version'))
        conn.commit()
    else:
        print(f'Existing tables found: {[t[0] for t in tables]}')
"

# DATABASE_URL already set above from environment variables

# Run alembic upgrade to ensure all migrations are applied
echo "Running alembic upgrade..."
alembic upgrade head

echo "Database migrations completed successfully!"

# Start the application
echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
