# Replo Application Makefile
# This Makefile provides convenient commands for development, testing, and deployment

.PHONY: help dev dev-db dev-frontend dev-backend build build-frontend build-backend \
        test test-frontend test-backend lint lint-frontend lint-backend format \
        format-frontend format-backend clean clean-docker deploy-staging deploy-prod \
        logs logs-dev logs-prod backup restore security-scan performance-test \
        setup-dev install-deps pre-commit-install devsetup

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.prod.yml
FRONTEND_DIR := frontend/replo
BACKEND_DIR := backend
PYTHON := python3
NODE := node
NPM := npm

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Replo Application - Available Commands$(NC)"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Development Commands
setup-dev: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@$(MAKE) install-deps
	@$(MAKE) pre-commit-install
	@$(MAKE) dev-db
	@echo "$(GREEN)Development environment setup complete!$(NC)"

install-deps: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "Installing backend dependencies..."
	@cd $(BACKEND_DIR) && pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	@cd $(FRONTEND_DIR) && $(NPM) install --force
	@echo "$(GREEN)Dependencies installed!$(NC)"

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	@pip install pre-commit
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"

devsetup: ## Reset database and reinstall packages (requires .venv activation)
	@echo "$(BLUE)Starting development setup with database reset...$(NC)"
	@echo "$(RED)WARNING: This will delete all database tables and data!$(NC)"
	@cd $(BACKEND_DIR) && \
		if [ ! -d ".venv" ]; then \
			echo "$(RED)Error: .venv not found. Please create a virtual environment first.$(NC)"; \
			echo "$(YELLOW)Run: cd backend && python3 -m venv .venv$(NC)"; \
			exit 1; \
		fi && \
		source .venv/bin/activate && \
		echo "$(YELLOW)Virtual environment activated$(NC)" && \
		echo "$(BLUE)Installing/updating packages...$(NC)" && \
		pip install -r requirements.txt -r requirements-dev.txt && \
		echo "$(GREEN)Packages installed successfully!$(NC)" && \
		echo "$(BLUE)Resetting database (dropping and recreating all tables)...$(NC)" && \
		echo "yes" | python app/scripts/devsetup/setup.py && \
		echo "$(GREEN)Database reset complete!$(NC)" && \
		echo "$(GREEN)Development setup complete! 🚀$(NC)"

dev: ## Start full development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@$(MAKE) dev-db
	@echo "$(YELLOW)Database started. Now start frontend and backend in separate terminals:$(NC)"
	@echo "$(YELLOW)  Frontend: make dev-frontend$(NC)"
	@echo "$(YELLOW)  Backend:  make dev-backend$(NC)"

dev-db: ## Start development database services
	@echo "$(BLUE)Starting development database services...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up -d postgres redis
	@echo "$(GREEN)Database services started!$(NC)"
	@echo "$(YELLOW)PostgreSQL: localhost:5432$(NC)"
	@echo "$(YELLOW)Redis: localhost:6379$(NC)"
	@echo "$(YELLOW)pgAdmin: http://localhost:5050$(NC)"
	@echo "$(YELLOW)RedisInsight: http://localhost:8001$(NC)"

dev-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting frontend development server...$(NC)"
	@echo "$(YELLOW)Installing/updating dependencies with force flag...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) install --force
	@echo "$(YELLOW)Starting development server...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run dev

dev-backend: ## Start backend development server
	@echo "$(BLUE)Starting backend development server...$(NC)"
	@echo "$(YELLOW)Make sure you have activated your virtual environment first:$(NC)"
	@echo "$(YELLOW)  cd backend && source .venv/bin/activate$(NC)"
	@cd $(BACKEND_DIR) && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Build Commands
build: ## Build all Docker images
	@echo "$(BLUE)Building all Docker images...$(NC)"
	@$(MAKE) build-frontend
	@$(MAKE) build-backend
	@echo "$(GREEN)All images built successfully!$(NC)"

build-frontend: ## Build frontend Docker image
	@echo "$(BLUE)Building frontend Docker image...$(NC)"
	@cd $(FRONTEND_DIR) && docker build -t replo-frontend:latest .
	@echo "$(GREEN)Frontend image built!$(NC)"

build-backend: ## Build backend Docker image
	@echo "$(BLUE)Building backend Docker image...$(NC)"
	@cd $(BACKEND_DIR) && docker build -t replo-backend:latest .
	@echo "$(GREEN)Backend image built!$(NC)"

# Testing Commands
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "$(GREEN)All tests completed!$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run test
	@cd $(FRONTEND_DIR) && $(NPM) run test:e2e

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest . -v --cov=app --cov-report=html --cov-report=term-missing

# Linting Commands
lint: ## Run all linting
	@echo "$(BLUE)Running all linting...$(NC)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend
	@echo "$(GREEN)Linting completed!$(NC)"

lint-frontend: ## Run frontend linting
	@echo "$(BLUE)Running frontend linting...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint
	@cd $(FRONTEND_DIR) && $(NPM) run type-check

lint-backend: ## Run backend linting
	@echo "$(BLUE)Running backend linting...$(NC)"
	@cd $(BACKEND_DIR) && flake8 .
	@cd $(BACKEND_DIR) && mypy .
	@cd $(BACKEND_DIR) && bandit -r . -f json -o bandit-report.json

# Formatting Commands
format: ## Format all code
	@echo "$(BLUE)Formatting all code...$(NC)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend
	@echo "$(GREEN)Code formatting completed!$(NC)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run format

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(NC)"
	@cd $(BACKEND_DIR) && black .
	@cd $(BACKEND_DIR) && isort .

