# DMLog Testing Makefile
# Comprehensive testing automation for DMLog project

.PHONY: help install test clean lint format security coverage report all
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
PROJECT_ROOT := $(shell pwd)
SOURCE_DIR := $(PROJECT_ROOT)/source_code
TESTS_DIR := $(PROJECT_ROOT)/tests
RESULTS_DIR := $(PROJECT_ROOT)/test_results
COVERAGE_DIR := $(PROJECT_ROOT)/htmlcov

# Help
help: ## Show this help message
	@echo "DMLog Testing Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install test dependencies
	$(PIP) install -r $(TESTS_DIR)/requirements.txt
	$(PIP) install -e $(SOURCE_DIR)/
	playwright install --with-deps

install-dev: ## Install development dependencies
	$(PIP) install pytest pytest-cov pytest-html pytest-asyncio pytest-xdist
	$(PIP) install black isort flake8 mypy bandit safety
	$(PIP) install pre-commit
	pre-commit install

# Code Quality
lint: ## Run linting checks
	@echo "Running linting checks..."
	flake8 $(SOURCE_DIR)/ --max-line-length=100 --ignore=E203,W503
	mypy $(SOURCE_DIR)/ --ignore-missing-imports --no-strict-optional
	bandit -r $(SOURCE_DIR)/ -f json -o $(RESULTS_DIR)/bandit-report.json || true
	safety check --json --output $(RESULTS_DIR)/safety-report.json || true

format: ## Format code with black and isort
	@echo "Formatting code..."
	black $(SOURCE_DIR)/
	isort $(SOURCE_DIR)/

format-check: ## Check code formatting
	@echo "Checking code formatting..."
	black --check --diff $(SOURCE_DIR)/
	isort --check-only --diff $(SOURCE_DIR)/

# Testing
test: ## Run all tests
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-security

test-fast: ## Run fast tests only (unit tests)
	$(MAKE) test-unit

test-full: ## Run full test suite including E2E and load tests
	$(MAKE) test
	$(MAKE) test-e2e
	$(MAKE) test-load

test-unit: ## Run unit tests with coverage
	@echo "Running unit tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/unit/ \
		-v \
		--cov=$(SOURCE_DIR) \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-fail-under=85 \
		--junitxml=$(RESULTS_DIR)/unit_tests.xml \
		--tb=short

test-integration: ## Run integration tests
	@echo "Running integration tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/integration/ \
		-v \
		--cov=$(SOURCE_DIR) \
		--cov-append \
		--cov-report=xml \
		--junitxml=$(RESULTS_DIR)/integration_tests.xml \
		--tb=short

test-e2e: ## Run end-to-end tests
	@echo "Running E2E tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/e2e/ \
		--browser chromium \
		--junitxml=$(RESULTS_DIR)/e2e_tests.xml \
		--tb=short

test-e2e-firefox: ## Run E2E tests on Firefox
	$(PYTHON) -m pytest $(TESTS_DIR)/e2e/ \
		--browser firefox \
		--junitxml=$(RESULTS_DIR)/e2e_firefox_tests.xml \
		--tb=short

test-security: ## Run security tests
	@echo "Running security tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/security/ \
		-v \
		--junitxml=$(RESULTS_DIR)/security_tests.xml \
		--tb=short

test-performance: ## Run performance tests
	@echo "Running performance tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/performance/ \
		--benchmark-only \
		--benchmark-json=$(RESULTS_DIR)/performance.json \
		--benchmark-html=$(RESULTS_DIR)/performance.html

test-load: ## Run load tests
	@echo "Running load tests..."
	cd $(TESTS_DIR)/load && $(PYTHON) locustfile.py moderate_load

test-load-light: ## Run light load tests
	cd $(TESTS_DIR)/load && $(PYTHON) locustfile.py light

test-load-heavy: ## Run heavy load tests
	cd $(TESTS_DIR)/load && $(PYTHON) locustfile.py heavy

test-load-stress: ## Run stress tests
	cd $(TESTS_DIR)/load && $(PYTHON) locustfile.py stress

test-parallel: ## Run tests in parallel
	$(PYTHON) -m pytest $(TESTS_DIR)/ \
		-n auto \
		--cov=$(SOURCE_DIR) \
		--cov-report=html \
		--junitxml=$(RESULTS_DIR)/parallel_tests.xml

