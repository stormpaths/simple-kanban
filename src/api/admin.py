"""
Admin API endpoints for user management.

Provides administrative functionality for managing users, including:
- Viewing user statistics (total users, boards, tasks)
- Enabling/disabling user accounts
- Granting/revoking admin privileges
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..models.board import Board
from ..models.column import Column
from ..models.task import Task
from ..schemas.admin import UserStatsResponse, UserUpdateRequest

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the current user is an admin.
    Initially allows user ID 1, later will check is_admin flag.
    """
    # For now, only allow user ID 1 (the initial admin)
    # Later this will be expanded to check is_admin flag
    if current_user.id != 1 and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=List[UserStatsResponse])
async def get_all_users_with_stats(
    db: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(get_admin_user)
):
    """
    Get all users with their statistics (board count, task count).
    Only accessible by admin users.
    """
    # Query users with their boards and tasks for statistics
    result = await db.execute(
        select(User)
        .options(selectinload(User.boards).selectinload(Board.columns).selectinload(Column.tasks))
        .order_by(User.id)
    )
    users = result.scalars().all()
    
    user_stats = []
    for user in users:
        # Count boards owned by user
        board_count = len(user.boards)
        
        # Count tasks across all user's boards
        task_count = 0
        for board in user.boards:
            for column in board.columns:
                task_count += len(column.tasks)
        
        user_stats.append(UserStatsResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_verified=user.is_verified,
            created_at=user.created_at,
            board_count=board_count,
            task_count=task_count
        ))
    
    return user_stats


@router.get("/stats", response_model=Dict[str, Any])
async def get_admin_stats(
    db: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(get_admin_user)
):
    """
    Get overall system statistics.
    Only accessible by admin users.
    """
    # Get total counts
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()
    
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar()
    
    total_boards_result = await db.execute(select(func.count(Board.id)))
    total_boards = total_boards_result.scalar()
    
    total_tasks_result = await db.execute(select(func.count(Task.id)))
    total_tasks = total_tasks_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "total_boards": total_boards,
        "total_tasks": total_tasks
    }


@router.patch("/users/{user_id}", response_model=UserStatsResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(get_admin_user)
):
    """
    Update user properties (active status, admin status).
    Only accessible by admin users.
    """
    # Get the user to update
    result = await db.execute(
        select(User)
        .options(selectinload(User.boards).selectinload(Board.columns).selectinload(Column.tasks))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from disabling themselves
    if user_id == admin_user.id and update_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )
    
    # Prevent admin from removing their own admin status if they're the only admin
    if (user_id == admin_user.id and 
        update_data.is_admin is False and 
        user.is_admin):
        # Check if there are other admins
        other_admins_result = await db.execute(
            select(func.count(User.id)).where(
                User.is_admin == True,
                User.id != user_id,
                User.is_active == True
            )
        )
        other_admins_count = other_admins_result.scalar()
        
        if other_admins_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin status - you are the only active admin"
            )
    
    # Update user properties
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    
    if update_data.is_admin is not None:
        user.is_admin = update_data.is_admin
    
    await db.commit()
    await db.refresh(user)
    
    # Calculate statistics for response
    board_count = len(user.boards)
    task_count = 0
    for board in user.boards:
        for column in board.columns:
            task_count += len(column.tasks)
    
    return UserStatsResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_verified=user.is_verified,
        created_at=user.created_at,
        board_count=board_count,
        task_count=task_count
    )
