#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Starting local development environment..."

# Start database services
echo "📦 Starting database services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are healthy
docker-compose ps

echo "✅ Development environment ready!"
echo ""
echo "📝 Next steps:"
echo "  make backend  - Start backend server"
echo "  make frontend - Start frontend server"
echo "  make worker   - Start worker process"
echo "  make dev-all  - Start all services"
echo ""
echo "🌐 Services:"
echo "  - Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo "  - Backend: http://localhost:${BACKEND_PORT:-8000}"
echo "  - API Docs: http://localhost:${BACKEND_PORT:-8000}/docs"

