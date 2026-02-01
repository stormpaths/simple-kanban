"""
Database migration for task structured data fields.

Adds tags, task_metadata, priority, steps, and results fields
for enhanced task tracking and agent integration.
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import engine

logger = logging.getLogger(__name__)


def migrate_task_fields():
    """
    Add structured data fields to tasks table.
    
    This migration adds:
    - tags: JSON array for labels/table view display
    - task_metadata: JSON object for agent tracking
    - priority: String (low/medium/high/critical)
    - steps: JSON array for completion tracking
    - results: JSON object for final summary
    """
    logger.info("Starting task structured fields migration...")

    with Session(engine) as session:
        try:
            # Check if tags column exists
            result = session.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'tasks' AND column_name = 'tags'
                """)
            )
            
            if result.fetchone() is None:
                logger.info("Adding structured fields to tasks table...")
                
                # Add tags column
                session.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb
                """))
                
                # Add task_metadata column
                session.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS task_metadata JSONB DEFAULT '{}'::jsonb
                """))
                
                # Add priority column
                session.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium'
                """))
                
                # Add steps column
                session.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS steps JSONB DEFAULT '[]'::jsonb
                """))
                
                # Add results column
                session.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS results JSONB DEFAULT NULL
                """))
                
                # Create indexes
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN (tags)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)
                """))
                
                session.commit()
                logger.info("Task structured fields migration completed")
            else:
                logger.info("Task structured fields already exist, skipping migration")
                
        except Exception as e:
            logger.error(f"Error during task fields migration: {e}")
            session.rollback()
            raise


def run_task_fields_migration():
    """Run task fields migration."""
    try:
        migrate_task_fields()
        logger.info("Task fields migration completed successfully")
    except Exception as e:
        logger.error(f"Task fields migration failed: {e}")
        raise
