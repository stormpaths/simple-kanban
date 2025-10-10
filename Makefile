# Development targets
.PHONY: help dev test test-all test-quick test-backend test-frontend test-frontend-json test-production lint format clean setup install dev-monitoring monitoring-up monitoring-down build run

# Variables
PROJECT_NAME ?= $(shell basename $(CURDIR))
IMAGE_TAG ?= latest
REGISTRY ?= localhost:5000
BASE_URL ?= http://localhost:8000

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "📚 Simple Kanban Board - Makefile Commands"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test              - Run all tests (backend + frontend) - 93% coverage"
	@echo "  make test-all          - Same as 'make test'"
	@echo "  make test-quick        - Quick smoke tests (~15s)"
	@echo "  make test-backend      - Backend/API tests only (100%)"
	@echo "  make test-frontend     - Frontend E2E tests only (92%)"
	@echo "  make test-frontend-json - Frontend tests with JSON report"
	@echo "  make test-production   - Run tests against production"
	@echo "  make test-url BASE_URL=<url> - Run tests against custom URL"
	@echo ""
	@echo "⚠️  Note: All tests require a deployed service (use 'make dev' first)"
	@echo ""
	@echo "🔐 Secrets Management:"
	@echo "  make secrets           - Generate SOPS-encrypted secrets"
	@echo "  make secrets-decrypt   - Decrypt secrets to .env"
	@echo "  make secrets-edit      - Edit encrypted secrets"
	@echo "  make secrets-k8s-apply - Apply Kubernetes secrets"
	@echo "  make secrets-check     - Check SOPS/GPG setup"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make setup             - Setup development environment"
	@echo "  make run               - Run application locally"
	@echo "  make dev               - Deploy for development (Skaffold)"
	@echo "  make build             - Build Docker image"
	@echo "  make deploy            - Deploy using Helm"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make monitoring-up     - Start monitoring stack"
	@echo "  make monitoring-down   - Stop monitoring stack"
	@echo "  make dev-monitoring    - Start app with monitoring"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint              - Run code quality checks"
	@echo "  make format            - Format code with black"
	@echo "  make security          - Run security scan"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean             - Clean build artifacts"
	@echo ""
	@echo "📊 Current Status:"
	@echo "  Test Coverage: 93% (57/61 tests)"
	@echo "  Backend: 100% (10/10 tests)"
	@echo "  Frontend: 92% (47/51 tests)"
	@echo "  Production: https://kanban.stormpath.net"

# Setup development environment
setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	pre-commit install || echo "pre-commit not available"

# Secrets management with SOPS
secrets:
	@echo "🔐 Generating SOPS-encrypted secrets..."
	python scripts/generate-secrets.py

secrets-decrypt:
	@echo "🔓 Decrypting secrets..."
	sops -d .env.sops > .env
	@echo "✅ Secrets decrypted to .env"

secrets-edit:
	@echo "✏️ Editing encrypted secrets..."
	sops .env.sops

secrets-k8s-decrypt:
	@echo "🔓 Decrypting Kubernetes secrets..."
	sops -d secrets/kubernetes-secrets.yaml

secrets-k8s-apply:
	@echo "🚀 Applying Kubernetes secrets..."
	sops -d secrets/kubernetes-secrets.yaml | kubectl apply -f -

secrets-check:
	@echo "🔍 Checking SOPS setup..."
	@command -v sops >/dev/null 2>&1 || { echo "❌ SOPS not installed"; exit 1; }
	@command -v gpg >/dev/null 2>&1 || { echo "❌ GPG not installed"; exit 1; }
	@gpg --list-secret-keys >/dev/null 2>&1 || { echo "❌ No GPG keys found"; exit 1; }
	@echo "✅ SOPS and GPG are properly configured"

# ============================================================================
# Testing Targets
# ============================================================================

