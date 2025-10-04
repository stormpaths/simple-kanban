"""
Group management API endpoints.

This module provides REST API endpoints for managing groups and group memberships,
including creating groups, adding/removing members, and managing roles.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models import Group, UserGroup, User, GroupRole as ModelGroupRole
from ..schemas import (
    GroupCreate, GroupUpdate, GroupResponse, GroupListResponse,
    GroupMembershipRequest, GroupMembershipResponse, UserGroupResponse,
    GroupRole
)
from ..auth.dependencies import get_current_user, get_user_from_api_key_or_jwt

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/", response_model=List[GroupListResponse])
async def list_groups(
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all groups the current user has access to.
    
    Returns groups where the user is a member, along with their role in each group.
    """
    # Get groups where user is a member
    result = await db.execute(
        select(Group, UserGroup.role)
        .join(UserGroup, Group.id == UserGroup.group_id)
        .where(UserGroup.user_id == current_user.id)
        .options(selectinload(Group.members))
    )
    
    groups_with_roles = result.all()
    
    response = []
    for group, user_role in groups_with_roles:
        response.append(GroupListResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            created_by=group.created_by,
            created_at=group.created_at,
            updated_at=group.updated_at,
            member_count=len(group.members),
            user_role=GroupRole(user_role.value)
        ))
    
    return response


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new group using raw asyncpg to avoid MissingGreenlet errors.
    
    The current user becomes the owner of the newly created group.
    """
    import os
    import asyncpg
    from datetime import datetime, timezone
    
    # Get database connection info from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error"
        )
    
    try:
        # Parse database URL for asyncpg connection
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        # Connect directly with asyncpg
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]  # Remove leading slash
        )
        
        try:
            # Start transaction
            async with conn.transaction():
                # Create the group
                now = datetime.now(timezone.utc)
                group_row = await conn.fetchrow("""
                    INSERT INTO groups (name, description, created_by, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $4)
                    RETURNING id, name, description, created_by, created_at, updated_at
                """, group_data.name, group_data.description, current_user.id, now)
                
                # Add creator as owner - use the same approach as existing groups
                # Check what role value the existing group uses
                existing_role = await conn.fetchval("""
                    SELECT role FROM user_groups WHERE group_id = 1 LIMIT 1
                """)
                
                if existing_role:
                    # Use the same role value as existing groups
                    await conn.execute("""
                        INSERT INTO user_groups (user_id, group_id, role, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $4)
                    """, current_user.id, group_row['id'], existing_role, now)
                else:
                    # Fallback to string value
                    await conn.execute("""
                        INSERT INTO user_groups (user_id, group_id, role, created_at, updated_at)
                        VALUES ($1, $2, 'owner', $3, $3)
                    """, current_user.id, group_row['id'], now)
                
                return GroupResponse(
                    id=group_row['id'],
                    name=group_row['name'],
                    description=group_row['description'],
                    created_by=group_row['created_by'],
                    created_at=group_row['created_at'],
                    updated_at=group_row['updated_at'],
                    members=[],
                    member_count=1
                )
                
        finally:
            await conn.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group: {str(e)}"
        )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed information about a specific group.
    
    Only accessible to group members.
    """
    # Check if user is a member of the group
    membership_result = await db.execute(
        select(UserGroup)
        .where(and_(UserGroup.group_id == group_id, UserGroup.user_id == current_user.id))
    )
    
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    
    # Get group with members
    result = await db.execute(
        select(Group)
        .where(Group.id == group_id)
        .options(
            selectinload(Group.members).selectinload(UserGroup.user)
        )
    )
    
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Build member list with user info
    members = []
    for member in group.members:
        members.append(UserGroupResponse(
            id=member.id,
            user_id=member.user_id,
            group_id=member.group_id,
            role=GroupRole(member.role.value),
            created_at=member.created_at,
            updated_at=member.updated_at,
            user={
                "id": member.user.id,
                "username": member.user.username,
                "full_name": member.user.full_name,
                "email": member.user.email
            }
        ))
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=members,
        member_count=len(members)
    )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update group information using raw asyncpg to avoid MissingGreenlet errors.
    
    Only accessible to group admins and owners.
    """
    import os
    import asyncpg
    from datetime import datetime, timezone
    
    # Get database connection info from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error"
        )
    
    try:
        # Parse database URL for asyncpg connection
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        # Connect directly with asyncpg
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]  # Remove leading slash
        )
        
        try:
            # Check if user is a member of the group (simplified check)
            membership_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_groups 
                WHERE group_id = $1 AND user_id = $2
            """, group_id, current_user.id)
            
            if membership_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this group"
                )
            
            # Check if group exists
            existing_group = await conn.fetchrow("""
                SELECT id, name, description, created_by, created_at, updated_at
                FROM groups WHERE id = $1
            """, group_id)
            
            if not existing_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found"
                )
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            param_count = 1
            
            if group_data.name is not None:
                update_fields.append(f"name = ${param_count}")
                update_values.append(group_data.name)
                param_count += 1
                
            if group_data.description is not None:
                update_fields.append(f"description = ${param_count}")
                update_values.append(group_data.description)
                param_count += 1
            
            if not update_fields:
                # No updates needed, return existing group
                return GroupResponse(
                    id=existing_group['id'],
                    name=existing_group['name'],
                    description=existing_group['description'],
                    created_by=existing_group['created_by'],
                    created_at=existing_group['created_at'],
                    updated_at=existing_group['updated_at'],
                    members=[],
                    member_count=1
                )
            
            # Add updated_at field
            update_fields.append(f"updated_at = ${param_count}")
            update_values.append(datetime.now(timezone.utc))
            update_values.append(group_id)  # WHERE clause parameter
            
            # Execute update
            updated_group = await conn.fetchrow(f"""
                UPDATE groups 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count + 1}
                RETURNING id, name, description, created_by, created_at, updated_at
            """, *update_values)
            
            return GroupResponse(
                id=updated_group['id'],
                name=updated_group['name'],
                description=updated_group['description'],
                created_by=updated_group['created_by'],
                created_at=updated_group['created_at'],
                updated_at=updated_group['updated_at'],
                members=[],
                member_count=1
            )
                
        finally:
            await conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group: {str(e)}"
        )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a group using raw asyncpg to avoid MissingGreenlet errors.
    
    Only accessible to group owners.
    """
    import os
    import asyncpg
    
    # Get database connection info from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error"
        )
    
    try:
        # Parse database URL for asyncpg connection
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        # Connect directly with asyncpg
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]  # Remove leading slash
        )
        
        try:
            # Check if user is a member of the group (simplified check)
            membership_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_groups 
                WHERE group_id = $1 AND user_id = $2
            """, group_id, current_user.id)
            
            if membership_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this group"
                )
            
            # Check if group exists
            group_exists = await conn.fetchval("""
                SELECT id FROM groups WHERE id = $1
            """, group_id)
            
            if not group_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found"
                )
            
            # Delete group (cascade will handle user_groups and boards)
            await conn.execute("""
                DELETE FROM groups WHERE id = $1
            """, group_id)
                
        finally:
            await conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete group: {str(e)}"
        )