# Coverage
coverage: ## Generate coverage report
	@echo "Generating coverage report..."
	$(PYTHON) $(TESTS_DIR)/utils/coverage_report.py

coverage-html: ## Generate HTML coverage report
	@echo "Opening HTML coverage report..."
	$(PYTHON) -c "import webbrowser; webbrowser.open('$(COVERAGE_DIR)/index.html')"

coverage-badge: ## Generate coverage badge only
	$(PYTHON) $(TESTS_DIR)/utils/coverage_report.py --badge-only

# Reporting
report: ## Generate comprehensive test report
	@echo "Generating test report..."
	$(PYTHON) $(TESTS_DIR)/utils/test_runner.py --generate-report-only

report-html: ## Open HTML test report
	$(PYTHON) -c "import webbrowser; webbrowser.open('$(RESULTS_DIR)/test_report.html')"

# Quality Gates
check-quality: ## Run all quality checks
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) coverage
	@echo "All quality checks passed!"

pre-commit: ## Run pre-commit checks
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test-fast

# Cleanup
clean: ## Clean up test artifacts and cache
	@echo "Cleaning up..."
	rm -rf $(RESULTS_DIR)
	rm -rf $(COVERAGE_DIR)
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-results: ## Clean up test results only
	rm -rf $(RESULTS_DIR)
	rm -rf .coverage
	rm -rf htmlcov

# Docker testing
docker-test: ## Run tests in Docker container
	@echo "Running tests in Docker..."
	docker build -t dmlog-test -f $(TESTS_DIR)/Dockerfile.test .
	docker run --rm -v $(PROJECT_ROOT):/app dmlog-test

docker-load-test: ## Run load tests in Docker
	@echo "Running load tests in Docker..."
	docker build -t dmlog-load-test -f $(TESTS_DIR)/Dockerfile.loadtest .
	docker run --rm dmlog-load-test

# CI/CD helpers
ci-test: ## Run tests for CI (no coverage upload)
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-security

ci-full: ## Run full CI test suite
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) test-e2e
	$(MAKE) test-performance

# Monitoring
watch-test: ## Watch for changes and run tests
	@echo "Watching for changes... (Ctrl+C to stop)"
	@while true; do \
		$(MAKE) test-fast; \
		inotifywait -e modify -r $(SOURCE_DIR)/ $(TESTS_DIR)/unit/ 2>/dev/null || sleep 2; \
	done

# Database testing
db-setup-test: ## Set up test database
	$(PYTHON) $(TESTS_DIR)/utils/setup_test_db.py

db-reset-test: ## Reset test database
	$(PYTHON) $(TESTS_DIR)/utils/reset_test_data.py

# Development helpers
dev-setup: ## Set up complete development environment
	$(MAKE) install-dev
	$(MAKE) db-setup-test
	@echo "Development environment set up complete!"

dev-test: ## Run development-friendly test suite
	$(MAKE) format
	$(MAKE) test-fast
	$(MAKE) lint

# Utilities
show-coverage: ## Show coverage summary
	@echo "Coverage Summary:"
	@if [ -f coverage.xml ]; then \
		grep -o 'line-rate="[0-9.]*"' coverage.xml | head -1 | cut -d'"' -f2 | awk '{printf "Line Coverage: %.1f%%\n", $$1 * 100}'; \
	else \
		echo "No coverage data found. Run 'make test' first."; \
	fi

list-tests: ## List all available tests
	@echo "Unit Tests:"
	@find $(TESTS_DIR)/unit/ -name "test_*.py" -exec basename {} \;
	@echo ""
	@echo "Integration Tests:"
	@find $(TESTS_DIR)/integration/ -name "test_*.py" -exec basename {} \;
	@echo ""
	@echo "E2E Tests:"
	@find $(TESTS_DIR)/e2e/ -name "test_*.py" -exec basename {} \;

# Quick commands
t: test ## Alias for test
tc: test-coverage ## Alias for test with coverage
tf: test-fast ## Alias for fast tests
l: lint ## Alias for lint
f: format ## Alias for format
c: clean ## Alias for clean

# All targets
all: clean install format lint test coverage report ## Run complete test suite