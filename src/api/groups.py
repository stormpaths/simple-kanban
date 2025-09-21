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
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/", response_model=List[GroupListResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new group.
    
    The current user becomes the owner of the newly created group.
    """
    # Create the group
    new_group = Group(
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id
    )
    
    db.add(new_group)
    await db.flush()  # Get the group ID
    
    # Add creator as owner
    membership = UserGroup(
        user_id=current_user.id,
        group_id=new_group.id,
        role=ModelGroupRole.OWNER
    )
    
    db.add(membership)
    await db.commit()
    
    # Refresh to get relationships
    await db.refresh(new_group, ["members"])
    
    return GroupResponse(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        created_by=new_group.created_by,
        created_at=new_group.created_at,
        updated_at=new_group.updated_at,
        members=[],
        member_count=1
    )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update group information.
    
    Only accessible to group admins and owners.
    """
    # Check if user has admin/owner permissions
    membership_result = await db.execute(
        select(UserGroup)
        .where(and_(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id,
            UserGroup.role.in_([ModelGroupRole.ADMIN, ModelGroupRole.OWNER])
        ))
    )
    
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this group"
        )
    
    # Get and update group
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Update fields
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    
    await db.commit()
    await db.refresh(group, ["members"])
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=[],
        member_count=len(group.members)
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a group.
    
    Only accessible to group owners.
    """
    # Check if user is owner
    membership_result = await db.execute(
        select(UserGroup)
        .where(and_(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id,
            UserGroup.role == ModelGroupRole.OWNER
        ))
    )
    
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this group"
        )
    
    # Get and delete group
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    await db.delete(group)
    await db.commit()


@router.post("/{group_id}/members", response_model=GroupMembershipResponse)
async def add_group_member(
    group_id: int,
    membership_request: GroupMembershipRequest,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
