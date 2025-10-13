# Simple Kanban Board - Project Rules

## Directory Structure

```
simple-kanban/
├── src/                          # Application source code
│   ├── api/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── projects.py           # Project management endpoints
│   │   ├── tasks.py              # Task management endpoints
│   │   ├── columns.py            # Column management endpoints
│   │   ├── stories.py            # User story endpoints
│   │   ├── epics.py              # Epic management endpoints
│   │   └── auth.py               # Authentication endpoints
│   ├── core/                     # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── security.py           # Authentication & authorization
│   │   ├── database.py           # Database connection & session
│   │   └── dependencies.py       # FastAPI dependencies
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── project.py            # Project model
│   │   ├── task.py               # Task model
│   │   ├── column.py             # Column model
│   │   ├── user_story.py         # User story model
│   │   ├── epic.py               # Epic model
│   │   └── user.py               # User model
│   ├── schemas/                  # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── project.py            # Project request/response schemas
│   │   ├── task.py               # Task schemas
│   │   ├── column.py             # Column schemas
│   │   ├── user_story.py         # User story schemas
│   │   ├── epic.py               # Epic schemas
│   │   └── user.py               # User schemas
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── project_service.py    # Project business logic
│   │   ├── task_service.py       # Task business logic
│   │   ├── story_service.py      # Story planning logic
│   │   └── analytics_service.py  # Analytics and reporting
│   ├── database/                 # Database management
│   │   ├── __init__.py
│   │   ├── migrations/           # Alembic migration files
│   │   ├── init.py               # Database initialization
│   │   └── seed.py               # Default data seeding
│   ├── static/                   # Static web assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/                # Jinja2 templates (if needed)
│   └── main.py                   # FastAPI application entry point
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/                     # Unit tests
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_schemas.py
│   ├── integration/              # Integration tests
│   │   ├── test_api.py
│   │   ├── test_database.py
│   │   └── test_auth.py
│   └── e2e/                      # End-to-end tests
│       └── test_workflows.py
├── helm/                         # Kubernetes deployment
│   └── simple-kanban/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-dev.yaml
│       ├── values-prod.yaml
│       └── templates/
├── docs/                         # Project documentation
├── alembic.ini                   # Database migration config
├── pyproject.toml                # Python dependencies & config
├── Dockerfile                    # Container build
├── skaffold.yaml                 # Development workflow (primary)
├── docker-compose.monitoring.yml # Optional monitoring stack
├── Makefile                      # Build automation
├── .gitignore
├── .dockerignore
└── README.md
```

## File Naming Conventions

### Python Files
- **Snake case**: `user_story.py`, `project_service.py`
- **Descriptive names**: Files should clearly indicate their purpose
- **Model files**: Singular nouns (`task.py`, not `tasks.py`)
- **Service files**: End with `_service.py`
- **API files**: Plural nouns for resource collections (`tasks.py`, `projects.py`)

### Database Migrations
- **Alembic format**: `YYYY_MM_DD_HHMM_description.py`
- **Descriptive**: `2025_08_24_2040_create_projects_table.py`

### Test Files
- **Prefix with `test_`**: `test_project_service.py`
- **Mirror source structure**: Test file location matches source file

### Configuration Files
- **Lowercase with hyphens**: `docker-compose.yml`, `skaffold.yaml`
- **Environment-specific**: `values-dev.yaml`, `values-prod.yaml`

## Coding Standards

### Python Code Style
```python
# Use Black formatting (88 character line length)
# Use type hints for all functions
from typing import List, Optional
from uuid import UUID

async def get_project_tasks(
    project_id: UUID,
    column_id: Optional[UUID] = None,
    limit: int = 100
) -> List[Task]:
    """Get tasks for a project with optional filtering."""
    pass

# Use Pydantic for data validation
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    column_id: UUID
    user_story_id: Optional[UUID] = None
    
    class Config:
        json_encoders = {UUID: str}
```

### Database Models
```python
# Use SQLAlchemy declarative base
# UUID primary keys for all tables
# Timestamps for audit trails
class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now()
    )
```

### API Design
```python
# Use FastAPI with proper HTTP status codes
# Consistent response schemas
# Proper error handling
@router.post("/", response_model=Task, status_code=201)
async def create_task(
    task_data: TaskCreate,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Task:
    """Create a new task in the project."""
    try:
        return await task_service.create_task(db, task_data, project_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Development Workflow Rules

### Git Workflow
```bash
# Feature branch naming
feature/kanban-api-endpoints
feature/user-authentication
feature/real-time-updates
bugfix/task-position-sorting
hotfix/security-vulnerability

