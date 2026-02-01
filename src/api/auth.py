"""
Authentication API endpoints for user registration, login, and profile management.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db_session
from ..models import User
from ..auth.jwt_handler import JWTHandler
from ..schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    PasswordChangeRequest,
    TokenResponse,
    MessageResponse,
)
from ..auth.dependencies import get_current_user, get_current_admin_user, get_user_from_api_key_or_jwt
from ..auth import session_service
from ..utils.error_handler import (
    handle_auth_error,
    handle_validation_error,
    handle_not_found_error,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
jwt_handler = JWTHandler()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate, db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Register a new user account.

    Creates a new user with hashed password and returns user data.
    """
    try:
        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_verified=True,  # Auto-verify for now, can add email verification later
        )
        user.set_password(user_data.password)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        handle_auth_error(
            e, "user registration", username=user_data.username, email=user_data.email
        )


@router.post("/login")
async def login_user(
    request: Request,
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Authenticate user and return JWT token.

    Accepts username or email with password.
    Creates a persistent session in the database.
    """
    try:
        # Try to find user by username or email
        result = await db.execute(
            select(User).where(
                (User.username == user_credentials.username)
                | (User.email == user_credentials.username)
            )
        )
        user = result.scalar_one_or_none()

        if not user or not user.verify_password(user_credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not active"
            )

        # Create JWT token
        token_response = jwt_handler.create_token_response(user.id, user.username)
        
        # Store session in database for persistence across deployments
        user_agent = request.headers.get("user-agent", "")[:512]
        ip_address = request.client.host if request.client else None
        await session_service.create_session(
            db=db,
            user_id=user.id,
            token=token_response["access_token"],
            user_agent=user_agent,
            ip_address=ip_address,
        )
        
        return token_response

    except HTTPException:
        raise
    except Exception as e:
        handle_auth_error(e, "user login", username=user_credentials.username)


@router.post("/logout")
async def logout_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Logout user and invalidate session.
    
    Removes the session from the database.
    """
    token = None
    
    # Get token from header or cookie
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.cookies.get("access_token")
    
    if token:
        await session_service.delete_session(db, token)
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user's profile information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Update current user's profile information."""

    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_update.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = user_update.email

    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Change user password."""
    # Verify current password
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    await db.commit()

    return MessageResponse(message="Password changed successfully")


@router.get("/debug")
async def debug_auth(request: Request):
    """Debug authentication status."""
    try:
        # Check for access token in cookies
        access_token = request.cookies.get("access_token")
        if not access_token:
            return {"status": "no_cookie", "cookies": list(request.cookies.keys())}

        # Try to decode token
        from ..auth.jwt_handler import JWTHandler

        jwt_handler = JWTHandler()
        token_data = jwt_handler.verify_token(access_token)

        if not token_data:
            return {"status": "invalid_token", "token_length": len(access_token)}

        # Check user in database
        from ..database import get_db_session
        from sqlalchemy import select

        async with get_db_session() as db:
            result = await db.execute(select(User).where(User.id == token_data.user_id))
            user = result.scalar_one_or_none()

        if not user:
            return {"status": "user_not_found", "token_user_id": token_data.user_id}

        return {
            "status": "authenticated",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "token_user_id": token_data.user_id,
            "token_subject": token_data.sub,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users


@router.put("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Activate a user account (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = True
    await db.commit()
    await db.refresh(user)

    return user


@router.put("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Deactivate a user account (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    user.is_active = False
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/users/search")
async def search_users(
    email: str = None,
    username: str = None,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Search for users by email or username.
    
    Returns a list of matching users (limited to 10 results).
    Only returns basic user info (id, username, email, full_name).
    """
    if not email and not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either email or username to search"
        )
    
    # Build query
    query = select(User).where(User.is_active == True)
    
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    elif username:
        query = query.where(User.username.ilike(f"%{username}%"))
    
    # Limit results
    query = query.limit(10)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Return basic user info only
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }
        for user in users
    ]
