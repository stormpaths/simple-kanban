"""
Authentication dependencies for FastAPI endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..models.user import User
from .jwt_handler import jwt_handler

# HTTP Bearer token scheme (auto_error=False to make it optional)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Get the current authenticated user from JWT token or cookie.
    
    Supports both Bearer token authentication and cookie-based authentication.
    Raises HTTPException if no valid authentication found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = None
    
    # Try Bearer token authentication first
    if credentials:
        token_data = jwt_handler.verify_token(credentials.credentials)
        if token_data:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == token_data.user_id))
            user = result.scalar_one_or_none()
    
    # Try cookie authentication if Bearer token failed
    if not user:
        access_token = request.cookies.get("access_token")
        if access_token:
            token_data = jwt_handler.verify_token(access_token)
            if token_data:
                from sqlalchemy import select
                result = await db.execute(select(User).where(User.id == token_data.user_id))
                user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for clarity)."""
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
