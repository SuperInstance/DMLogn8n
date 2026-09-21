# DMLog Makefile
# Comprehensive build automation for DMLog development and deployment
# Author: DMLog Development Team
# Version: 1.0.0

.PHONY: help install dev test lint format clean build deploy-staging deploy-prod
.PHONY: docker-build docker-up docker-down docker-logs
.PHONY: db-migrate db-reset db-shell cache-clear logs-tail monitor
.PHONY: security-check performance-test docs-build backup restore
.DEFAULT_GOAL := help

# Configuration
PYTHON := $(PROJECT_ROOT)/dmlog_env/bin/python
PIP := $(PROJECT_ROOT)/dmlog_env/bin/pip
PROJECT_ROOT := $(shell pwd)
DOCKER_COMPOSE := docker-compose
APP_MODULE := app.main:app
APP_HOST := 0.0.0.0
APP_PORT := 8000

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(CYAN)DMLog Development Tools - Makefile Help$(NC)"
	@echo "$(CYAN)=========================================$(NC)"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Development/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Testing Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Testing/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Database Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Database/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Docker/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Deployment Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zAYZ_-]+:.*?## / && /Deployment/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Maintenance Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Maintenance/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Utility/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# Development Commands
install: ## Development - Install all dependencies and setup environment
	@echo "$(CYAN)Installing DMLog development environment...$(NC)"
	@if [ ! -d "dmlog_env" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv dmlog_env; \
	fi
	@echo "$(YELLOW)Activating virtual environment...$(NC)"
	@source dmlog_env/bin/activate && \
	echo "$(YELLOW)Upgrading pip...$(NC)" && \
	pip install --upgrade pip setuptools wheel && \
	echo "$(YELLOW)Installing dependencies...$(NC)" && \
	pip install -r requirements.txt && \
	echo "$(YELLOW)Installing development dependencies...$(NC)" && \
	pip install -r requirements-dev.txt || true && \
	echo "$(GREEN)✅ Installation completed successfully!$(NC)"

dev: ## Development - Start development server with auto-reload
	@echo "$(CYAN)Starting DMLog development server...$(NC)"
	@echo "$(BLUE)Server will be available at http://$(APP_HOST):$(APP_PORT)$(NC)"
	@echo "$(BLUE)API docs at http://$(APP_HOST):$(APP_PORT)/docs$(NC)"
	@source dmlog_env/bin/activate && \
	uvicorn $(APP_MODULE) --host $(APP_HOST) --port $(APP_PORT) --reload

dev-bg: ## Development - Start development server in background
	@echo "$(CYAN)Starting DMLog development server in background...$(NC)"
	@source dmlog_env/bin/activate && \
	nohup uvicorn $(APP_MODULE) --host $(APP_HOST) --port $(APP_PORT) --reload > logs/dev_server.log 2>&1 & \
	echo $$! > .dev_server.pid && \
	echo "$(GREEN)✅ Development server started in background (PID: $$!)$(NC)"

stop-dev: ## Development - Stop background development server
	@echo "$(CYAN)Stopping development server...$(NC)"
	@if [ -f .dev_server.pid ]; then \
		kill $$(cat .dev_server.pid) && \
		rm .dev_server.pid && \
		echo "$(GREEN)✅ Development server stopped$(NC)"; \
	else \
		echo "$(YELLOW)No development server running$(NC)"; \
	fi

format: ## Development - Format code using black and isort
	@echo "$(CYAN)Formatting code...$(NC)"
	@source dmlog_env/bin/activate && \
	black app/ scripts/ tests/ && \
	isort app/ scripts/ tests/ && \
	echo "$(GREEN)✅ Code formatted successfully$(NC)"

format-check: ## Development - Check code formatting without making changes
	@echo "$(CYAN)Checking code formatting...$(NC)"
	@source dmlog_env/bin/activate && \
	black --check app/ scripts/ tests/ && \
	isort --check-only app/ scripts/ tests/ && \
	echo "$(GREEN)✅ Code formatting is correct$(NC)"

lint: ## Development - Run linting tools (flake8, mypy)
	@echo "$(CYAN)Running linting tools...$(NC)"
	@source dmlog_env/bin/activate && \
	flake8 app/ scripts/ tests/ && \
	mypy app/ && \
	echo "$(GREEN)✅ Linting passed$(NC)"

lint-fix: ## Development - Run linting tools with auto-fix where possible
	@echo "$(CYAN)Running linting tools with auto-fix...$(NC)"
	@source dmlog_env/bin/activate && \
	autopep8 --in-place --recursive app/ scripts/ tests/ && \
	echo "$(GREEN)✅ Linting fixes applied$(NC)"

# Testing Commands
test: ## Testing - Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest tests/ -v && \
	echo "$(GREEN)✅ All tests passed$(NC)"

test-cov: ## Testing - Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html && \
	echo "$(GREEN)✅ Tests completed with coverage$(NC)"
	@echo "$(BLUE)Coverage report available at htmlcov/index.html$(NC)"

test-unit: ## Testing - Run unit tests only
	@echo "$(CYAN)Running unit tests...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest tests/unit/ -v && \
	echo "$(GREEN)✅ Unit tests passed$(NC)"

test-integration: ## Testing - Run integration tests only
	@echo "$(CYAN)Running integration tests...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest tests/integration/ -v && \
	echo "$(GREEN)✅ Integration tests passed$(NC)"

test-watch: ## Testing - Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	@source dmlog_env/bin/activate && \
	ptw --runner "python -m pytest tests/ -v"

test-file: ## Testing - Run specific test file (usage: make test-file FILE=tests/test_example.py)
	@echo "$(CYAN)Running tests for $(FILE)...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest $(FILE) -v && \
	echo "$(GREEN)✅ Tests for $(FILE) passed$(NC)"

# Database Commands
db-up: ## Database - Start database services
	@echo "$(CYAN)Starting database services...$(NC)"
	@$(DOCKER_COMPOSE) up -d postgres redis
	@echo "$(GREEN)✅ Database services started$(NC)"

db-down: ## Database - Stop database services
	@echo "$(CYAN)Stopping database services...$(NC)"
	@$(DOCKER_COMPOSE) down postgres redis
	@echo "$(GREEN)✅ Database services stopped$(NC)"

db-migrate: ## Database - Run database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	@source dmlog_env/bin/activate && \
	alembic upgrade head && \
	echo "$(GREEN)✅ Database migrations completed$(NC)"

db-migrate-create: ## Database - Create new migration (usage: make db-migrate-create MSG="Add users table")
	@echo "$(CYAN)Creating migration: $(MSG)$(NC)"
	@source dmlog_env/bin/activate && \
	alembic revision --autogenerate -m "$(MSG)" && \
	echo "$(GREEN)✅ Migration created: $(MSG)$(NC)"

db-reset: ## Database - Reset database to initial state
	@echo "$(RED)⚠️  Resetting database...$(NC)"
	@read -p "Are you sure you want to reset the database? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(DOCKER_COMPOSE) down -v && \
		$(DOCKER_COMPOSE) up -d postgres && \
		sleep 10 && \
		make db-migrate && \
		echo "$(GREEN)✅ Database reset successfully$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled$(NC)"; \
	fi

db-shell: ## Database - Open database shell
	@echo "$(CYAN)Opening database shell...$(NC)"
	@$(DOCKER_COMPOSE) exec postgres psql -U dmlog_user -d dmlog_db

db-backup: ## Database - Create database backup
	@echo "$(CYAN)Creating database backup...$(NC)"
	@mkdir -p backups
	@$(DOCKER_COMPOSE) exec postgres pg_dump -U dmlog_user dmlog_db > backups/dmlog_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup created$(NC)"

db-restore: ## Database - Restore database from backup (usage: make db-restore FILE=backups/backup.sql)
	@echo "$(CYAN)Restoring database from $(FILE)...$(NC)"
	@$(DOCKER_COMPOSE) exec -T postgres psql -U dmlog_user dmlog_db < $(FILE)
	@echo "$(GREEN)✅ Database restored$(NC)"

# Docker Commands
docker-build: ## Docker - Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Docker images built$(NC)"

docker-up: ## Docker - Start all services
	@echo "$(CYAN)Starting all services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ All services started$(NC)"

docker-down: ## Docker - Stop all services
	@echo "$(CYAN)Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ All services stopped$(NC)"

docker-logs: ## Docker - Show logs for all services
	@$(DOCKER_COMPOSE) logs -f

docker-logs-app: ## Docker - Show logs for application service
	@$(DOCKER_COMPOSE) logs -f app

docker-logs-db: ## Docker - Show logs for database service
	@$(DOCKER_COMPOSE) logs -f postgres

docker-clean: ## Docker - Clean up Docker resources
	@echo "$(CYAN)Cleaning up Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup completed$(NC)"

# Cache Commands
cache-clear: ## Utility - Clear Redis cache
	@echo "$(CYAN)Clearing Redis cache...$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli FLUSHALL
	@echo "$(GREEN)✅ Redis cache cleared$(NC)"

cache-info: ## Utility - Show Redis cache information
	@echo "$(CYAN)Redis cache information:$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli INFO

# Log Commands
logs-tail: ## Utility - Tail application logs (usage: make logs-tail LINES=100)
	@echo "$(CYAN)Tailing application logs...$(NC)"
	@tail -n $(or $(LINES),50) logs/app/app.log

logs-error: ## Utility - Show error logs only
	@echo "$(CYAN)Showing error logs...$(NC)"
	@grep "ERROR\|CRITICAL" logs/app/app.log | tail -n 20

logs-watch: ## Utility - Watch logs in real-time
	@echo "$(CYAN)Watching logs in real-time...$(NC)"
	@tail -f logs/app/app.log

# Monitoring Commands
monitor: ## Utility - Start performance monitoring
	@echo "$(CYAN)Starting performance monitoring...$(NC)"
	@source dmlog_env/bin/activate && \
	python dev_tools.py monitor

health: ## Utility - Check system health
	@echo "$(CYAN)Checking system health...$(NC)"
	@source dmlog_env/bin/activate && \
	python dev_tools.py status

# Security Commands
security-check: ## Maintenance - Run security checks
	@echo "$(CYAN)Running security checks...$(NC)"
	@source dmlog_env/bin/activate && \
	bandit -r app/ && \
	safety check && \
	echo "$(GREEN)✅ Security checks passed$(NC)"

security-scan: ## Maintenance - Run comprehensive security scan
	@echo "$(CYAN)Running comprehensive security scan...$(NC)"
	@source dmlog_env/bin/activate && \
	bandit -r app/ -f json -o reports/security_scan.json && \
	safety check --json --output reports/safety_report.json && \
	echo "$(GREEN)✅ Security scan completed$(NC)"
	@echo "$(BLUE)Reports available in reports/ directory$(NC)"

# Documentation Commands
docs-build: ## Utility - Build documentation
	@echo "$(CYAN)Building documentation...$(NC)"
	@mkdir -p docs/_build
	@source dmlog_env/bin/activate && \
	sphinx-build -b html docs/ docs/_build/ && \
	echo "$(GREEN)✅ Documentation built$(NC)"
	@echo "$(BLUE)Documentation available at docs/_build/index.html$(NC)"

docs-serve: ## Utility - Serve documentation locally
	@echo "$(CYAN)Serving documentation...$(NC)"
	@cd docs/_build && \
	python -m http.server 8080

# Performance Commands
performance-test: ## Testing - Run performance tests
	@echo "$(CYAN)Running performance tests...$(NC)"
	@source dmlog_env/bin/activate && \
	locust -f tests/performance/locustfile.py --host=http://localhost:$(APP_PORT) && \
	echo "$(GREEN)✅ Performance tests completed$(NC)"

benchmark: ## Testing - Run application benchmarks
	@echo "$(CYAN)Running application benchmarks...$(NC)"
	@source dmlog_env/bin/activate && \
	python scripts/benchmark.py && \
	echo "$(GREEN)✅ Benchmarks completed$(NC)"

# Backup Commands
backup: ## Maintenance - Create full backup
	@echo "$(CYAN)Creating full backup...$(NC)"
	@mkdir -p backups/backup_$$(date +%Y%m%d_%H%M%S)
	@cp -r app/ backups/backup_$$(date +%Y%m%d_%H%M%S)/
	@cp -r config/ backups/backup_$$(date +%Y%m%d_%H%M%S)/
	@cp requirements.txt backups/backup_$$(date +%Y%m%d_%H%M%S)/
	@make db-backup
	@mv backups/dmlog_backup_*.sql backups/backup_$$(date +%Y%m%d_%H%M%S)/
	@echo "$(GREEN)✅ Full backup created$(NC)"

restore: ## Maintenance - Restore from backup (usage: make restore BACKUP=backup_20231201_120000)
	@echo "$(CYAN)Restoring from backup: $(BACKUP)$(NC)"
	@cp -r backups/$(BACKUP)/app/ ./
	@cp -r backups/$(BACKUP)/config/ ./
	@cp backups/$(BACKUP)/requirements.txt ./
	@make db-restore FILE=backups/$(BACKUP)/*.sql
	@echo "$(GREEN)✅ Restore completed$(NC)"

# Deployment Commands
deploy-staging: ## Deployment - Deploy to staging environment
	@echo "$(CYAN)Deploying to staging environment...$(NC)"
	@source dmlog_env/bin/activate && \
	python scripts/deploy.py --environment staging && \
	echo "$(GREEN)✅ Staging deployment completed$(NC)"

deploy-prod: ## Deployment - Deploy to production environment
	@echo "$(CYAN)Deploying to production environment...$(NC)"
	@echo "$(RED)⚠️  Production deployment requires confirmation$(NC)"
	@read -p "Are you sure you want to deploy to production? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		source dmlog_env/bin/activate && \
		python scripts/deploy.py --environment production && \
		echo "$(GREEN)✅ Production deployment completed$(NC)"; \
	else \
		echo "$(YELLOW)Production deployment cancelled$(NC)"; \
	fi

deploy-check: ## Deployment - Check deployment readiness
	@echo "$(CYAN)Checking deployment readiness...$(NC)"
	@source dmlog_env/bin/activate && \
	python scripts/pre_deployment_check.py && \
	echo "$(GREEN)✅ Deployment readiness check passed$(NC)"

# Build Commands
build: ## Utility - Build application for production
	@echo "$(CYAN)Building application for production...$(NC)"
	@source dmlog_env/bin/activate && \
	python -m PyInstaller --onefile --name dmlog app/main.py && \
	echo "$(GREEN)✅ Application built$(NC)"

build-docker: ## Docker - Build production Docker image
	@echo "$(CYAN)Building production Docker image...$(NC)"
	@docker build -t dmlog:latest -f docker/Dockerfile.prod . && \
	echo "$(GREEN)✅ Production Docker image built$(NC)"

# Maintenance Commands
clean: ## Maintenance - Clean up temporary files and artifacts
	@echo "$(CYAN)Cleaning up temporary files...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	@rm -rf .mypy_cache/ .tox/
	@rm -f .dev_server.pid
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: ## Maintenance - Clean up everything including Docker
	@echo "$(CYAN)Cleaning up all files...$(NC)"
	@make clean
	@make docker-clean
	@rm -rf dmlog_env/
	@rm -rf logs/
	@rm -rf .pytest_cache/
	@echo "$(GREEN)✅ Full cleanup completed$(NC)"

update: ## Maintenance - Update dependencies
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@source dmlog_env/bin/activate && \
	pip install --upgrade -r requirements.txt && \
	pip-compile requirements.in > requirements.txt && \
	echo "$(GREEN)✅ Dependencies updated$(NC)"

check: ## Utility - Run all checks (format, lint, test, security)
	@echo "$(CYAN)Running all checks...$(NC)"
	@make format-check
	@make lint
	@make test
	@make security-check
	@echo "$(GREEN)✅ All checks passed$(NC)"

# Quick start commands
quickstart: ## Development - Quick setup for new developers
	@echo "$(CYAN)Setting up DMLog for development...$(NC)"
	@./setup.sh
	@echo "$(GREEN)✅ Quick start completed$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "$(BLUE)1. Copy .env.example to .env and configure$(NC)"
	@echo "$(BLUE)2. Run 'make dev' to start the development server$(NC)"
	@echo "$(BLUE)3. Visit http://localhost:8000/docs for API documentation$(NC)"

# Utility Commands
version: ## Utility - Show version information
	@echo "$(CYAN)DMLog Version Information:$(NC)"
	@echo "Python: $$(python --version)"
	@echo "Pip: $$(pip --version)"
	@echo "Project: DMLog v1.0.0"
	@if [ -f ".git" ]; then \
		echo "Git: $$(git --version)"; \
		echo "Branch: $$(git branch --show-current)"; \
		echo "Commit: $$(git rev-parse --short HEAD)"; \
	fi

env-info: ## Utility - Show environment information
	@echo "$(CYAN)Environment Information:$(NC)"
	@echo "OS: $$(uname -s)"
	@echo "Architecture: $$(uname -m)"
	@echo "Shell: $$SHELL"
	@echo "Python: $$(which python)"
	@echo "Project Root: $(PROJECT_ROOT)"
	@echo "Virtual Environment: $(PROJECT_ROOT)/dmlog_env"
	@echo "Docker: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose: $$(docker-compose --version 2>/dev/null || echo 'Not installed')"

install-deps: ## Development - Install system dependencies (Ubuntu/Debian)
	@echo "$(CYAN)Installing system dependencies...$(NC)"
	@sudo apt-get update
	@sudo apt-get install -y python3 python3-pip python3-venv \
		build-essential libpq-dev postgresql-client \
		docker.io docker-compose redis-tools \
		curl wget git
	@echo "$(GREEN)✅ System dependencies installed$(NC)"

# Advanced development commands
shell: ## Development - Open Python shell with app context
	@echo "$(CYAN)Opening Python shell with app context...$(NC)"
	@source dmlog_env/bin/activate && \
	python -i -c "from app.main import app; from app.core.config import settings; print('DMLog shell ready!')"

db-seed: ## Database - Seed database with sample data
	@echo "$(CYAN)Seeding database with sample data...$(NC)"
	@source dmlog_env/bin/activate && \
	python scripts/dev/seed_data.py && \
	echo "$(GREEN)✅ Database seeded successfully$(NC)"

# CI/CD Commands
ci-test: ## CI/CD - Run tests for CI environment
	@echo "$(CYAN)Running CI tests...$(NC)"
	@source dmlog_env/bin/activate && \
	pytest tests/ --cov=app --cov-report=xml --junitxml=reports/junit.xml && \
	echo "$(GREEN)✅ CI tests completed$(NC)"

ci-build: ## CI/CD - Build for CI environment
	@echo "$(CYAN)Building for CI environment...$(NC)"
	@make clean
	@make format-check
	@make lint
	@make ci-test
	@make security-check
	@echo "$(GREEN)✅ CI build completed$(NC)"

# Include custom makefile if it exists
-include Makefile.local