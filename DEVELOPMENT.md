# Development Guide

This guide covers local development setup, workflows, and best practices for the Replo application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Workflows](#development-workflows)
4. [Code Quality](#code-quality)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Database Management](#database-management)
8. [API Documentation](#api-documentation)
9. [Contributing](#contributing)

## Prerequisites

### Required Software
- **Docker & Docker Compose**: For database services
- **Node.js 20+**: For frontend development
- **Python 3.11+**: For backend development
- **Git**: Version control

### Optional Tools
- **VS Code**: Recommended IDE with extensions
- **Postman/Insomnia**: API testing
- **pgAdmin**: Database administration
- **Redis Insight**: Redis administration

### VS Code Extensions (Recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers",
    "ms-vscode.docker"
  ]
}
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/replo.git
cd replo
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Minimum required:
# - OPENAI_API_KEY (for AI features)
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Start Database Services
```bash
# Start PostgreSQL and Redis
docker compose -f docker-compose.dev.yml up -d

# Optional: Start with admin tools
docker compose -f docker-compose.dev.yml --profile admin up -d
```

### 4. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup
```bash
cd frontend/replo

# Install dependencies
npm install

# Start development server
npm run dev
```

### 6. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **pgAdmin** (if enabled): http://localhost:5050
- **Redis Insight** (if enabled): http://localhost:8001

## Development Workflows

### Daily Development Workflow

1. **Start Development Environment**
   ```bash
   # Terminal 1: Start databases
   docker compose -f docker-compose.dev.yml up -d
   
   # Terminal 2: Start backend
   cd backend && source venv/bin/activate
   uvicorn app.main:app --reload
   
   # Terminal 3: Start frontend
   cd frontend/replo && npm run dev
   ```

2. **Make Changes**
   - Edit code with live reload enabled
   - Use hot module replacement for frontend
   - Backend auto-reloads on file changes

3. **Test Changes**
   ```bash
   # Run backend tests
   cd backend && pytest
   
   # Run frontend tests
   cd frontend/replo && npm test
   ```

4. **Commit Changes**
   ```bash
   # Format and lint code
   cd backend && black . && isort . && flake8 .
   cd frontend/replo && npm run prettier:fix && npm run lint:fix
   
   # Commit with conventional commits
   git add .
   git commit -m "feat: add new feature"
   ```

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **hotfix/**: Critical bug fixes
- **release/**: Release preparation

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# Work on feature...

# Push and create PR
git push origin feature/new-feature
# Create PR to develop branch
```

### Docker Development (Alternative)

For full Docker development environment:

```bash
# Start all services with live reload
docker compose up --no-build backend frontend

# View logs
docker compose logs -f backend frontend

# Execute commands in containers
docker compose exec backend python manage.py shell
docker compose exec frontend npm run test
```

## Code Quality

### Backend Code Quality

#### Formatting and Linting
```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .

# Security scanning with bandit
bandit -r .

# Dependency vulnerability check
safety check
```

#### Pre-commit Hooks
Install pre-commit hooks to automatically run checks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', '.']
```

### Frontend Code Quality

#### Formatting and Linting
```bash
# Format with Prettier
npm run prettier:fix

# Lint with ESLint
npm run lint:fix

# Type checking
npm run type-check

# Run all checks
npm run check-all
```

#### Package.json Scripts
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "prettier": "prettier --check .",
    "prettier:fix": "prettier --write .",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:ci": "jest --ci --coverage --watchAll=false",
    "check-all": "npm run type-check && npm run lint && npm run prettier && npm run test:ci"
  }
}
```

## Testing

### Backend Testing

#### Test Structure
```
backend/tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_main.py         # Main application tests
├── unit/                # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/         # Integration tests
│   ├── test_api.py
│   └── test_database.py
└── e2e/                 # End-to-end tests
    └── test_workflows.py
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching pattern
pytest -k "test_user"

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

#### Test Configuration
Create `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
```

### Frontend Testing

#### Test Structure
```
frontend/replo/tests/
├── __mocks__/           # Mock files
├── components/          # Component tests
├── pages/              # Page tests
├── utils/              # Utility function tests
└── e2e/                # End-to-end tests
```

#### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:ci

# Run specific test file
npm test -- components/Button.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"
```

#### Jest Configuration
Create `jest.config.js`:
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/pages/(.*)$': '<rootDir>/pages/$1',
    '^@/utils/(.*)$': '<rootDir>/utils/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'pages/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

## Debugging

### Backend Debugging

#### VS Code Debug Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/app/main.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "args": ["--reload", "--host", "0.0.0.0", "--port", "8000"]
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

#### Debugging Tips
```python
# Use pdb for debugging
import pdb; pdb.set_trace()

# Use rich for better debugging output
from rich import print
print({"user": user, "data": data})

# Use logging for production debugging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Frontend Debugging

#### Browser DevTools
- Use React Developer Tools extension
- Use Redux DevTools for state management
- Use Network tab for API debugging
- Use Console for JavaScript debugging

#### VS Code Debug Configuration
```json
{
  "name": "Next.js: debug server-side",
  "type": "node",
  "request": "launch",
  "program": "${workspaceFolder}/frontend/replo/node_modules/.bin/next",
  "args": ["dev"],
  "console": "integratedTerminal",
  "skipFiles": ["<node_internals>/**"]
}
```

## Database Management

### Migrations

#### Create Migration
```bash
cd backend

# Auto-generate migration
alembic revision --autogenerate -m "Add user table"

# Create empty migration
alembic revision -m "Custom migration"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

#### Migration Best Practices
1. Always review auto-generated migrations
2. Test migrations on development data
3. Create rollback procedures for production
4. Use descriptive migration messages
5. Avoid breaking changes in migrations

### Database Operations

#### Connect to Database
```bash
# Using Docker
docker exec -it replo-postgres-dev psql -U tutorial_user -d tutorial_db

# Using local PostgreSQL
psql -h localhost -U tutorial_user -d tutorial_db
```

#### Common SQL Operations
```sql
-- Show all tables
\dt

-- Describe table structure
\d users

-- Show database size
SELECT pg_size_pretty(pg_database_size('tutorial_db'));

-- Show table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Show active connections
SELECT * FROM pg_stat_activity;
```

#### Backup and Restore
```bash
# Backup database
docker exec replo-postgres-dev pg_dump -U tutorial_user tutorial_db > backup.sql

# Restore database
docker exec -i replo-postgres-dev psql -U tutorial_user tutorial_db < backup.sql

# Backup with compression
docker exec replo-postgres-dev pg_dump -U tutorial_user -Fc tutorial_db > backup.dump

# Restore from compressed backup
docker exec -i replo-postgres-dev pg_restore -U tutorial_user -d tutorial_db backup.dump
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Testing

#### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Get user (with authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me

# Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

#### Using HTTPie
```bash
# Install HTTPie
pip install httpie

# Health check
http GET localhost:8000/health

# Get user (with authentication)
http GET localhost:8000/api/users/me Authorization:"Bearer <token>"

# Create user
http POST localhost:8000/api/users email=user@example.com password=password123
```

### API Client Generation
Generate TypeScript client for frontend:

```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o frontend/replo/src/api/generated
```

## Contributing

### Code Style Guidelines

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public functions
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names

#### TypeScript/JavaScript (Frontend)
- Use TypeScript for all new code
- Follow Airbnb style guide
- Use functional components with hooks
- Prefer const over let, avoid var
- Use meaningful component and variable names

### Commit Message Format
Use Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(auth): add JWT token refresh functionality
fix(api): resolve user creation validation error
docs(readme): update installation instructions
test(user): add unit tests for user service
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Changes**
   ```bash
   # Run all tests
   cd backend && pytest
   cd frontend/replo && npm test
   
   # Run linting
   cd backend && black . && isort . && flake8 .
   cd frontend/replo && npm run lint && npm run prettier
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use descriptive title and description
   - Link related issues
   - Add screenshots for UI changes
   - Request review from team members

6. **Address Review Comments**
   - Make requested changes
   - Push additional commits
   - Re-request review

7. **Merge**
   - Squash and merge to develop
   - Delete feature branch

### Development Environment Troubleshooting

#### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   ```

2. **Database Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres
   
   # Restart database
   docker compose -f docker-compose.dev.yml restart postgres
   ```

3. **Node Modules Issues**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Python Virtual Environment Issues**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

For additional help, check the project documentation or ask the development team.