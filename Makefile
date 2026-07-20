.PHONY: help dev setup-dev backend frontend worker dev-all build start stop logs clean


help:
	@echo "Available commands:"
	@echo "  make setup-dev - Interactive development environment setup"
	@echo "  make dev       - Start database services only"
	@echo "  make backend   - Start backend server"
	@echo "  make frontend  - Start frontend server"
	@echo "  make worker    - Start worker process"
	@echo "  make dev-all   - Start backend, frontend, and worker"
	@echo "  make build     - Build production Docker images"
	@echo "  make start     - Start production environment"
	@echo "  make stop      - Stop all services"
	@echo "  make logs      - View logs"
	@echo "  make clean     - Clean up Docker resources"

setup-dev:
	@./scripts/setup-dev.sh

dev:
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
	echo "🐳 Starting database services..." && \
	docker-compose up -d postgres redis && \
	echo "✅ Database services started!" && \
	echo "   PostgreSQL: localhost:$${POSTGRES_PORT:-5432}" && \
	echo "   Redis: localhost:$${REDIS_PORT:-6379}"

backend: dev
	@echo "🚀 Starting backend server..."
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
	cd backend && \
	if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi && \
	source .venv/bin/activate && \
	if [ ! -f ".venv/.deps_installed" ]; then \
		echo "Installing dependencies..."; \
		pip install -q -r requirements.txt; \
		touch .venv/.deps_installed; \
	fi && \
	uvicorn app.main:app --reload --host 0.0.0.0 --port $${BACKEND_PORT:-8000}

frontend:
	@echo "🚀 Starting frontend server..."
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
	cd frontend/replo && \
	if [ ! -d "node_modules" ]; then \
		echo "Installing dependencies..."; \
		npm install; \
	fi && \
	npm run dev

worker: dev
	@echo "⚙️  Starting worker process..."
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
	cd backend && \
	if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi && \
	source .venv/bin/activate && \
	if [ ! -f ".venv/.deps_installed" ]; then \
		echo "Installing dependencies..."; \
		pip install -q -r requirements.txt; \
		touch .venv/.deps_installed; \
	fi && \
	python run_worker.py

dev-all:
	@if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
	echo "🚀 Starting all development services..." && \
	echo "   Backend: http://localhost:$${BACKEND_PORT:-8000}" && \
	echo "   Frontend: http://localhost:$${FRONTEND_PORT:-3000}" && \
	echo "" && \
	echo "Press Ctrl+C to stop all services" && \
	trap 'kill 0' EXIT; \
	make -j3 backend frontend worker

build:
	@./scripts/build.sh

start:
	@./scripts/start.sh

stop:
	@docker-compose down

logs:
	@docker-compose logs -f

clean:
	@docker-compose down -v
	@docker system prune -f
