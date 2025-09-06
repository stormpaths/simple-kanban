"""
SQL utility functions with injection protection.

Provides safe database operations using SQLAlchemy's parameterized queries.
"""
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, insert, text
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select, Update, Delete, Insert


class SQLQueryBuilder:
    """
    Safe SQL query builder with injection protection.
    
    All queries use SQLAlchemy's parameterized queries to prevent SQL injection.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def select_one(
        self, 
        model_class, 
        where_conditions: Optional[Dict[str, Any]] = None,
        eager_load: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        Select a single record with optional eager loading.
        
        Args:
            model_class: SQLAlchemy model class
            where_conditions: Dictionary of field->value conditions
            eager_load: List of relationship names to eager load
            
        Returns:
            Single model instance or None
        """
        query = select(model_class)
        
        # Add where conditions safely
        if where_conditions:
            for field, value in where_conditions.items():
                if hasattr(model_class, field):
                    query = query.where(getattr(model_class, field) == value)
        
        # Add eager loading
        if eager_load:
            for relationship in eager_load:
                if hasattr(model_class, relationship):
                    query = query.options(selectinload(getattr(model_class, relationship)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def select_many(
        self, 
        model_class, 
        where_conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        eager_load: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Select multiple records with optional filtering, ordering, and eager loading.
        
        Args:
            model_class: SQLAlchemy model class
            where_conditions: Dictionary of field->value conditions
            order_by: Field name to order by
            limit: Maximum number of records to return
            eager_load: List of relationship names to eager load
            
        Returns:
            List of model instances
        """
        query = select(model_class)
        
        # Add where conditions safely
        if where_conditions:
            for field, value in where_conditions.items():
                if hasattr(model_class, field):
                    if isinstance(value, list):
                        # Handle IN queries
                        query = query.where(getattr(model_class, field).in_(value))
                    else:
                        query = query.where(getattr(model_class, field) == value)
        
        # Add ordering
        if order_by and hasattr(model_class, order_by):
            query = query.order_by(getattr(model_class, order_by))
        
        # Add limit
        if limit:
            query = query.limit(limit)
        
        # Add eager loading
        if eager_load:
            for relationship in eager_load:
                if hasattr(model_class, relationship):
                    query = query.options(selectinload(getattr(model_class, relationship)))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def insert_one(
        self, 
        model_class, 
        data: Dict[str, Any]
    ) -> Any:
        """
        Insert a single record safely.
        
        Args:
            model_class: SQLAlchemy model class
            data: Dictionary of field->value data
            
        Returns:
            Created model instance
        """
        # Filter data to only include valid model fields
        valid_fields = {
            key: value for key, value in data.items() 
            if hasattr(model_class, key)
        }
        
        instance = model_class(**valid_fields)
        self.session.add(instance)
        await self.session.flush()  # Get the ID without committing
        await self.session.refresh(instance)
        return instance
    
    async def update_one(
        self, 
        model_class, 
        where_conditions: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a single record safely.
        
        Args:
            model_class: SQLAlchemy model class
            where_conditions: Dictionary of field->value conditions for WHERE clause
            update_data: Dictionary of field->value data to update
            
        Returns:
            True if record was updated, False otherwise
        """
        query = update(model_class)
        
        # Add where conditions safely
        for field, value in where_conditions.items():
            if hasattr(model_class, field):
                query = query.where(getattr(model_class, field) == value)
        
        # Filter update data to only include valid model fields
        valid_updates = {
            key: value for key, value in update_data.items() 
            if hasattr(model_class, key)
        }
        
        query = query.values(**valid_updates)
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def delete_one(
        self, 
        model_class, 
        where_conditions: Dict[str, Any]
    ) -> bool:
        """
        Delete a single record safely.
        
        Args:
            model_class: SQLAlchemy model class
            where_conditions: Dictionary of field->value conditions for WHERE clause
            
        Returns:
            True if record was deleted, False otherwise
        """
        query = delete(model_class)
        
        # Add where conditions safely
        for field, value in where_conditions.items():
            if hasattr(model_class, field):
                query = query.where(getattr(model_class, field) == value)
        
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def execute_raw_query(
        self, 
        query_text: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a raw SQL query with parameter binding for injection protection.
        
        Args:
            query_text: SQL query string with named parameters (:param_name)
            parameters: Dictionary of parameter values
            
        Returns:
            Query result
        """
        query = text(query_text)
        result = await self.session.execute(query, parameters or {})
        return result
    
    async def commit(self):
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        await self.session.rollback()


def get_sql_builder(session: AsyncSession) -> SQLQueryBuilder:
    """
    Factory function to create a SQL query builder instance.
    
    Args:
        session: AsyncSession instance
        
    Returns:
        SQLQueryBuilder instance
    """
    return SQLQueryBuilder(session)
