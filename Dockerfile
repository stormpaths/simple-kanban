# ============================================================================
# Base stage - shared dependencies
# ============================================================================
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Test stage - for running tests
# ============================================================================
FROM base AS test

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    httpx

# Copy application code
COPY . .

# Run tests by default
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]

# ============================================================================
# Production stage - final image
# ============================================================================
FROM base AS production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set production environment variables
ENV OTEL_SERVICE_NAME=simple-kanban \
    OTEL_SERVICE_VERSION=1.0.0 \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Copy application code
COPY --chown=appuser:appuser . .

# Make startup script executable
RUN chmod +x scripts/startup.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application with startup script
CMD ["./scripts/startup.sh"]
