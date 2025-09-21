"""
FastAPI application entry point for simple-kanban.

This module provides the main FastAPI application with health checks,
basic routing, and error handling.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from .schemas import HealthResponse, MessageRequest, MessageResponse
from .core.config import settings
from .middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    CSRFProtectionMiddleware,
    setup_redis_client
)
from typing import Dict, Any
import logging
import os

from .database import create_tables
from .migrations.group_migration import run_group_migrations
from .api import boards, columns, tasks, auth, oidc, task_comments, admin, groups

# Configure logging
log_level = logging.DEBUG if settings.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Simple Kanban Board",
    description="Self-hosted kanban board with drag-and-drop functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add exception handler for validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed logging."""
    logger.error(f"422 Validation error on {request.method} {request.url}")
    
    # Get request body for debugging
    try:
        body = await request.body()
        if body:
            logger.error(f"Request body: {body.decode('utf-8')}")
        else:
            logger.error("Request body: empty")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")
    
    # Log headers for debugging auth issues
    logger.error(f"Request headers: {dict(request.headers)}")
    
    # Log detailed validation errors
    logger.error(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Setup Redis client for rate limiting
redis_client = setup_redis_client()

# Add security middleware (order matters - add from innermost to outermost)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(oidc.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(boards.router, prefix="/api")
app.include_router(columns.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(task_comments.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and run migrations on startup."""
    logger.info("Creating database tables...")
    create_tables()
    logger.info("Database tables created successfully")
    
    logger.info("Running group management migrations...")
    run_group_migrations()
    logger.info("Group management migrations completed")


@app.get("/")
async def root():
    """Serve the main kanban board interface."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "message": "simple-kanban API",
            "status": "running",
            "docs": "/docs"
        }

@app.get("/admin")
async def admin_panel():
    """Serve the admin panel interface."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    admin_path = os.path.join(static_dir, "admin.html")
    
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    else:
        return {"error": "Admin panel not found"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )

@app.post("/echo", response_model=MessageResponse)
async def echo_message(request: MessageRequest):
    """Echo endpoint for testing API functionality."""
    logger.info(f"Received message: {request.message}")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    return MessageResponse(
        echo=request.message,
        length=len(request.message)
    )

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    return {
        "requests_total": 0,  # Implement proper metrics collection
        "uptime_seconds": 0,
        "memory_usage_mb": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
