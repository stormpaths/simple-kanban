"""
OIDC authentication API endpoints.
"""

import secrets
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db_session, AsyncSessionLocal
from ..models import User, OIDCProvider
from ..auth.oidc_client import get_oidc_client
from ..auth.oidc_config import oidc_config
from ..auth.jwt_handler import JWTHandler
from ..schemas import (
    OIDCAuthRequest,
    OIDCCallbackRequest,
    TokenResponse,
    AccountLinkRequest,
)
from ..auth.dependencies import get_current_user
from ..utils.error_handler import (
    handle_auth_error,
    handle_validation_error,
    handle_generic_error,
)

router = APIRouter(prefix="/oidc", tags=["oidc"])
jwt_handler = JWTHandler()


@router.get("/providers")
async def get_available_providers() -> Dict[str, str]:
    """Get list of available OIDC providers."""
    return oidc_config.get_available_providers()


@router.post("/auth/{provider}")
async def initiate_oidc_auth(
    provider: str, request: Request, response: Response
) -> Dict[str, Any]:
    """Initiate OIDC authentication flow."""
    if not oidc_config.is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' is not configured",
        )

    try:
        oidc_client = get_oidc_client(provider)
        state = oidc_client.generate_state()

        # Store state in session/cookie for CSRF protection
        response.set_cookie(
            key=f"oidc_state_{provider}",
            value=state,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=True,
            samesite="lax",
        )

        auth_url = await oidc_client.get_authorization_url(state)

        return {"auth_url": auth_url, "provider": provider, "state": state}

    except Exception as e:
        handle_auth_error(e, "OIDC authentication initiation", provider=provider)


@router.get("/callback/{provider}")
async def oidc_callback(
    provider: str, code: str, state: str, request: Request, response: Response
) -> Dict[str, Any]:
    """Handle OIDC provider callback."""
    if not oidc_config.is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' is not configured",
        )

    # Verify state parameter for CSRF protection
    stored_state = request.cookies.get(f"oidc_state_{provider}")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter"
        )

    # Clear the state cookie
    response.delete_cookie(f"oidc_state_{provider}")

    try:
        oidc_client = get_oidc_client(provider)

        # Exchange code for tokens
        token_data = await oidc_client.exchange_code_for_tokens(code, state)
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from provider",
            )

        # Get user info from provider
        user_info = await oidc_client.get_user_info(access_token)
        provider_user_id = user_info.get("sub") or user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        avatar_url = user_info.get("picture")

        if not provider_user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient user information from provider",
            )

        # Use raw asyncpg connection to bypass SQLAlchemy async issues
        import asyncpg
        import os

        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://kanban:kanban@simple-kanban-postgres-postgresql.apps.svc.cluster.local:5432/simple_kanban",
        )

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Check if OIDC provider is already linked to a user
            oidc_row = await conn.fetchrow(
                "SELECT id, user_id FROM oidc_providers WHERE provider = $1 AND provider_user_id = $2",
                provider,
                provider_user_id,
            )

            if oidc_row:
                # Get the user
                user_row = await conn.fetchrow(
                    "SELECT id, username, email, full_name, is_active, is_admin, is_verified FROM users WHERE id = $1",
                    oidc_row["user_id"],
                )

                if not user_row["is_active"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User account is deactivated",
                    )

                # Update provider info
                await conn.execute(
                    "UPDATE oidc_providers SET provider_email = $1, provider_name = $2, provider_avatar_url = $3, updated_at = NOW() WHERE id = $4",
                    email,
                    name,
                    avatar_url,
                    oidc_row["id"],
                )

                # Generate JWT token
                token_response = jwt_handler.create_token_response(
                    user_row["id"], user_row["username"]
                )

                # Set JWT token in secure cookie and redirect to main app
                redirect_response = RedirectResponse(url="/", status_code=302)
                redirect_response.set_cookie(
                    key="access_token",
                    value=token_response["access_token"],
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=1800,  # 30 minutes
                )
                return redirect_response

            else:
                # Check if user exists with this email
                existing_user_row = await conn.fetchrow(
                    "SELECT id, username, email, full_name, is_active, is_admin, is_verified FROM users WHERE email = $1",
                    email,
                )

                if existing_user_row:
                    # Link OIDC provider to existing user
                    await conn.execute(
                        "INSERT INTO oidc_providers (user_id, provider, provider_user_id, provider_email, provider_name, provider_avatar_url) VALUES ($1, $2, $3, $4, $5, $6)",
                        existing_user_row["id"],
                        provider,
                        provider_user_id,
                        email,
                        name,
                        avatar_url,
                    )

                    # Generate JWT token
                    token_response = jwt_handler.create_token_response(
                        existing_user_row["id"], existing_user_row["username"]
                    )

                    # Set JWT token in secure cookie and redirect to main app
                    redirect_response = RedirectResponse(url="/", status_code=302)
                    redirect_response.set_cookie(
                        key="access_token",
                        value=token_response["access_token"],
                        httponly=True,
                        secure=True,
                        samesite="lax",
                        max_age=1800,  # 30 minutes
                    )
                    return redirect_response

                else:
                    # Create new user account
                    username = email.split("@")[0]  # Use email prefix as username
                    counter = 1
                    original_username = username

                    # Ensure username is unique
                    while True:
                        existing_username = await conn.fetchval(
                            "SELECT id FROM users WHERE username = $1", username
                        )
                        if not existing_username:
                            break
                        username = f"{original_username}{counter}"
                        counter += 1

                    # Insert new user
                    user_id = await conn.fetchval(
                        "INSERT INTO users (username, email, full_name, is_active, is_admin, is_verified) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
                        username,
                        email,
                        name,
                        True,
                        False,
                        True,
                    )

                    # Create OIDC provider link
                    await conn.execute(
                        "INSERT INTO oidc_providers (user_id, provider, provider_user_id, provider_email, provider_name, provider_avatar_url) VALUES ($1, $2, $3, $4, $5, $6)",
                        user_id,
                        provider,
                        provider_user_id,
                        email,
                        name,
                        avatar_url,
                    )

                    # Generate JWT token
                    token_response = jwt_handler.create_token_response(
                        user_id, username
                    )

                    # Set JWT token in secure cookie and redirect to main app
                    redirect_response = RedirectResponse(url="/", status_code=302)
                    redirect_response.set_cookie(
                        key="access_token",
                        value=token_response["access_token"],
                        httponly=True,
                        secure=True,
                        samesite="lax",
                        max_age=1800,  # 30 minutes
                    )
                    return redirect_response
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        handle_auth_error(e, "OIDC callback processing", provider=provider, code=code)


