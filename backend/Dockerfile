# ./backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for tree-sitter
RUN mkdir -p vendor/tree-sitter-javascript vendor/tree-sitter-python vendor/tree-sitter-typescript build

# Clone tree-sitter language repositories
RUN git clone https://github.com/tree-sitter/tree-sitter-javascript vendor/tree-sitter-javascript && \
    git clone https://github.com/tree-sitter/tree-sitter-python vendor/tree-sitter-python && \
    git clone https://github.com/tree-sitter/tree-sitter-typescript vendor/tree-sitter-typescript

# Create temp directory for repository cloning
RUN mkdir -p /tmp/reploai

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]