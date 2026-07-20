# Replo

AI-powered code tutorial generator that transforms GitHub repositories into interactive learning experiences.

## Quick Start

### First Time Setup

```bash
# Interactive setup (creates .env and initializes database)
make setup-dev
```

### Development

```bash
# Start all services (backend, frontend, worker)
make dev-all

# Or start individually:
make backend   # Starts backend server (auto-starts DB)
make frontend   # Starts frontend server
make worker     # Starts worker process (auto-starts DB)
```

### Production

```bash
# Build images
make build

# Start services
make start
```

## Environment Variables

The setup script will create a `.env` file at the root. You can also create it manually from `.env.example`:

```env
POSTGRES_USER=tutorial_user
POSTGRES_PASSWORD=tutorial_password
POSTGRES_DB=tutorial_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=kwaipilot/kat-coder-pro:free
JWT_SECRET_KEY=your_jwt_secret
CORS_ORIGINS=http://localhost:3000
```

## Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Tech Stack

- **Frontend**: Next.js 16, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL 15
- **Queue**: Redis, ARQ
- **AI**: OpenRouter (open-source models)