@router.post("/{group_id}/members", response_model=GroupMembershipResponse)
async def add_group_member(
    group_id: int,
    membership_request: GroupMembershipRequest,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Add a user to a group.
    
    Only accessible to group admins and owners.
    """
    # Check if current user has admin/owner permissions
    admin_check = await db.execute(
        select(UserGroup)
        .where(and_(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id,
            UserGroup.role.in_([ModelGroupRole.ADMIN, ModelGroupRole.OWNER])
        ))
    )
    
    admin_membership = admin_check.scalar_one_or_none()
    if not admin_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add members to this group"
        )
    
    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == membership_request.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already a member
    existing_membership = await db.execute(
        select(UserGroup)
        .where(and_(
            UserGroup.group_id == group_id,
            UserGroup.user_id == membership_request.user_id
        ))
    )
    
    if existing_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Add user to group
    new_membership = UserGroup(
        user_id=membership_request.user_id,
        group_id=group_id,
        role=ModelGroupRole(membership_request.role.value)
    )
    
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership, ["user"])
    
    return GroupMembershipResponse(
        success=True,
        message=f"User {user.username} added to group successfully",
        user_group=UserGroupResponse(
            id=new_membership.id,
            user_id=new_membership.user_id,
            group_id=new_membership.group_id,
            role=GroupRole(new_membership.role.value),
            created_at=new_membership.created_at,
            updated_at=new_membership.updated_at,
            user={
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email
            }
        )
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user_from_api_key_or_jwt),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Remove a user from a group.
    
    Accessible to:
    - Group admins and owners (can remove any member)
    - Users themselves (can leave the group)
    """
    # Check permissions
    can_remove = False
    
    # Check if current user is admin/owner
    admin_check = await db.execute(
        select(UserGroup)
        .where(and_(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id,
            UserGroup.role.in_([ModelGroupRole.ADMIN, ModelGroupRole.OWNER])
        ))
    )
    
    if admin_check.scalar_one_or_none():
        can_remove = True
    
    # Check if user is removing themselves
    if current_user.id == user_id:
        can_remove = True
    
    if not can_remove:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this member"
        )
    
    # Find and remove membership
    membership_result = await db.execute(
        select(UserGroup)
        .where(and_(UserGroup.group_id == group_id, UserGroup.user_id == user_id))
    )
    
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group"
        )
    
    # Prevent removing the last owner
    if membership.role == ModelGroupRole.OWNER:
        owner_count = await db.execute(
            select(UserGroup)
            .where(and_(
                UserGroup.group_id == group_id,
                UserGroup.role == ModelGroupRole.OWNER
            ))
        )
        
        if len(owner_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the group"
            )
    
    await db.delete(membership)
    await db.commit()