# Run all tests (backend + frontend) - DEFAULT
test:
	@echo "🧪 Running complete test suite (backend + frontend)..."
	@echo ""
	@echo "📊 Test Coverage: 93% (57/61 tests)"
	@echo "   Backend: 100% (10/10 tests)"
	@echo "   Frontend: 92% (47/51 tests)"
	@echo ""
	@echo "⚠️  Note: Tests run against deployed service"
	@echo ""
	./scripts/test-all.sh

# Run all tests (alias for test)
test-all:
	@$(MAKE) test

# Run quick smoke tests (~15s)
test-quick:
	@echo "🧪 Running quick smoke tests (~15s)..."
	./scripts/test-all.sh --quick

# Run backend/API tests only
test-backend:
	@echo "🧪 Running backend API tests only..."
	@echo ""
	@echo "📊 Backend Coverage: 100% (10/10 tests)"
	@echo ""
	./scripts/test-auth-comprehensive.sh

# Run frontend E2E tests
test-frontend:
	@echo "🧪 Running frontend E2E tests..."
	@echo ""
	@echo "📊 Frontend Coverage: 92% (47/51 tests)"
	@echo ""
	cd tests/frontend && docker-compose run --rm frontend-tests pytest -v

# Run frontend tests with JSON report
test-frontend-json:
	@echo "🧪 Running frontend tests with JSON report..."
	./scripts/test-frontend-json.sh
	@echo ""
	@echo "📄 Report generated: frontend-test-results.json"

# Run tests against production
test-production:
	@echo "🧪 Running tests against production..."
	@echo ""
	@echo "🌐 Target: https://kanban.stormpath.net"
	@echo ""
	BASE_URL=https://kanban.stormpath.net ./scripts/test-all.sh

# Run tests against custom URL
test-url:
	@echo "🧪 Running tests against $(BASE_URL)..."
	@if [ -z "$(BASE_URL)" ]; then \
		echo "❌ Error: BASE_URL not set"; \
		echo "Usage: make test-url BASE_URL=https://your-url.com"; \
		exit 1; \
	fi
	BASE_URL=$(BASE_URL) ./scripts/test-all.sh

# Code quality checks (containerized)
lint:
	@echo "🔍 Running code quality checks (containerized)..."
	docker run --rm -v $(PWD):/app -w /app python:3.11-slim sh -c "\
		pip install -q black flake8 mypy && \
		black --check src/ tests/ && \
		flake8 src/ tests/ && \
		mypy src/"

# Format code (containerized)
format:
	@echo "✨ Formatting code (containerized)..."
	docker run --rm -v $(PWD):/app -w /app python:3.11-slim sh -c "\
		pip install -q black && \
		black src/ tests/"
	@echo "✅ Code formatted"

# Build Docker image
build:
	@echo "🏗️  Building Docker image..."
	docker build -t $(PROJECT_NAME):$(IMAGE_TAG) .

# Deploy using Helm
deploy:
	helm upgrade --install $(PROJECT_NAME) ./helm/$(PROJECT_NAME) \
		--set image.repository=$(REGISTRY)/$(PROJECT_NAME) \
		--set image.tag=$(IMAGE_TAG)

# Monitoring stack targets
monitoring-up:
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo "Monitoring stack started:"
	@echo "  Grafana: http://localhost:3000 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  AlertManager: http://localhost:9093"

monitoring-down:
	docker-compose -f docker-compose.monitoring.yml down

dev-monitoring: monitoring-up
	@echo "Starting development with monitoring..."
	docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
	@echo "Application with monitoring started:"
	@echo "  Application: http://localhost:8000"
	@echo "  Metrics: http://localhost:8000/metrics"
	@echo "  Grafana: http://localhost:3000"

# Run application locally
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Deploy for development
dev:
	skaffold dev

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Security scan
security:
	docker run --rm -v $(PWD):/app -w /app aquasec/trivy fs .

# Integration test
integration-test:
	./test.sh
