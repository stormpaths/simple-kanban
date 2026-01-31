"""
Task management API routes.

Provides CRUD operations for kanban board tasks.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db_session
from ..models import Task, Column, Board, User
from ..schemas import TaskCreate, TaskUpdate, TaskMove, TaskResponse
from ..auth.dependencies import get_current_user, get_user_from_api_key_or_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: Request,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Create a new task in a column."""
    try:
        user_id = current_user.id  # Get user ID early to avoid async issues
        logger.info(f"Creating task for user {user_id}: {task.dict()}")

        # Verify column exists
        result = await db.execute(select(Column).where(Column.id == task.column_id))
        column = result.scalar_one_or_none()
        if not column:
            logger.error(f"Column {task.column_id} not found for task creation")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
            )

        # If no position specified, add to end
        if task.position is None:
            result = await db.execute(
                select(Task).where(Task.column_id == task.column_id)
            )
            max_position = len(result.scalars().all())
            task.position = max_position

        db_task = Task(
            title=task.title,
            description=task.description,
            position=task.position,
            column_id=task.column_id,
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        logger.info(f"Successfully created task {db_task.id} for user {user_id}")
        return db_task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating task: {str(e)}", exc_info=True)
        logger.error(f"Task data: {task.dict()}")
        logger.error(f"User: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during task creation",
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Get a specific task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Update a task's title, description, or position within the same column."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Update fields if provided
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.position is not None:
        # Handle position changes within the same column
        old_position = task.position
        new_position = task_update.position

        if old_position != new_position:
            # Get all tasks in the same column
            result = await db.execute(
                select(Task)
                .where(Task.column_id == task.column_id, Task.id != task_id)
                .order_by(Task.position)
            )
            column_tasks = result.scalars().all()

            # Adjust positions of other tasks
            if new_position > old_position:
                # Moving down: shift tasks up
                for t in column_tasks:
                    if old_position < t.position <= new_position:
                        t.position -= 1
            else:
                # Moving up: shift tasks down
                for t in column_tasks:
                    if new_position <= t.position < old_position:
                        t.position += 1

            task.position = new_position

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: int,
    move_data: TaskMove,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Move a task to a different column and position."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Verify target column exists
    result = await db.execute(select(Column).where(Column.id == move_data.column_id))
    target_column = result.scalar_one_or_none()
    if not target_column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target column not found"
        )

    old_column_id = task.column_id
    old_position = task.position
    new_column_id = move_data.column_id
    new_position = move_data.position

    if old_column_id == new_column_id:
        # Moving within same column - use update_task logic
        if new_position != old_position:
            result = await db.execute(
                select(Task)
                .where(Task.column_id == old_column_id)
                .order_by(Task.position)
            )
            tasks = result.scalars().all()

            if new_position > old_position:
                for t in tasks:
                    if old_position < t.position <= new_position:
                        t.position -= 1
            else:
                for t in tasks:
                    if new_position <= t.position < old_position:
                        t.position += 1

            task.position = new_position
    else:
        # Moving between columns
        # Remove from old column - shift remaining tasks up
        result = await db.execute(
            select(Task).where(
                Task.column_id == old_column_id, Task.position > old_position
            )
        )
        old_tasks = result.scalars().all()
        for t in old_tasks:
            t.position -= 1

        # Add to new column - shift existing tasks down
        result = await db.execute(
            select(Task).where(
                Task.column_id == new_column_id, Task.position >= new_position
            )
        )
        new_tasks = result.scalars().all()
        for t in new_tasks:
            t.position += 1

        # Update task
        task.column_id = new_column_id
        task.position = new_position

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    column_id = task.column_id
    position = task.position

    # Delete the task
    await db.delete(task)

    # Shift remaining tasks up
    result = await db.execute(
        select(Task).where(Task.column_id == column_id, Task.position > position)
    )
    remaining_tasks = result.scalars().all()
    for t in remaining_tasks:
        t.position -= 1

    await db.commit()