# Security Commands
security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	@echo "Scanning backend dependencies..."
	@cd $(BACKEND_DIR) && safety check
	@echo "Scanning frontend dependencies..."
	@cd $(FRONTEND_DIR) && $(NPM) audit
	@echo "Scanning Docker images..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image replo-frontend:latest
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image replo-backend:latest
	@echo "$(GREEN)Security scans completed!$(NC)"

# Performance Testing
performance-test: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	@echo "Running Lighthouse CI..."
	@cd $(FRONTEND_DIR) && npx lhci autorun
	@echo "Running k6 load tests..."
	@k6 run ./tests/load/api-test.js
	@echo "$(GREEN)Performance tests completed!$(NC)"

# Deployment Commands
deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@echo "$(YELLOW)This would typically be handled by CI/CD pipeline$(NC)"
	@echo "$(YELLOW)Manual deployment steps:$(NC)"
	@echo "1. Build and push images"
	@echo "2. Update ECS task definitions"
	@echo "3. Deploy to staging cluster"

deploy-prod: ## Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(RED)WARNING: This is a production deployment!$(NC)"
	@echo "$(YELLOW)This would typically be handled by CI/CD pipeline$(NC)"
	@echo "$(YELLOW)Manual deployment steps:$(NC)"
	@echo "1. Build and push images with production tags"
	@echo "2. Update production ECS task definitions"
	@echo "3. Deploy to production cluster"
	@echo "4. Run health checks"

# Logging Commands
logs: ## Show development logs
	@echo "$(BLUE)Showing development logs...$(NC)"
	@$(DOCKER_COMPOSE_DEV) logs -f

logs-dev: ## Show development database logs
	@echo "$(BLUE)Showing development database logs...$(NC)"
	@$(DOCKER_COMPOSE_DEV) logs -f postgres redis

logs-prod: ## Show production logs
	@echo "$(BLUE)Showing production logs...$(NC)"
	@$(DOCKER_COMPOSE_PROD) logs -f

# Database Commands
backup: ## Backup development database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p ./backups
	@docker exec $$($(DOCKER_COMPOSE_DEV) ps -q postgres) \
		pg_dump -U replo_user replo_db > ./backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created in ./backups/ directory!$(NC)"

restore: ## Restore database from backup (requires BACKUP_FILE variable)
	@echo "$(BLUE)Restoring database from backup...$(NC)"
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Error: Please specify BACKUP_FILE variable$(NC)"; \
		echo "$(YELLOW)Usage: make restore BACKUP_FILE=backup_20231201_120000.sql$(NC)"; \
		exit 1; \
	fi
	@docker exec -i $$($(DOCKER_COMPOSE_DEV) ps -q postgres) \
		psql -U replo_user -d replo_db < $(BACKUP_FILE)
	@echo "$(GREEN)Database restored!$(NC)"

# Cleanup Commands
clean: ## Clean up development environment
	@echo "$(BLUE)Cleaning up development environment...$(NC)"
	@$(DOCKER_COMPOSE_DEV) down -v
	@echo "$(GREEN)Development environment cleaned!$(NC)"

clean-docker: ## Clean up Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)Docker cleanup completed!$(NC)"

# Status Commands
status: ## Show status of all services
	@echo "$(BLUE)Service Status$(NC)"
	@echo "=============="
	@echo "$(YELLOW)Development Services:$(NC)"
	@$(DOCKER_COMPOSE_DEV) ps
	@echo ""
	@echo "$(YELLOW)Docker Images:$(NC)"
	@docker images | grep replo || echo "No Replo images found"
	@echo ""
	@echo "$(YELLOW)Docker Volumes:$(NC)"
	@docker volume ls | grep replo || echo "No Replo volumes found"

# Health Checks
health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(YELLOW)Database Health:$(NC)"
	@pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo "✓ PostgreSQL" || echo "✗ PostgreSQL"
	@redis-cli -h localhost -p 6379 ping > /dev/null 2>&1 && echo "✓ Redis" || echo "✗ Redis"
	@echo "$(YELLOW)Application Health:$(NC)"
	@curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Backend API" || echo "✗ Backend API"
	@curl -f http://localhost:3000 > /dev/null 2>&1 && echo "✓ Frontend" || echo "✗ Frontend"

# Documentation
docs: ## Generate and serve documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)API Documentation: http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW)Development Guide: See DEVELOPMENT.md$(NC)"
	@echo "$(YELLOW)Deployment Guide: See DEPLOYMENT.md$(NC)"

# Quick Start
quick-start: ## Quick start for new developers
	@echo "$(BLUE)Quick Start Guide$(NC)"
	@echo "=================="
	@echo "$(YELLOW)1. Set up development environment:$(NC)"
	@echo "   make setup-dev"
	@echo ""
	@echo "$(YELLOW)2. Start database services:$(NC)"
	@echo "   make dev-db"
	@echo ""
	@echo "$(YELLOW)3. In separate terminals, start:$(NC)"
	@echo "   make dev-backend    # Terminal 1"
	@echo "   make dev-frontend   # Terminal 2"
	@echo ""
	@echo "$(YELLOW)4. Access the application:$(NC)"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend API: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "$(YELLOW)5. Run tests:$(NC)"
	@echo "   make test"
	@echo ""
	@echo "$(GREEN)Happy coding! 🚀$(NC)"