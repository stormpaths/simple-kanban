"""
FastAPI application entry point for simple-kanban.

This module provides the main FastAPI application with health checks,
basic routing, and error handling.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .schemas import HealthResponse, MessageRequest, MessageResponse
from typing import Dict, Any
import logging
import os

from .database import create_tables
from .api import boards, columns, tasks, auth, oidc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Simple Kanban Board",
    description="Self-hosted kanban board with drag-and-drop functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(oidc.router, prefix="/api")
app.include_router(boards.router, prefix="/api")
app.include_router(columns.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    logger.info("Creating database tables...")
    create_tables()
    logger.info("Database tables created successfully")


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
