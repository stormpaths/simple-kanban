"""
Database migration for persistent sessions table.

Creates sessions table to store user login tokens for persistence across deployments.
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import engine

logger = logging.getLogger(__name__)


def migrate_sessions_table():
    """
    Create sessions table for persistent login storage.
    
    This table stores JWT tokens so users stay logged in during deployments.
    """
    logger.info("Starting sessions table migration...")

    with Session(engine) as session:
        try:
            # Check if sessions table exists
            result = session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'sessions'
                """)
            )
            
            if result.fetchone() is None:
                logger.info("Creating sessions table...")
                
                session.execute(text("""
                    CREATE TABLE sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token_hash VARCHAR(64) UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                        last_used_at TIMESTAMP,
                        user_agent VARCHAR(512),
                        ip_address VARCHAR(45)
                    )
                """))
                
                # Create indexes
                session.execute(text("""
                    CREATE INDEX idx_sessions_user_id ON sessions(user_id)
                """))
                session.execute(text("""
                    CREATE INDEX idx_sessions_token_hash ON sessions(token_hash)
                """))
                session.execute(text("""
                    CREATE INDEX idx_sessions_expires_at ON sessions(expires_at)
                """))
                
                session.commit()
                logger.info("Sessions table created successfully")
            else:
                logger.info("Sessions table already exists, skipping migration")
                
        except Exception as e:
            logger.error(f"Error during sessions migration: {e}")
            session.rollback()
            raise


def run_sessions_migration():
    """Run sessions table migration."""
    try:
        migrate_sessions_table()
        logger.info("Sessions migration completed successfully")
    except Exception as e:
        logger.error(f"Sessions migration failed: {e}")
        raise
