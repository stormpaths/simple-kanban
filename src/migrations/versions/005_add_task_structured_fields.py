"""
Migration 005: Add structured data fields to tasks.

Adds tags, metadata, priority, steps, and results fields for enhanced
task tracking and agent integration.
"""

import asyncio
import asyncpg
import os


async def upgrade(conn: asyncpg.Connection) -> None:
    """Add structured data fields to tasks table."""
    
    # Add tags (JSON array for labels displayed in table view)
    await conn.execute("""
        ALTER TABLE tasks 
        ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb
    """)
    
    # Add task_metadata (JSON object for structured agent/integration data)
    await conn.execute("""
        ALTER TABLE tasks 
        ADD COLUMN IF NOT EXISTS task_metadata JSONB DEFAULT '{}'::jsonb
    """)
    
    # Add priority (enum-like string: low, medium, high, critical)
    await conn.execute("""
        ALTER TABLE tasks 
        ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium'
    """)
    
    # Add steps (JSON array for tracking completion steps)
    # Format: [{"step": "description", "completed": bool, "completed_at": timestamp}]
    await conn.execute("""
        ALTER TABLE tasks 
        ADD COLUMN IF NOT EXISTS steps JSONB DEFAULT '[]'::jsonb
    """)
    
    # Add results (JSON object for final results/summary)
    # Format: {"summary": "...", "output": "...", "status": "success|failed|partial"}
    await conn.execute("""
        ALTER TABLE tasks 
        ADD COLUMN IF NOT EXISTS results JSONB DEFAULT NULL
    """)
    
    # Create index on tags for efficient filtering
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN (tags)
    """)
    
    # Create index on priority for filtering
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)
    """)
    
    print("Migration 005: Added structured data fields to tasks")


async def downgrade(conn: asyncpg.Connection) -> None:
    """Remove structured data fields from tasks table."""
    
    await conn.execute("DROP INDEX IF EXISTS idx_tasks_priority")
    await conn.execute("DROP INDEX IF EXISTS idx_tasks_tags")
    await conn.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS results")
    await conn.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS steps")
    await conn.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS priority")
    await conn.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS task_metadata")
    await conn.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS tags")
    
    print("Migration 005: Removed structured data fields from tasks")


async def main():
    """Run migration directly."""
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    conn = await asyncpg.connect(database_url)
    try:
        await upgrade(conn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
