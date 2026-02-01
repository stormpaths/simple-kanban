"""
Session service for persistent login across deployments.

Provides database-backed session storage so users stay logged in
when pods restart during deployments.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..models.session import Session
from ..models.user import User

logger = logging.getLogger(__name__)

# Session expiry (same as JWT expiry - 7 days)
SESSION_EXPIRY_DAYS = 7


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of the token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(
    db: AsyncSession,
    user_id: int,
    token: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Session:
    """
    Create a new session in the database.
    
    Args:
        db: Database session
        user_id: ID of the user
        token: JWT token to store (will be hashed)
        user_agent: Optional browser user agent
        ip_address: Optional client IP address
    
    Returns:
        Created Session object
    """
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)
    
    session = Session(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    logger.info(f"Created session for user {user_id}, expires {expires_at}")
    return session


async def validate_session(
    db: AsyncSession,
    token: str,
) -> Optional[Tuple[Session, User]]:
    """
    Validate a session token against the database.
    
    Args:
        db: Database session
        token: JWT token to validate
    
    Returns:
        Tuple of (Session, User) if valid, None otherwise
    """
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(Session)
        .where(Session.token_hash == token_hash)
        .where(Session.expires_at > datetime.utcnow())
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return None
    
    # Get the user
    result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return None
    
    # Update last_used_at
    session.last_used_at = datetime.utcnow()
    await db.commit()
    
    return (session, user)


async def delete_session(db: AsyncSession, token: str) -> bool:
    """
    Delete a session from the database (logout).
    
    Args:
        db: Database session
        token: JWT token to delete
    
    Returns:
        True if session was deleted, False otherwise
    """
    token_hash = hash_token(token)
    
    result = await db.execute(
        delete(Session).where(Session.token_hash == token_hash)
    )
    await db.commit()
    
    deleted = result.rowcount > 0
    if deleted:
        logger.info("Session deleted successfully")
    return deleted


async def delete_user_sessions(db: AsyncSession, user_id: int) -> int:
    """
    Delete all sessions for a user (logout everywhere).
    
    Args:
        db: Database session
        user_id: ID of the user
    
    Returns:
        Number of sessions deleted
    """
    result = await db.execute(
        delete(Session).where(Session.user_id == user_id)
    )
    await db.commit()
    
    logger.info(f"Deleted {result.rowcount} sessions for user {user_id}")
    return result.rowcount


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """
    Remove expired sessions from the database.
    
    Args:
        db: Database session
    
    Returns:
        Number of sessions cleaned up
    """
    result = await db.execute(
        delete(Session).where(Session.expires_at < datetime.utcnow())
    )
    await db.commit()
    
    if result.rowcount > 0:
        logger.info(f"Cleaned up {result.rowcount} expired sessions")
    return result.rowcount
