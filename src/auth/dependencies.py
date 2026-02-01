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
from . import session_service

# HTTP Bearer token scheme (auto_error=False to make it optional)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get the current authenticated user from JWT token or cookie.

    Supports both Bearer token authentication and cookie-based authentication.
    First checks database for persistent sessions, then falls back to JWT validation.
    Raises HTTPException if no valid authentication found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = None
    token = None

    # Get token from Bearer header or cookie
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")

    if token:
        # First, try database session validation (survives deployments)
        session_result = await session_service.validate_session(db, token)
        if session_result:
            _, user = session_result
        else:
            # Fall back to JWT validation (for new tokens not yet in DB)
            token_data = jwt_handler.verify_token(token)
            if token_data:
                result = await db.execute(select(User).where(User.id == token_data.user_id))
                user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for clarity)."""
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
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
    required_scope: Optional[str] = None,
) -> tuple[User, ApiKey]:
    """
    Authenticate using API key and return user and API key.

    Uses raw asyncpg queries to avoid SQLAlchemy MissingGreenlet issues.

    Args:
        credentials: Bearer token credentials
        db: Database session (unused, kept for compatibility)
        required_scope: Optional scope requirement

    Returns:
        tuple: (User, ApiKey) if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    import logging
    import os
    import asyncpg
    from datetime import datetime, timezone

    logger = logging.getLogger(__name__)

    logger.info(
        f"[API_KEY_AUTH] Attempting to authenticate API key: {credentials.credentials[:20]}..."
    )

    if not credentials.credentials.startswith("sk_"):
        logger.warning(
            f"[API_KEY_AUTH] Invalid API key format: {credentials.credentials[:10]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Hash the provided key for lookup
    key_hash = ApiKey.hash_key(credentials.credentials)
    logger.info(f"[API_KEY_AUTH] Key hash: {key_hash}")

    # Get database connection info from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("[API_KEY_AUTH] DATABASE_URL not found in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error",
        )

    try:
        # Parse database URL for asyncpg connection
        # Format: postgresql://user:password@host:port/database
        if database_url.startswith("postgresql://"):
            # Extract connection parameters
            import urllib.parse

            parsed = urllib.parse.urlparse(database_url)

            # Connect directly with asyncpg
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading slash
            )

            try:
                # Find the API key with user information
                api_key_row = await conn.fetchrow(
                    """
                    SELECT ak.id, ak.name, ak.description, ak.key_hash, ak.key_prefix,
                           ak.user_id, ak.scopes, ak.expires_at, ak.is_active,
                           ak.last_used_at, ak.usage_count, ak.created_at, ak.updated_at,
                           u.id as user_id, u.username, u.email, u.full_name,
                           u.is_active as user_is_active, u.is_admin, u.is_verified
                    FROM api_keys ak
                    JOIN users u ON ak.user_id = u.id
                    WHERE ak.key_hash = $1
                """,
                    key_hash,
                )

                if not api_key_row:
                    logger.warning(
                        f"[API_KEY_AUTH] API key not found in database for hash: {key_hash}"
                    )

                    # Debug: Check if any API keys exist
                    count = await conn.fetchval("SELECT COUNT(*) FROM api_keys")
                    logger.info(f"[API_KEY_AUTH] Total API keys in database: {count}")

                    if count > 0:
                        sample_prefixes = await conn.fetch(
                            "SELECT key_prefix FROM api_keys LIMIT 3"
                        )
                        logger.info(
                            f"[API_KEY_AUTH] Sample key prefixes: {[row['key_prefix'] for row in sample_prefixes]}"
                        )

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                logger.info(
                    f"[API_KEY_AUTH] Found API key: ID={api_key_row['id']}, Name={api_key_row['name']}, Active={api_key_row['is_active']}"
                )

                # Check if API key is active
                if not api_key_row["is_active"]:
                    logger.warning(f"[API_KEY_AUTH] API key is inactive")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API key is inactive or expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # Check if API key is expired
                if api_key_row["expires_at"]:
                    now = datetime.now(timezone.utc)
                    if now > api_key_row["expires_at"]:
                        logger.warning(
                            f"[API_KEY_AUTH] API key has expired: {api_key_row['expires_at']}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key is inactive or expired",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                # Check scope if required
                if required_scope:
                    scopes = (
                        api_key_row["scopes"].split(",")
                        if api_key_row["scopes"]
                        else []
                    )
                    scopes = [s.strip() for s in scopes]

                    # Admin scope grants all permissions
                    if required_scope not in scopes and "admin" not in scopes:
                        logger.warning(
                            f"[API_KEY_AUTH] API key missing required scope: {required_scope}, has: {scopes}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"API key does not have required scope: {required_scope}",
                        )

                # Check if user is active
                if not api_key_row["user_is_active"]:
                    logger.warning(
                        f"[API_KEY_AUTH] User is inactive: {api_key_row['username']}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is inactive",
                    )

                logger.info(
                    f"[API_KEY_AUTH] Authentication successful for user: {api_key_row['username']}"
                )

                # Record usage
                await conn.execute(
                    """
                    UPDATE api_keys 
                    SET last_used_at = $1, usage_count = usage_count + 1, updated_at = $1
                    WHERE id = $2
                """,
                    datetime.now(timezone.utc),
                    api_key_row["id"],
                )

                # Create User and ApiKey objects for return
                user = User(
                    id=api_key_row["user_id"],
                    username=api_key_row["username"],
                    email=api_key_row["email"],
                    full_name=api_key_row["full_name"],
                    is_active=api_key_row["user_is_active"],
                    is_admin=api_key_row["is_admin"],
                    is_verified=api_key_row["is_verified"],
                )

                api_key = ApiKey(
                    id=api_key_row["id"],
                    name=api_key_row["name"],
                    description=api_key_row["description"],
                    key_hash=api_key_row["key_hash"],
                    key_prefix=api_key_row["key_prefix"],
                    user_id=api_key_row["user_id"],
                    scopes=api_key_row["scopes"],
                    expires_at=api_key_row["expires_at"],
                    is_active=api_key_row["is_active"],
                    last_used_at=api_key_row["last_used_at"],
                    usage_count=api_key_row["usage_count"] + 1,  # Reflect the increment
                    created_at=api_key_row["created_at"],
                    updated_at=datetime.now(timezone.utc),
                )
                api_key.user = user

                return user, api_key

            finally:
                await conn.close()

        else:
            logger.error(
                f"[API_KEY_AUTH] Unsupported database URL format: {database_url[:20]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database configuration error",
            )

    except asyncpg.PostgresError as e:
        logger.error(f"[API_KEY_AUTH] Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during authentication",
        )
    except Exception as e:
        logger.error(f"[API_KEY_AUTH] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_user_from_api_key_or_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    required_scope: Optional[str] = None,
) -> User:
    """
    Authenticate user using either API key or JWT token.

    Supports multiple authentication methods:
    1. API key via X-API-Key header
    2. API key via Authorization: Bearer sk_...
    3. JWT token via Authorization: Bearer or cookie

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
    import logging

    logger = logging.getLogger(__name__)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check for X-API-Key header first (common convention)
    x_api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if x_api_key and x_api_key.startswith("sk_"):
        logger.info("[AUTH] Found X-API-Key header, attempting API key authentication")
        try:
            # Create credentials-like object for authenticate_api_key
            class ApiKeyCredentials:
                def __init__(self, key: str):
                    self.credentials = key
            
            user, _ = await authenticate_api_key(ApiKeyCredentials(x_api_key), db, required_scope)
            logger.info(f"[AUTH] X-API-Key authentication successful for user: {user.username}")
            return user
        except HTTPException as e:
            logger.warning(f"[AUTH] X-API-Key authentication failed: {e.detail}")
            raise credentials_exception

    logger.info(
        f"[AUTH] Authentication attempt - credentials present: {credentials is not None}"
    )
    if credentials:
        logger.info(f"[AUTH] Credential type: {credentials.credentials[:10]}...")

    # Try API key authentication if credentials look like an API key
    if credentials and credentials.credentials.startswith("sk_"):
        logger.info("[AUTH] Attempting API key authentication via Bearer token")
        try:
            user, _ = await authenticate_api_key(credentials, db, required_scope)
            logger.info(
                f"[AUTH] API key authentication successful for user: {user.username}"
            )
            return user
        except HTTPException as e:
            logger.warning(f"[AUTH] API key authentication failed: {e.detail}")
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
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        return await get_user_from_api_key_or_jwt(request, credentials, db, scope)

    return _require_scope
