"""
Task comment API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models.task_comment import TaskComment
from ..models.task import Task
from ..models.user import User
from ..models.board import Board
from ..models.column import Column
from ..schemas.task_comment import (
    TaskCommentCreate, 
    TaskCommentUpdate, 
    TaskCommentResponse,
    TaskCommentListResponse
)
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["task-comments"])


async def _can_access_task(db: AsyncSession, user: User, task_id: int) -> bool:
    """Check if user can access the task (owns the board)."""
    result = await db.execute(
        select(Task)
        .join(Column, Task.column_id == Column.id)
        .join(Board, Column.board_id == Board.id)
        .where(Task.id == task_id)
        .where(Board.owner_id == user.id)
    )
    return result.scalar_one_or_none() is not None


@router.get("/{task_id}/comments", response_model=TaskCommentListResponse)
async def get_task_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a task."""
    if not await _can_access_task(db, current_user, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = await db.execute(
        select(TaskComment)
        .where(TaskComment.task_id == task_id)
        .options(selectinload(TaskComment.author))
        .order_by(TaskComment.created_at.desc())
    )
    comments = result.scalars().all()
    
    # Convert to response format with author names
    comment_responses = []
    for comment in comments:
        comment_dict = {
            "id": comment.id,
            "content": comment.content,
            "task_id": comment.task_id,
            "author_id": comment.author_id,
            "author_name": comment.author.full_name or comment.author.username,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at
        }
        comment_responses.append(TaskCommentResponse(**comment_dict))
    
    return TaskCommentListResponse(
        comments=comment_responses,
        total=len(comment_responses)
    )


@router.post("/{task_id}/comments", response_model=TaskCommentResponse)
async def create_task_comment(
    task_id: int,
    comment_data: TaskCommentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a task."""
    if not await _can_access_task(db, current_user, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Ensure task_id matches URL parameter
    if comment_data.task_id != task_id:
        raise HTTPException(status_code=400, detail="Task ID mismatch")
    
    comment = TaskComment(
        content=comment_data.content,
        task_id=task_id,
        author_id=current_user.id
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Load author relationship for response
    await db.refresh(comment, ["author"])
    
    return TaskCommentResponse(
        id=comment.id,
        content=comment.content,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=comment.author.full_name or comment.author.username,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.put("/comments/{comment_id}", response_model=TaskCommentResponse)
async def update_task_comment(
    comment_id: int,
    comment_data: TaskCommentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update a task comment (only by the author)."""
    result = await db.execute(
        select(TaskComment)
        .where(TaskComment.id == comment_id)
        .options(selectinload(TaskComment.author))
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author of the comment
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    # Check if user can access the task
    if not await _can_access_task(db, current_user, comment.task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    comment.content = comment_data.content
    await db.commit()
    await db.refresh(comment)
    
    return TaskCommentResponse(
        id=comment.id,
        content=comment.content,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=comment.author.full_name or comment.author.username,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.delete("/comments/{comment_id}")
async def delete_task_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a task comment (only by the author)."""
    result = await db.execute(
        select(TaskComment)
        .where(TaskComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author of the comment
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    # Check if user can access the task
    if not await _can_access_task(db, current_user, comment.task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(comment)
    await db.commit()
    
    return {"message": "Comment deleted successfully"}
