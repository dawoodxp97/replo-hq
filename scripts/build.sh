#!/bin/bash
set -e

echo "🔨 Building production Docker images..."

# Build backend
echo "📦 Building backend image..."
docker build -t replo-backend:latest ./backend

# Build frontend
echo "📦 Building frontend image..."
docker build -t replo-frontend:latest ./frontend/replo

echo "✅ All images built successfully!"
echo ""
echo "📊 Image sizes:"
docker images | grep replo

