"""
Task management API routes.

Provides CRUD operations for kanban board tasks.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, Column, Board
from ..schemas import TaskCreate, TaskUpdate, TaskMove, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])




@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task in a column."""
    # Verify column exists
    column = db.query(Column).filter(Column.id == task.column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found"
        )
    
    # If no position specified, add to end
    if task.position is None:
        max_position = db.query(Task).filter(Task.column_id == task.column_id).count()
        task.position = max_position
    
    db_task = Task(
        title=task.title,
        description=task.description,
        position=task.position,
        column_id=task.column_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task's title, description, or position within the same column."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    old_position = task.position
    column_id = task.column_id
    
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    
    # Handle position change within same column
    if task_update.position is not None and task_update.position != old_position:
        # Get all tasks in the column
        tasks = db.query(Task).filter(Task.column_id == column_id).order_by(Task.position).all()
        
        # Update positions
        new_position = task_update.position
        if new_position > old_position:
            # Moving down - shift tasks up
            for t in tasks:
                if old_position < t.position <= new_position:
                    t.position -= 1
        else:
            # Moving up - shift tasks down
            for t in tasks:
                if new_position <= t.position < old_position:
                    t.position += 1
        
        task.position = new_position
    
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: int,
    move_data: TaskMove,
    db: Session = Depends(get_db)
):
    """Move a task to a different column and position."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify target column exists
    target_column = db.query(Column).filter(Column.id == move_data.column_id).first()
    if not target_column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target column not found"
        )
    
    old_column_id = task.column_id
    old_position = task.position
    new_column_id = move_data.column_id
    new_position = move_data.position
    
    if old_column_id == new_column_id:
        # Moving within same column - use update_task logic
        if new_position != old_position:
            tasks = db.query(Task).filter(Task.column_id == old_column_id).order_by(Task.position).all()
            
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
        old_tasks = db.query(Task).filter(
            Task.column_id == old_column_id,
            Task.position > old_position
        ).all()
        for t in old_tasks:
            t.position -= 1
        
        # Add to new column - shift existing tasks down
        new_tasks = db.query(Task).filter(
            Task.column_id == new_column_id,
            Task.position >= new_position
        ).all()
        for t in new_tasks:
            t.position += 1
        
        # Update task
        task.column_id = new_column_id
        task.position = new_position
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    column_id = task.column_id
    position = task.position
    
    # Delete the task
    db.delete(task)
    
    # Shift remaining tasks up
    remaining_tasks = db.query(Task).filter(
        Task.column_id == column_id,
        Task.position > position
    ).all()
    for t in remaining_tasks:
        t.position -= 1
    
    db.commit()
