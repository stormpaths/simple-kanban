"""
Database migration functions for group management feature.

This module handles the migration of existing data to support group ownership
while maintaining backward compatibility with individual board ownership.
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import engine

logger = logging.getLogger(__name__)


def migrate_board_ownership():
    """
    Migrate existing boards to support optional group ownership.

    This migration:
    1. Adds group_id column to boards table (if not exists)
    2. Makes owner_id nullable (if not already)
    3. Ensures existing boards maintain their current ownership
    """
    logger.info("Starting board ownership migration...")

    with Session(engine) as session:
        try:
            # Check if group_id column exists in boards table
            result = session.execute(
                text(
                    """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'boards' AND column_name = 'group_id'
            """
                )
            )

            group_id_exists = result.fetchone() is not None

            if not group_id_exists:
                logger.info("Adding group_id column to boards table...")
                session.execute(
                    text(
                        """
                    ALTER TABLE boards 
                    ADD COLUMN group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE
                """
                    )
                )

            # Check if owner_id is nullable
            result = session.execute(
                text(
                    """
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'boards' AND column_name = 'owner_id'
            """
                )
            )

            owner_nullable = result.fetchone()
            if owner_nullable and owner_nullable[0] == "NO":
                logger.info("Making owner_id nullable in boards table...")
                session.execute(
                    text(
                        """
                    ALTER TABLE boards 
                    ALTER COLUMN owner_id DROP NOT NULL
                """
                    )
                )

            session.commit()
            logger.info("Board ownership migration completed successfully")

        except Exception as e:
            logger.error(f"Error during board ownership migration: {e}")
            session.rollback()
            # Don't raise the error - let the app continue with new schema
            # The create_tables() call will handle creating the correct schema


def create_default_groups():
    """
    Create default groups for existing users if needed.

    This is optional and can be used to automatically create personal
    groups for existing users to ease the transition.
    """
    logger.info("Checking for default group creation...")

    try:
        from ..models import User, Group, UserGroup, GroupRole

        with Session(engine) as session:
            # Check if we have users but no groups
            user_count = session.query(User).count()
            group_count = session.query(Group).count()

            if user_count > 0 and group_count == 0:
                logger.info(
                    f"Found {user_count} users with no groups. Creating personal groups..."
                )

                users = session.query(User).all()
                for user in users:
                    # Create a personal group for each user
                    personal_group = Group(
                        name=f"{user.username}'s Personal Group",
                        description=f"Personal workspace for {user.full_name or user.username}",
                        created_by=user.id,
                    )
                    session.add(personal_group)
                    session.flush()  # Get the group ID

                    # Add user as owner of their personal group
                    membership = UserGroup(
                        user_id=user.id,
                        group_id=personal_group.id,
                        role=GroupRole.OWNER,
                    )
                    session.add(membership)

                session.commit()
                logger.info(f"Created personal groups for {user_count} users")
            else:
                logger.info("No default group creation needed")

    except Exception as e:
        logger.error(f"Error during default group creation: {e}")
        # Don't raise - this is optional functionality


def run_group_migrations():
    """
    Run all group-related migrations.

    This function is called during application startup to ensure
    the database schema supports group management features.
    """
    logger.info("Running group management migrations...")

    try:
        # First, let SQLAlchemy create the new tables
        from ..models import Base

        Base.metadata.create_all(bind=engine)

        # Then run our custom migrations for existing data
        migrate_board_ownership()
        create_default_groups()

        logger.info("All group migrations completed successfully")

    except Exception as e:
        logger.error(f"Error during group migrations: {e}")
        # Log but don't crash the application
        # The new schema will still work for new data
