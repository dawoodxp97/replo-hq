# Multi-stage Dockerfile for Backend
# Base stage with common dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies including build tools for tree-sitter
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    git \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
COPY requirements-dev.txt* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install development dependencies if file exists
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# Development stage with additional tools
FROM base AS development

# Copy and install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Create directories for tree-sitter
RUN mkdir -p vendor/tree-sitter-javascript vendor/tree-sitter-python vendor/tree-sitter-typescript build

# Clone tree-sitter language repositories
RUN git clone https://github.com/tree-sitter/tree-sitter-javascript vendor/tree-sitter-javascript && \
    git clone https://github.com/tree-sitter/tree-sitter-python vendor/tree-sitter-python && \
    git clone https://github.com/tree-sitter/tree-sitter-typescript vendor/tree-sitter-typescript

# Create temp directory for repository cloning
RUN mkdir -p /tmp/reploai

# Stage 3: Linting and code quality checks
FROM development AS lint

# Run code formatting check
RUN black --check --diff .

# Run import sorting check
RUN isort --check-only --diff .

# Run linting
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
RUN flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run type checking
RUN mypy . --ignore-missing-imports || true

# Run security checks
RUN bandit -r . -f json -o bandit-report.json || true
RUN safety check --json --output safety-report.json || true

# Stage 4: Testing (optional - can be extended)
FROM development AS test

# Run tests if test files exist
RUN if [ -d "tests" ]; then python -m pytest tests/ -v; fi

# Stage 5: Production build
FROM base AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code from development stage
COPY --from=development /app/app ./app
COPY --from=development /app/vendor ./vendor
COPY --from=development /app/run.py ./
COPY --from=development /app/run_worker.py ./

# Create necessary directories
RUN mkdir -p /tmp/reploai && \
    chown -R appuser:appuser /app /tmp/reploai

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]