@router.post("/link-account")
async def link_oidc_account(
    link_request: AccountLinkRequest, db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Link an OIDC provider to an existing user account."""
    # Verify existing user credentials
    result = await db.execute(
        select(User).where(User.username == link_request.username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.verify_password(link_request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated",
        )

    # Check if OIDC provider is already linked
    result = await db.execute(
        select(OIDCProvider).where(
            OIDCProvider.provider == link_request.provider,
            OIDCProvider.provider_user_id == link_request.provider_user_id,
        )
    )
    existing_link = result.scalar_one_or_none()

    if existing_link:
        if existing_link.user_id == user.id:
            return {"message": "Account is already linked to this provider"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This provider account is already linked to another user",
            )

    # Create the link
    new_oidc_provider = OIDCProvider(
        user_id=user.id,
        provider=link_request.provider,
        provider_user_id=link_request.provider_user_id,
    )
    db.add(new_oidc_provider)
    await db.commit()

    return {"message": "Account successfully linked to OIDC provider"}


@router.delete("/unlink/{provider}")
async def unlink_oidc_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Unlink an OIDC provider from the current user account."""
    result = await db.execute(
        select(OIDCProvider).where(
            OIDCProvider.user_id == current_user.id, OIDCProvider.provider == provider
        )
    )
    oidc_provider = result.scalar_one_or_none()

    if not oidc_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {provider} account linked to this user",
        )

    # Ensure user has a password or other OIDC providers before unlinking
    if not current_user.hashed_password:
        # Check if user has other OIDC providers
        result = await db.execute(
            select(OIDCProvider).where(
                OIDCProvider.user_id == current_user.id,
                OIDCProvider.provider != provider,
            )
        )
        other_providers = result.scalars().all()

        if not other_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink the only authentication method. Set a password first.",
            )

    await db.delete(oidc_provider)
    await db.commit()

    return {"message": f"{provider.title()} account successfully unlinked"}


@router.get("/linked-accounts")
async def get_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get list of OIDC providers linked to the current user."""
    result = await db.execute(
        select(OIDCProvider).where(OIDCProvider.user_id == current_user.id)
    )
    oidc_providers = result.scalars().all()

    linked_accounts = []
    for provider in oidc_providers:
        linked_accounts.append(
            {
                "provider": provider.provider,
                "provider_email": provider.provider_email,
                "provider_name": provider.provider_name,
                "provider_avatar_url": provider.provider_avatar_url,
                "linked_at": provider.created_at,
            }
        )

    return {
        "linked_accounts": linked_accounts,
        "has_password": bool(current_user.hashed_password),
    }
