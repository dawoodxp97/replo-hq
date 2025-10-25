# ReploAI: AI-Powered Code Tutorial Generator

ReploAI is an application that automatically generates interactive code tutorials from GitHub repositories. It uses AI to analyze codebases, create step-by-step tutorials with explanations, interactive code editors, and quizzes.

## Features

- **Repository Analysis**: Submit any GitHub repository URL for analysis
- **Multi-Level Tutorials**: Automatically generates beginner, intermediate, and advanced tutorials
- **Interactive Code Editor**: Built-in Sandpack editor for running code examples
- **Quizzes**: Auto-generated quizzes to test understanding
- **Progress Tracking**: Track your progress through tutorials
- **Custom Authoring**: Edit and customize generated tutorials

## Architecture

ReploAI is built with a modern tech stack:

- **Frontend**: Next.js 16, React 19, TanStack Query, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI & Analysis**: OpenAI GPT-4, CodeBERT, Tree-sitter
- **Job Queue**: Redis + ARQ for background processing
- **Containerization**: Docker and Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/reploai.git
   cd reploai
   ```

2. Create a `.env` file in the backend directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Start the application with Docker Compose:
   ```bash
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Development

### Backend Development

The backend is structured as follows:

- `app/`: Main application package
  - `core/`: Core services (analysis, generation, security)
  - `db/`: Database models and session management
  - `models/`: SQLAlchemy models
  - `routers/`: API endpoints
  - `schemas/`: Pydantic schemas
  - `workers/`: Background job workers

To run the backend locally:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

To run the worker:

```bash
cd backend
python run_worker.py
```

### Frontend Development

The frontend is structured as follows:

- `app/`: Next.js app router
- `components/`: React components
  - `dashboard/`: Dashboard components
  - `tutorial/`: Tutorial player components
  - `author/`: Authoring components
- `lib/`: Utility functions and API client
- `services/`: API service functions

To run the frontend locally:

```bash
cd frontend/replo
npm install
npm run dev
```

## Implementation Details

### Phase 1: Database Schema

PostgreSQL database with tables for:
- Repositories
- Tutorials
- Modules
- Quizzes
- User Progress

### Phase 2: AI Analysis Pipeline

1. Repository ingestion via Git
2. Code structure analysis with Tree-sitter
3. Code summarization with CodeBERT
4. Dependency graph generation
5. Tutorial generation with GPT-4
6. Module and quiz generation

### Phase 3: API Design

RESTful API endpoints for:
- Repository submission and retrieval
- Tutorial content
- User progress tracking
- Quiz submission
- Custom authoring

### Phase 4: Frontend Components

- Dashboard with repository submission
- Tutorial player with split-screen layout
- Interactive code editor
- Quiz component
- Progress tracking

### Phase 5: Worker & Queue Integration

- Redis for job queue
- ARQ for worker management
- Background processing for long-running tasks

### Phase 6: Custom Authoring Panel

- Edit tutorial content
- Modify code examples
- Customize quizzes

## License

This project is licensed under the MIT License - see the LICENSE file for details.