# Commit message format
feat: add task drag-and-drop API endpoints
fix: resolve task position conflicts
docs: update API documentation
test: add integration tests for projects API
```

### Code Review Requirements
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Security scan clean (`make lint-security`)
- [ ] Code coverage > 80%
- [ ] API documentation updated
- [ ] Database migrations reviewed

### Testing Standards
```python
# Test file structure mirrors source
# Use pytest fixtures for common setup
# Test both success and error cases
@pytest.mark.asyncio
async def test_create_task_success(db_session, sample_project):
    """Test successful task creation."""
    task_data = TaskCreate(
        title="Test Task",
        description="Test Description",
        column_id=sample_project.default_column_id
    )
    
    result = await task_service.create_task(
        db_session, task_data, sample_project.id
    )
    
    assert result.title == "Test Task"
    assert result.project_id == sample_project.id

@pytest.mark.asyncio
async def test_create_task_invalid_column(db_session, sample_project):
    """Test task creation with invalid column."""
    task_data = TaskCreate(
        title="Test Task",
        column_id=uuid4()  # Non-existent column
    )
    
    with pytest.raises(ValidationError):
        await task_service.create_task(
            db_session, task_data, sample_project.id
        )
```

## Security Rules

### Authentication & Authorization
- **JWT tokens**: 15-minute access tokens, 7-day refresh tokens
- **Role-based access**: Admin, User, Viewer roles
- **API rate limiting**: 100 requests/minute per user
- **Input validation**: All user input validated with Pydantic

### Database Security
- **Connection pooling**: Max 20 connections
- **Prepared statements**: Use SQLAlchemy ORM (no raw SQL)
- **Migrations**: All schema changes via Alembic
- **Backups**: Daily automated PostgreSQL dumps

### Container Security
- **Non-root user**: UID/GID 1000:1000
- **Read-only filesystem**: Except for temp directories
- **Security scanning**: Checkov for infrastructure, Bandit for Python
- **Minimal base image**: Python 3.11-slim

## Performance Rules

### Database Optimization
- **Indexes**: On foreign keys and frequently queried columns
- **Connection pooling**: SQLAlchemy async pool
- **Query optimization**: Use select_related for joins
- **Pagination**: Default limit 100, max 1000

### Caching Strategy
- **Redis caching**: Session data, frequently accessed projects
- **Cache TTL**: 1 hour for project data, 15 minutes for user sessions
- **Cache invalidation**: On data updates

### API Performance
- **Response time**: < 200ms for CRUD operations
- **Pagination**: Required for list endpoints
- **Compression**: Gzip for responses > 1KB
- **Rate limiting**: Per-user and per-endpoint limits

## Documentation Rules

### Code Documentation
- **Docstrings**: All public functions and classes
- **Type hints**: Required for all function parameters and returns
- **Comments**: Explain complex business logic
- **README**: Keep updated with setup and usage instructions

### API Documentation
- **OpenAPI/Swagger**: Auto-generated from FastAPI
- **Examples**: Include request/response examples
- **Error codes**: Document all possible error responses
- **Authentication**: Document auth requirements

## Deployment Rules

### Environment Configuration
- **Environment variables**: All configuration via env vars
- **Secrets management**: Use Kubernetes secrets
- **Health checks**: Liveness and readiness probes
- **Resource limits**: CPU/memory limits defined

### Monitoring & Logging
- **Structured logging**: JSON format with correlation IDs
- **Metrics**: Prometheus metrics for API endpoints
- **Alerts**: Error rate > 5%, response time > 500ms
- **Tracing**: Request tracing for debugging

## Quality Gates

### Pre-commit Checks
```bash
make lint           # Black, Ruff, Pyright, security scans
make test           # Unit and integration tests
make test-coverage  # Ensure > 80% coverage
```

### Pre-deployment Checks
```bash
make deploy-dev     # Deploy to development
make test-e2e       # End-to-end tests
make security-scan  # Full security audit
```

### Production Deployment
- [ ] All tests pass in staging
- [ ] Performance tests completed
- [ ] Security review approved
- [ ] Database migration tested
- [ ] Rollback plan documented
