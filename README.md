<div align="center">

# 🚀 ReploAI: AI-Powered Code Tutorial Generator

**Turn any codebase into step-by-step interactive tutorials automatically**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

_A modern learning platform that automatically analyzes GitHub repositories and generates comprehensive, interactive tutorials with AI-powered explanations, code examples, diagrams, and quizzes._

[Features](#-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [Development](#-development) • [Documentation](#-documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Development Guide](#-development-guide)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Implementation Phases](#-implementation-phases)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

ReploAI is an intelligent platform that transforms any GitHub repository into an interactive learning experience. By leveraging advanced AI models (GPT-4, CodeBERT, Tree-sitter), it automatically:

- **Analyzes** code repositories to understand structure and dependencies
- **Generates** step-by-step tutorials at multiple difficulty levels (Beginner, Intermediate, Advanced)
- **Creates** interactive code examples with live execution
- **Produces** visual dependency graphs and architecture diagrams
- **Builds** quizzes to test understanding and track progress

Perfect for developers learning new codebases, educators creating course content, or teams onboarding new members.

### Key Value Propositions

✨ **Automated Learning**: No manual tutorial creation needed  
🎓 **Multi-Level Content**: Beginner to advanced tracks from the same codebase  
💻 **Interactive Experience**: Live code editing and execution  
📊 **Visual Learning**: Dependency graphs and architecture diagrams  
📝 **Progress Tracking**: Monitor your learning journey  
✏️ **Customizable**: Edit and improve AI-generated content

---

## ✨ Features

### Core Features

| Feature                         | Description                                                                                  |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| **🔍 Repository Analysis**      | Analyze any GitHub repository structure using AST parsing and AI code understanding          |
| **📚 Multi-Level Tutorials**    | Automatically generate Beginner, Intermediate, and Advanced tutorials from the same codebase |
| **💡 Interactive Code Editor**  | Built-in Sandpack editor with Monaco for live code editing and execution                     |
| **📊 Dependency Visualization** | Mermaid.js-powered dependency graphs showing code relationships                              |
| **🧪 AI-Generated Quizzes**     | Automatically create quizzes based on tutorial content to test understanding                 |
| **📈 Progress Tracking**        | Track completion status, quiz scores, and learning analytics                                 |
| **✏️ Custom Authoring**         | Edit, customize, and improve AI-generated tutorials                                          |
| **🔔 Notifications**            | Real-time updates on tutorial generation status                                              |
| **🔎 Search & Discovery**       | Search through repositories and tutorials                                                    |
| **📱 Responsive Design**        | Beautiful, modern UI that works on all devices                                               |

### Advanced Features

- **Background Processing**: Async job queue for long-running tutorial generation
- **Real-time Updates**: WebSocket support for live generation progress
- **User Authentication**: Secure JWT-based authentication system
- **Settings Management**: Customizable user preferences and notification settings
- **Dashboard Analytics**: Comprehensive insights into learning progress

---

## 🏗️ Architecture

ReploAI follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  Next.js 16 + React 19 + TanStack Query + Tailwind CSS     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Dashboard  │  │  Tutorial   │  │  Authoring  │         │
│  │   Viewer    │  │   Player    │  │    Panel   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────┴─────────────────────────────────┐
│                        Backend API Layer                      │
│  FastAPI + SQLAlchemy + Pydantic + JWT Authentication        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Repository  │  │  Tutorial   │  │   Progress  │         │
│  │   Router    │  │   Router    │  │   Router    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      Background Workers                       │
│  ARQ + Redis Queue for Async Processing                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Analysis Worker: Code Analysis & Tutorial Generation│   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                        AI Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    GPT-4    │  │  CodeBERT   │  │ Tree-sitter │         │
│  │ (Tutorials) │  │ (Code Understanding)│ (AST Parsing)│   │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      Data Layer                              │
│  ┌───────────────┐              ┌───────────────┐          │
│  │  PostgreSQL   │              │     Redis     │          │
│  │  (Tutorials,  │              │  (Job Queue,  │          │
│  │   Progress,   │              │   Caching)    │          │
│  │   Users)      │              │               │          │
│  └───────────────┘              └───────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Repository Submission**: User submits GitHub repo URL via frontend
2. **Analysis Queue**: Job is queued in Redis for background processing
3. **Code Analysis**: Worker clones repo, analyzes structure with Tree-sitter, understands code with CodeBERT
4. **Tutorial Generation**: GPT-4 generates tutorial content, modules, and quizzes
5. **Storage**: Generated content is stored in PostgreSQL
6. **Delivery**: Frontend fetches and displays tutorials with interactive components

---

## 🛠️ Tech Stack

### Frontend

| Technology         | Purpose                                 | Version   |
| ------------------ | --------------------------------------- | --------- |
| **Next.js**        | React framework with SSR/SSG            | 16.0.0    |
| **React**          | UI library                              | 19.2.0    |
| **TypeScript**     | Type-safe JavaScript                    | ^5        |
| **TanStack Query** | Data fetching and caching               | ^5.90.5   |
| **Tailwind CSS**   | Utility-first CSS framework             | ^4        |
| **Sandpack**       | Interactive code editor and execution   | ^2.20.0   |
| **Monaco Editor**  | Code editor (VS Code editor in browser) | ^4.7.0    |
| **Mermaid.js**     | Diagram and flowchart rendering         | 11.12.0   |
| **Ant Design**     | UI component library                    | 5.27.6    |
| **Zustand**        | State management                        | 5.0.8     |
| **Framer Motion**  | Animation library                       | ^12.23.24 |

### Backend

| Technology     | Purpose                                       | Version |
| -------------- | --------------------------------------------- | ------- |
| **FastAPI**    | Modern, fast web framework for Python         | 0.104.1 |
| **Python**     | Programming language                          | 3.11+   |
| **SQLAlchemy** | ORM for database operations                   | 2.0.23  |
| **Alembic**    | Database migrations                           | 1.12.1  |
| **Pydantic**   | Data validation using Python type annotations | 2.6.0   |
| **ARQ**        | Async Redis queue for job processing          | 0.25.0  |
| **Redis**      | In-memory data store for queues and caching   | 5.0.1   |
| **PostgreSQL** | Relational database                           | 15+     |
| **PyJWT**      | JWT authentication                            | 2.8.0   |
| **GitPython**  | Git repository operations                     | 3.1.40  |

### AI & Code Analysis

| Technology       | Purpose                                     |
| ---------------- | ------------------------------------------- |
| **OpenAI GPT-4** | Tutorial content generation and explanation |
| **CodeBERT**     | Code understanding and summarization        |
| **Tree-sitter**  | AST parsing for code structure analysis     |
| **Transformers** | Hugging Face transformers for CodeBERT      |
| **PyTorch**      | Deep learning framework for CodeBERT        |

### Infrastructure

- **Docker** & **Docker Compose**: Containerization and orchestration
- **GitHub API**: Repository access and metadata
- **Nginx**: Reverse proxy (production)

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Node.js** (18.0+) and **npm** (9.0+) - for local frontend development
- **Python** (3.11+) and **pip** - for local backend development
- **Git** - for version control
- **OpenAI API Key** - for AI tutorial generation

### Quick Start with Docker

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/replo-hq.git
   cd replo-hq
   ```

2. **Set up environment variables**

   Create a `.env` file in the root directory:

   ```bash
   # OpenAI API Key (required)
   OPENAI_API_KEY=your_openai_api_key_here

   # Database Configuration (optional - defaults provided)
   POSTGRES_USER=tutorial_user
   POSTGRES_PASSWORD=tutorial_password
   POSTGRES_DB=tutorial_db

   # Redis Configuration
   REDIS_HOST=redis
   REDIS_PORT=6379

   # API Configuration
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start all services**

   ```bash
   docker-compose up
   ```

   This will start:

   - PostgreSQL database (port 5432)
   - Redis (port 6379)
   - Backend API (port 8000)
   - Background worker
   - Frontend (port 3000)

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Installation

If you prefer to run services locally without Docker:

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_openai_api_key_here
export SQLALCHEMY_DATABASE_URL=postgresql://tutorial_user:tutorial_password@localhost/tutorial_db
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run database migrations (if needed)
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload

# In another terminal, start the worker
python run_worker.py
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend/replo

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## 💻 Development Guide

### Project Structure

```
replo-hq/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── core/              # Core services
│   │   │   ├── analysis_service.py    # Code analysis logic
│   │   │   ├── generation_service.py  # AI tutorial generation
│   │   │   ├── llm_providers.py       # LLM integration (OpenAI, etc.)
│   │   │   ├── quiz_service.py        # Quiz generation
│   │   │   └── security.py            # Authentication & authorization
│   │   ├── db/                # Database configuration
│   │   │   └── session.py     # SQLAlchemy session management
│   │   ├── models/            # SQLAlchemy database models
│   │   │   ├── repositories.py
│   │   │   ├── tutorials.py
│   │   │   ├── modules.py
│   │   │   ├── quizzes.py
│   │   │   └── user_progress.py
│   │   ├── routers/           # API route handlers
│   │   │   ├── repo.py        # Repository endpoints
│   │   │   ├── tutorial.py    # Tutorial endpoints
│   │   │   ├── progress.py    # Progress tracking
│   │   │   ├── author.py      # Authoring panel
│   │   │   └── ...
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── workers/           # Background job workers
│   │   │   ├── worker.py      # ARQ worker setup
│   │   │   └── analysis_worker.py  # Tutorial generation worker
│   │   └── main.py            # FastAPI application entry
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile
│   └── run_worker.py          # Worker entry point
│
├── frontend/replo/            # Next.js frontend application
│   ├── app/                   # Next.js app router
│   │   ├── (private)/         # Protected routes
│   │   │   ├── dashboard/     # User dashboard
│   │   │   ├── tutorial/      # Tutorial viewer
│   │   │   ├── authoring/     # Authoring panel
│   │   │   ├── progress/      # Progress tracking
│   │   │   └── settings/      # User settings
│   │   └── (public)/          # Public routes
│   │       ├── login/          # Authentication
│   │       └── signup/
│   ├── components/            # React components
│   │   ├── features/          # Feature-specific components
│   │   │   ├── tutorial/      # Tutorial player components
│   │   │   ├── dashboard/     # Dashboard components
│   │   │   └── authoring/     # Authoring components
│   │   ├── common/            # Shared components
│   │   └── ui/                # UI primitives
│   ├── lib/                   # Utility functions
│   │   ├── apiClient.ts       # API client configuration
│   │   └── auth.ts            # Authentication utilities
│   ├── services/              # API service functions
│   │   ├── tutorialService.ts
│   │   ├── repoService.ts
│   │   └── ...
│   ├── styles/                # Global styles
│   └── package.json
│
├── docker-compose.yml         # Docker orchestration
├── README.md                  # This file
└── LICENSE                    # MIT License
```

### Development Workflow

1. **Backend Development**

   ```bash
   cd backend
   # Make changes to code
   # Auto-reload is enabled with --reload flag
   ```

2. **Frontend Development**

   ```bash
   cd frontend/replo
   npm run dev
   # Hot reload enabled automatically
   ```

3. **Running Tests** (when implemented)

   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend/replo
   npm test
   ```

4. **Code Quality**

   ```bash
   # Backend linting
   cd backend
   flake8 app/
   black app/  # Format code

   # Frontend linting
   cd frontend/replo
   npm run lint
   npm run format  # Format code
   ```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## 📚 API Documentation

### Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Key Endpoints

#### Repository Management

- `POST /api/repo` - Submit a new repository for analysis
- `GET /api/repo` - List all repositories
- `GET /api/repo/{repo_id}` - Get repository details
- `DELETE /api/repo/{repo_id}` - Delete a repository

#### Tutorials

- `GET /api/tutorial` - List all tutorials
- `GET /api/tutorial/{tutorial_id}` - Get tutorial content
- `GET /api/tutorial/{tutorial_id}/modules` - Get tutorial modules
- `POST /api/tutorial/{tutorial_id}/generate` - Trigger tutorial generation

#### Progress Tracking

- `GET /api/progress` - Get user progress
- `POST /api/progress` - Update progress
- `GET /api/progress/{tutorial_id}` - Get progress for specific tutorial

#### Authoring

- `PUT /api/author/tutorial/{tutorial_id}` - Update tutorial content
- `PUT /api/author/module/{module_id}` - Update module content
- `POST /api/author/quiz/{module_id}` - Create/update quiz

### Interactive API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📋 Implementation Phases

ReploAI is built in phases, following the PRD:

### ✅ Phase 1: Core MVP (Completed)

- [x] Database schema design (PostgreSQL)
- [x] GitHub repository ingestion
- [x] AST parsing with Tree-sitter
- [x] Code analysis with CodeBERT
- [x] Basic tutorial generation with GPT-4
- [x] Next.js viewer UI with markdown rendering

### ✅ Phase 2: Interactive Layer (Completed)

- [x] Sandpack/Monaco Editor integration
- [x] Split-screen tutorial view
- [x] PostgreSQL storage for modules and metadata
- [x] Real-time code execution

### ✅ Phase 3: Learning System (Completed)

- [x] AI quiz generation
- [x] Progress tracking system
- [x] Analytics dashboard
- [x] User authentication

### 🚧 Phase 4: Stretch Features (In Progress)

- [ ] Multi-language tutorial support
- [ ] Video tutorial generation with TTS
- [ ] Community moderation system
- [ ] Auto-adjusting difficulty levels
- [ ] Integration with documentation tools

---

## ⚙️ Configuration

### Environment Variables

#### Backend

| Variable                  | Description                  | Default                                                              |
| ------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| `OPENAI_API_KEY`          | OpenAI API key for GPT-4     | **Required**                                                         |
| `SQLALCHEMY_DATABASE_URL` | PostgreSQL connection string | `postgresql://tutorial_user:tutorial_password@localhost/tutorial_db` |
| `REDIS_HOST`              | Redis host                   | `localhost`                                                          |
| `REDIS_PORT`              | Redis port                   | `6379`                                                               |
| `JWT_SECRET_KEY`          | Secret key for JWT tokens    | Generated automatically                                              |
| `JWT_ALGORITHM`           | JWT algorithm                | `HS256`                                                              |

#### Frontend

| Variable              | Description     | Default                 |
| --------------------- | --------------- | ----------------------- |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

### LLM Provider Configuration

The system supports multiple LLM providers. See `backend/LLM_PROVIDERS.md` for configuration details.

---

## 🐛 Troubleshooting

### Common Issues

#### Backend won't start

- **Check database connection**: Ensure PostgreSQL is running
- **Verify Redis**: Ensure Redis is accessible
- **Check environment variables**: Ensure `OPENAI_API_KEY` is set

#### Worker not processing jobs

- **Check Redis connection**: Verify Redis is running and accessible
- **Check logs**: `docker-compose logs worker`
- **Verify job queue**: Check Redis for queued jobs

#### Frontend API errors

- **Verify API URL**: Check `NEXT_PUBLIC_API_URL` environment variable
- **Check CORS**: Ensure backend CORS settings allow frontend origin
- **Check authentication**: Verify JWT tokens are valid

#### Tutorial generation fails

- **Check OpenAI API key**: Verify key is valid and has credits
- **Check repository access**: Ensure repository is public or access is granted
- **Review worker logs**: Check for specific error messages

### Getting Help

- Check the [WORKER_TROUBLESHOOTING.md](backend/WORKER_TROUBLESHOOTING.md) guide
- Review logs: `docker-compose logs`
- Open an issue on GitHub

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Contribution Guidelines

- Follow the existing code style
- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

### Development Setup for Contributors

1. Fork and clone the repository
2. Set up the development environment (see [Development Guide](#-development-guide))
3. Create a branch for your changes
4. Make your changes and test thoroughly
5. Submit a pull request with a clear description

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **Microsoft** for CodeBERT model
- **Tree-sitter** for AST parsing
- **CodeSandbox** for Sandpack inspiration
- **Mermaid.js** for diagram generation
- All open-source contributors and libraries that made this possible

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/replo-hq/issues)
- **Documentation**: Check the `/docs` folder for detailed guides
- **PRD**: See `I need full fledged PRD and implementations steps.md` for the complete product requirements

---

<div align="center">

**Built with ❤️ by the ReploAI Team**

_Making code learning accessible, interactive, and intelligent_

[⭐ Star us on GitHub](https://github.com/yourusername/replo-hq) • [🐛 Report Bug](https://github.com/yourusername/replo-hq/issues) • [💡 Request Feature](https://github.com/yourusername/replo-hq/issues)

</div>
