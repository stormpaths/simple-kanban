"""
API Key management endpoints.

This module provides REST API endpoints for managing API keys,
including creation, listing, updating, and deletion of API keys.
"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models import ApiKey, User, ApiKeyScope as ModelApiKeyScope
from ..schemas import (
    ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse, ApiKeyCreateResponse,
    ApiKeyListResponse, ApiKeyUsageStats
)
from ..auth.dependencies import get_current_user, get_user_from_api_key_or_jwt

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("/", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all API keys for the current user.
    
    Returns all API keys owned by the authenticated user, excluding the actual key values.
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    
    api_keys = result.scalars().all()
    
    # Debug logging
    print(f"[API_KEYS] User {current_user.id} ({current_user.username}) requesting API keys")
    print(f"[API_KEYS] Found {len(api_keys)} API keys in database")
    for key in api_keys:
        print(f"[API_KEYS] - Key ID {key.id}: {key.name} (active: {key.is_active})")
    
    # Convert to response format
    api_key_responses = []
    for key in api_keys:
        api_key_responses.append(ApiKeyResponse(
            id=key.id,
            name=key.name,
            description=key.description,
            key_prefix=key.key_prefix,
            scopes=key.get_scopes_list(),
            expires_at=key.expires_at,
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at,
            updated_at=key.updated_at
        ))
    
    return ApiKeyListResponse(
        api_keys=api_key_responses,
        total=len(api_key_responses)
    )


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new API key.
    
    Generates a secure API key with the specified scopes and expiration.
    The full key is only returned once - store it securely!
    """
    # Generate the API key
    full_key, key_hash = ApiKey.generate_key()
    key_prefix = full_key[:8]
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        from datetime import timezone
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_in_days)
    
    # Convert scopes to string
    scopes_str = ",".join([scope.value for scope in key_data.scopes])
    
    # Create the API key record
    new_api_key = ApiKey(
        name=key_data.name,
        description=key_data.description,
        key_hash=key_hash,
        key_prefix=key_prefix,
        user_id=current_user.id,
        scopes=scopes_str,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(new_api_key)
    await db.commit()
    await db.refresh(new_api_key)
    
    # Prepare response
    key_info = ApiKeyResponse(
        id=new_api_key.id,
        name=new_api_key.name,
        description=new_api_key.description,
        key_prefix=new_api_key.key_prefix,
        scopes=new_api_key.get_scopes_list(),
        expires_at=new_api_key.expires_at,
        is_active=new_api_key.is_active,
        last_used_at=new_api_key.last_used_at,
        usage_count=new_api_key.usage_count,
        created_at=new_api_key.created_at,
        updated_at=new_api_key.updated_at
    )
    
    return ApiKeyCreateResponse(
        api_key=full_key,
        key_info=key_info
    )


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get details of a specific API key.
    
    Returns API key information (excluding the actual key value).
    """
    result = await db.execute(
        select(ApiKey)
        .where(and_(ApiKey.id == key_id, ApiKey.user_id == current_user.id))
    )
    
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        scopes=api_key.get_scopes_list(),
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: int,
    key_data: ApiKeyUpdate,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update an API key.
    
    Allows updating name, description, and active status.
    The actual key value and scopes cannot be changed.
    """
    result = await db.execute(
        select(ApiKey)
        .where(and_(ApiKey.id == key_id, ApiKey.user_id == current_user.id))
    )
    
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields
    if key_data.name is not None:
        api_key.name = key_data.name
    if key_data.description is not None:
        api_key.description = key_data.description
    if key_data.is_active is not None:
        api_key.is_active = key_data.is_active
    
    await db.commit()
    await db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        scopes=api_key.get_scopes_list(),
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete an API key.
    
    Permanently removes the API key. This action cannot be undone.
    """
    result = await db.execute(
        select(ApiKey)
        .where(and_(ApiKey.id == key_id, ApiKey.user_id == current_user.id))
    )
    
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    await db.delete(api_key)
    await db.commit()


@router.get("/stats/usage", response_model=ApiKeyUsageStats)
async def get_api_key_stats(
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get API key usage statistics for the current user.
    
    Returns statistics about the user's API keys including counts and usage patterns.
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.usage_count.desc())
    )
    
    api_keys = result.scalars().all()
    
    # Calculate statistics
    total_keys = len(api_keys)
    active_keys = sum(1 for key in api_keys if key.is_active and key.is_valid())
    from datetime import timezone
    now = datetime.now(timezone.utc)
    expired_keys = sum(1 for key in api_keys if key.expires_at and key.expires_at < now)
    
    # Find most used key
    most_used_key = None
    if api_keys and api_keys[0].usage_count > 0:
        most_used = api_keys[0]
        most_used_key = ApiKeyResponse(
            id=most_used.id,
            name=most_used.name,
            description=most_used.description,
            key_prefix=most_used.key_prefix,
            scopes=most_used.get_scopes_list(),
            expires_at=most_used.expires_at,
            is_active=most_used.is_active,
            last_used_at=most_used.last_used_at,
            usage_count=most_used.usage_count,
            created_at=most_used.created_at,
            updated_at=most_used.updated_at
        )
    
    # Recent usage (simplified for now)
    recent_usage = []
    for key in api_keys[:5]:  # Top 5 most used
        if key.last_used_at:
            recent_usage.append({
                "key_name": key.name,
                "last_used": key.last_used_at,
                "usage_count": key.usage_count
            })
    
    # Calculate requests today based on last_used_at timestamps
    from datetime import timezone, timedelta
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    requests_today = 0
    for key in api_keys:
        if key.last_used_at and key.last_used_at >= today_start:
            # This is a simplified calculation - in a real system you'd track individual requests
            # For now, we'll count keys that were used today as having at least 1 request
            requests_today += 1
    
    return ApiKeyUsageStats(
        total_keys=total_keys,
        active_keys=active_keys,
        expired_keys=expired_keys,
        most_used_key=most_used_key,
        recent_usage=recent_usage,
        total_requests=sum(key.usage_count for key in api_keys),
        requests_today=requests_today
    )
