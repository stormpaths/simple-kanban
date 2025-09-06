"""
Database model and relationship tests for Simple Kanban Board.

Tests SQLAlchemy models, relationships, constraints, and database operations.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.database import Base
from src.models.user import User
from src.models.board import Board
from src.models.column import Column
from src.models.task import Task


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_database.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def setup_database():
    """Setup test database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user():
    """Create a test user."""
    async with TestSessionLocal() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        user.set_password("testpassword123")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def test_board(test_user):
    """Create a test board."""
    async with TestSessionLocal() as session:
        board = Board(
            name="Test Board",
            description="A test board",
            owner_id=test_user.id
        )
        session.add(board)
        await session.commit()
        await session.refresh(board)
        return board


class TestUserModel:
    """Test User model functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, setup_database):
        """Test creating a new user."""
        async with TestSessionLocal() as session:
            user = User(
                username="newuser",
                email="newuser@example.com",
                full_name="New User"
            )
            user.set_password("password123")
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            assert user.id is not None
            assert user.username == "newuser"
            assert user.email == "newuser@example.com"
            assert user.full_name == "New User"
            assert user.is_active is True
            assert user.is_admin is False
            assert user.is_verified is False
            assert user.hashed_password is not None
    
    @pytest.mark.asyncio
    async def test_user_unique_constraints(self, setup_database):
        """Test that username and email must be unique."""
        async with TestSessionLocal() as session:
            # Create first user
            user1 = User(username="testuser", email="test@example.com")
            session.add(user1)
            await session.commit()
            
            # Try to create user with same username
            user2 = User(username="testuser", email="different@example.com")
            session.add(user2)
            
            with pytest.raises(IntegrityError):
                await session.commit()
        
        # Reset session for email test
        async with TestSessionLocal() as session:
            # Create first user
            user1 = User(username="testuser1", email="test@example.com")
            session.add(user1)
            await session.commit()
            
            # Try to create user with same email
            user2 = User(username="testuser2", email="test@example.com")
            session.add(user2)
            
            with pytest.raises(IntegrityError):
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_user_password_methods(self, setup_database):
        """Test password hashing and verification methods."""
        async with TestSessionLocal() as session:
            user = User(username="testuser", email="test@example.com")
            password = "securepassword123"
            
            # Test password setting
            user.set_password(password)
            assert user.hashed_password is not None
            assert user.hashed_password != password
            
            # Test password verification
            assert user.verify_password(password) is True
            assert user.verify_password("wrongpassword") is False
            
            # Test class method
            hashed = User.hash_password(password)
            assert hashed != password
            assert len(hashed) > 50


class TestBoardModel:
    """Test Board model functionality."""
    
    @pytest.mark.asyncio
    async def test_create_board(self, setup_database, test_user):
        """Test creating a new board."""
        async with TestSessionLocal() as session:
            board = Board(
                name="My Board",
                description="A test board",
                owner_id=test_user.id
            )
            
            session.add(board)
            await session.commit()
            await session.refresh(board)
            
            assert board.id is not None
            assert board.name == "My Board"
            assert board.description == "A test board"
            assert board.owner_id == test_user.id
            assert board.created_at is not None
            assert board.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_board_owner_relationship(self, setup_database, test_user):
        """Test board-owner relationship."""
        async with TestSessionLocal() as session:
            board = Board(
                name="Test Board",
                description="Test",
                owner_id=test_user.id
            )
            session.add(board)
            await session.commit()
            
            # Test relationship loading
            result = await session.execute(
                select(Board).where(Board.id == board.id)
            )
            loaded_board = result.scalar_one()
            
            # Load owner relationship
            await session.refresh(loaded_board, ["owner"])
            assert loaded_board.owner.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_board_cascade_delete(self, setup_database, test_user):
        """Test that deleting a user cascades to boards."""
        async with TestSessionLocal() as session:
            # Create board
            board = Board(
                name="Test Board",
                description="Test",
                owner_id=test_user.id
            )
            session.add(board)
            await session.commit()
            board_id = board.id
            
            # Delete user
            await session.delete(test_user)
            await session.commit()
            
            # Check that board is also deleted
            result = await session.execute(
                select(Board).where(Board.id == board_id)
            )
            assert result.scalar_one_or_none() is None


class TestColumnModel:
    """Test Column model functionality."""
    
    @pytest.mark.asyncio
    async def test_create_column(self, setup_database, test_board):
        """Test creating a new column."""
        async with TestSessionLocal() as session:
            column = Column(
                name="To Do",
                position=1,
                board_id=test_board.id
            )
            
            session.add(column)
            await session.commit()
            await session.refresh(column)
            
            assert column.id is not None
            assert column.name == "To Do"
            assert column.position == 1
            assert column.board_id == test_board.id
            assert column.created_at is not None
            assert column.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_column_board_relationship(self, setup_database, test_board):
        """Test column-board relationship."""
        async with TestSessionLocal() as session:
            column = Column(
                name="Test Column",
                position=1,
                board_id=test_board.id
            )
            session.add(column)
            await session.commit()
            
            # Test relationship loading
            result = await session.execute(
                select(Column).where(Column.id == column.id)
            )
            loaded_column = result.scalar_one()
            
            # Load board relationship
            await session.refresh(loaded_column, ["board"])
            assert loaded_column.board.name == test_board.name
    
    @pytest.mark.asyncio
    async def test_column_position_constraint(self, setup_database, test_board):
        """Test that column positions must be unique within a board."""
        async with TestSessionLocal() as session:
            # Create first column
            column1 = Column(name="Column 1", position=1, board_id=test_board.id)
            session.add(column1)
            await session.commit()
            
            # Try to create column with same position
            column2 = Column(name="Column 2", position=1, board_id=test_board.id)
            session.add(column2)
            
            with pytest.raises(IntegrityError):
                await session.commit()


class TestTaskModel:
    """Test Task model functionality."""
    
    @pytest.mark.asyncio
    async def test_create_task(self, setup_database, test_board):
        """Test creating a new task."""
        async with TestSessionLocal() as session:
            # First create a column
            column = Column(name="To Do", position=1, board_id=test_board.id)
            session.add(column)
            await session.commit()
            await session.refresh(column)
            
            # Create task
            task = Task(
                title="Test Task",
                description="A test task",
                position=1,
                column_id=column.id
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            assert task.id is not None
            assert task.title == "Test Task"
            assert task.description == "A test task"
            assert task.position == 1
            assert task.column_id == column.id
            assert task.created_at is not None
            assert task.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_task_column_relationship(self, setup_database, test_board):
        """Test task-column relationship."""
        async with TestSessionLocal() as session:
            # Create column and task
            column = Column(name="Test Column", position=1, board_id=test_board.id)
            session.add(column)
            await session.commit()
            await session.refresh(column)
            
            task = Task(
                title="Test Task",
                description="Test",
                position=1,
                column_id=column.id
            )
            session.add(task)
            await session.commit()
            
            # Test relationship loading
            result = await session.execute(
                select(Task).where(Task.id == task.id)
            )
            loaded_task = result.scalar_one()
            
            # Load column relationship
            await session.refresh(loaded_task, ["column"])
            assert loaded_task.column.name == column.name
    
    @pytest.mark.asyncio
    async def test_task_position_constraint(self, setup_database, test_board):
        """Test that task positions must be unique within a column."""
        async with TestSessionLocal() as session:
            # Create column
            column = Column(name="Test Column", position=1, board_id=test_board.id)
            session.add(column)
            await session.commit()
            await session.refresh(column)
            
            # Create first task
            task1 = Task(title="Task 1", position=1, column_id=column.id)
            session.add(task1)
            await session.commit()
            
            # Try to create task with same position in same column
            task2 = Task(title="Task 2", position=1, column_id=column.id)
            session.add(task2)
            
            with pytest.raises(IntegrityError):
                await session.commit()


class TestComplexRelationships:
    """Test complex model relationships and queries."""
    
    @pytest.mark.asyncio
    async def test_full_board_structure(self, setup_database, test_user):
        """Test creating a complete board structure with relationships."""
        async with TestSessionLocal() as session:
            # Create board
            board = Board(
                name="Complete Board",
                description="A complete test board",
                owner_id=test_user.id
            )
            session.add(board)
            await session.commit()
            await session.refresh(board)
            
            # Create columns
            columns = []
            for i, name in enumerate(["To Do", "In Progress", "Done"], 1):
                column = Column(name=name, position=i, board_id=board.id)
                session.add(column)
                columns.append(column)
            
            await session.commit()
            for column in columns:
                await session.refresh(column)
            
            # Create tasks
            tasks = []
            for i, column in enumerate(columns):
                for j in range(2):  # 2 tasks per column
                    task = Task(
                        title=f"Task {i+1}.{j+1}",
                        description=f"Description for task {i+1}.{j+1}",
                        position=j+1,
                        column_id=column.id
                    )
                    session.add(task)
                    tasks.append(task)
            
            await session.commit()
            
            # Verify structure
            assert len(columns) == 3
            assert len(tasks) == 6
            
            # Test eager loading
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Board)
                .where(Board.id == board.id)
                .options(
                    selectinload(Board.columns)
                    .selectinload(Column.tasks)
                )
            )
            loaded_board = result.scalar_one()
            
            assert len(loaded_board.columns) == 3
            for column in loaded_board.columns:
                assert len(column.tasks) == 2
    
    @pytest.mark.asyncio
    async def test_cascade_deletes(self, setup_database, test_user):
        """Test that cascade deletes work properly."""
        async with TestSessionLocal() as session:
            # Create complete structure
            board = Board(name="Test Board", owner_id=test_user.id)
            session.add(board)
            await session.commit()
            await session.refresh(board)
            
            column = Column(name="Test Column", position=1, board_id=board.id)
            session.add(column)
            await session.commit()
            await session.refresh(column)
            
            task = Task(title="Test Task", position=1, column_id=column.id)
            session.add(task)
            await session.commit()
            task_id = task.id
            column_id = column.id
            
            # Delete board - should cascade to column and task
            await session.delete(board)
            await session.commit()
            
            # Verify cascade deletion
            result = await session.execute(select(Column).where(Column.id == column_id))
            assert result.scalar_one_or_none() is None
            
            result = await session.execute(select(Task).where(Task.id == task_id))
            assert result.scalar_one_or_none() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
