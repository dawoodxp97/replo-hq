#!/bin/bash
set -e

echo "🔧 Development Environment Setup"
echo "================================"
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file."
        source .env
    else
        rm .env
    fi
fi

# If .env doesn't exist or was removed, create it
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    
    # Database Configuration
    echo ""
    echo "📊 Database Configuration:"
    read -p "PostgreSQL Username [tutorial_user]: " postgres_user
    postgres_user=${postgres_user:-tutorial_user}
    
    read -sp "PostgreSQL Password [tutorial_password]: " postgres_password
    postgres_password=${postgres_password:-tutorial_password}
    echo ""
    
    read -p "PostgreSQL Database Name [tutorial_db]: " postgres_db
    postgres_db=${postgres_db:-tutorial_db}
    
    read -p "PostgreSQL Host [localhost]: " postgres_host
    postgres_host=${postgres_host:-localhost}
    
    read -p "PostgreSQL Port [5432]: " postgres_port
    postgres_port=${postgres_port:-5432}
    
    # Redis Configuration
    echo ""
    echo "🔴 Redis Configuration:"
    echo "   Note: Default Redis container doesn't require a password."
    echo "   Only set a password if your Redis instance requires authentication."
    read -p "Redis Host [localhost]: " redis_host
    redis_host=${redis_host:-localhost}
    
    read -p "Redis Port [6379]: " redis_port
    redis_port=${redis_port:-6379}
    
    read -sp "Redis Password (press Enter for no password): " redis_password_input
    redis_password=${redis_password_input:-""}
    echo ""
    
    # OpenRouter API
    echo ""
    echo "🤖 OpenRouter API Configuration:"
    read -sp "OpenRouter API Key: " openrouter_key
    echo ""
    
    read -p "OpenRouter Model [kwaipilot/kat-coder-pro:free]: " openrouter_model
    openrouter_model=${openrouter_model:-kwaipilot/kat-coder-pro:free}
    
    # JWT Secret
    echo ""
    echo "🔐 Security Configuration:"
    read -sp "JWT Secret Key: " jwt_secret
    echo ""
    
    # Create .env file
    cat > .env << EOF
# Database Configuration
POSTGRES_USER=$postgres_user
POSTGRES_PASSWORD=$postgres_password
POSTGRES_DB=$postgres_db
POSTGRES_HOST=$postgres_host
POSTGRES_PORT=$postgres_port

# Redis Configuration
REDIS_HOST=$redis_host
REDIS_PORT=$redis_port
REDIS_PASSWORD=${redis_password:-}

# OpenRouter API
OPENROUTER_API_KEY=$openrouter_key
OPENROUTER_MODEL=$openrouter_model

# JWT Secret
JWT_SECRET_KEY=$jwt_secret

# CORS Origins
CORS_ORIGINS=http://localhost:3000

# Backend Port
BACKEND_PORT=8000

# Frontend Port
FRONTEND_PORT=3000

# Next.js Public API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    
    echo "✅ .env file created!"
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start database services
echo ""
echo "🐳 Starting database services..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check database connection
echo "🔍 Testing database connection..."
until docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
    echo "Waiting for database..."
    sleep 2
done

echo "✅ Database is ready!"

# Reset database
echo ""
echo "🗑️  Resetting database (dropping and recreating all tables)..."
read -p "This will delete all data. Continue? (y/N): " confirm
if [[ $confirm =~ ^[Yy]$ ]]; then
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies if needed
    if [ ! -f ".venv/.deps_installed" ]; then
        echo "📦 Installing dependencies..."
        pip install -q -r requirements.txt
        touch .venv/.deps_installed
    fi
    
    # Run database reset
    echo "🔄 Resetting database..."
    # Load environment variables before running Python script
    export $(cat ../.env | grep -v '^#' | xargs)
    # Get the project root directory (one level up from backend/)
    PROJECT_ROOT=$(cd .. && pwd)
    python -c "
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load .env from project root
env_path = Path('$PROJECT_ROOT') / '.env'
if env_path.exists():
    load_dotenv(env_path)

sys.path.insert(0, os.path.abspath('.'))

from app.db.session import engine, Base
# Import all models to register them with Base
from app.models import (
    User, Repository, Tutorial, Module, Quiz,
    UserProgress, UserSettings, Notification, TutorialInstance
)

print('Dropping all tables CASCADE...')
with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
    conn.commit()

print('Creating all tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database reset complete!')
"
    
    deactivate
    cd ..
else
    echo "⏭️  Skipping database reset."
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "  make backend  - Start backend server"
echo "  make frontend - Start frontend server"
echo "  make worker   - Start worker process"
echo "  make dev-all  - Start all services"
