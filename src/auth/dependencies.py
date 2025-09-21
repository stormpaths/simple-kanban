"""
Authentication dependencies for FastAPI endpoints.
"""
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..database import get_db_session
from ..models.user import User
from ..models.api_key import ApiKey
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
    request: Request,
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
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def authenticate_api_key(
    credentials: HTTPAuthorizationCredentials,
    db: AsyncSession,
    required_scope: Optional[str] = None
) -> tuple[User, ApiKey]:
    """
    Authenticate using API key and return user and API key.
    
    Args:
        credentials: Bearer token credentials
        db: Database session
        required_scope: Optional scope requirement
        
    Returns:
        tuple: (User, ApiKey) if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials.credentials.startswith("sk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hash the provided key for lookup
    key_hash = ApiKey.hash_key(credentials.credentials)
    
    # Find the API key in database
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.key_hash == key_hash)
        .options(selectinload(ApiKey.user))
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if API key is valid
    if not api_key.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check scope if required
    if required_scope and not api_key.has_scope(required_scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key does not have required scope: {required_scope}",
        )
    
    # Check if user is active
    if not api_key.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Record usage
    api_key.record_usage()
    await db.commit()
    
    return api_key.user, api_key


async def get_user_from_api_key_or_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    required_scope: Optional[str] = None
) -> User:
    """
    Authenticate user using either API key or JWT token.
    
    Supports both authentication methods:
    1. API key (Bearer sk_...)
    2. JWT token (Bearer jwt_token or cookie)
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session
        required_scope: Optional API key scope requirement (ignored for JWT)
        
    Returns:
        User: Authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try API key authentication first if credentials look like an API key
    if credentials and credentials.credentials.startswith("sk_"):
        try:
            user, _ = await authenticate_api_key(credentials, db, required_scope)
            return user
        except HTTPException:
            raise credentials_exception
    
    # Fall back to JWT authentication
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        raise credentials_exception


def require_api_scope(scope: str):
    """
    Dependency factory for requiring specific API key scopes.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: User = Depends(require_api_scope("admin"))):
            ...
    """
    async def _require_scope(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_db_session)
    ) -> User:
        return await get_user_from_api_key_or_jwt(request, credentials, db, scope)
    
    return _require_scope
