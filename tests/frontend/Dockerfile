# Dockerfile for Playwright Frontend Tests
# Uses official Playwright image with all browser dependencies pre-installed

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies using pip (simpler for Docker)
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Set environment variables
ENV BASE_URL=https://kanban.stormpath.dev
ENV TEST_USERNAME=testuser
ENV TEST_PASSWORD=TestPassword123!
ENV PYTHONUNBUFFERED=1

# Default command runs all tests
CMD ["pytest", "--browser", "chromium", "-v"]
