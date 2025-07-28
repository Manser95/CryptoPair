# Makefile
.PHONY: help build up down logs test test-unit test-integration test-load test-stress test-all test-docker test-ci clean scale dev-build dev-up dev-down dev-logs shell redis-cli grafana prometheus loki health lint format install-deps poetry-install k6-test locust-test locust-cluster-up locust-cluster-down locust-scale locust-cluster-logs locust-basic locust-stress locust-endurance setup-test

help:
	@echo "Available commands:"
	@echo "  make build               - Build all production Docker images"
	@echo "  make up                  - Start all services and open Grafana"
	@echo "  make down                - Stop all services in production mode"
	@echo "  make logs                - Show logs from all services"
	@echo "  make test                - Run all tests (unit + integration)"
	@echo "  make test-unit           - Run unit tests only"
	@echo "  make test-integration    - Run integration tests only"
	@echo "  make test-docker         - Run all tests in Docker with test environment"
	@echo "  make test-ci             - Run tests in CI mode (build, test, cleanup)"
	@echo "  make setup-test          - Quick setup for new developers (Docker only)"
	@echo "  make test-load           - Run load tests with hey"
	@echo "  make test-stress         - Run stress test for 60 seconds"
	@echo "  make k6-test             - Run k6 load tests"
	@echo "  make locust-test         - Run locust load tests (standalone)"
	@echo "  make locust-cluster-up   - Start Locust cluster (master + workers)"
	@echo "  make locust-scale N=X    - Scale Locust to X workers"
	@echo "  make locust-cluster-down - Stop Locust cluster"
	@echo "  make locust-basic        - Run basic load test (300 users)"
	@echo "  make locust-stress       - Run stress test (500 users)"
	@echo "  make locust-endurance    - Run endurance test (10 min)"
	@echo "  make benchmark           - Run performance benchmark suite"
	@echo "  make benchmark-quick     - Run quick performance benchmark"
	@echo "  make clean               - Clean up containers and volumes"
	@echo "  make scale N=X           - Scale application to X instances"
	@echo "  make dev-build           - Build development Docker images"
	@echo "  make dev-up              - Start services in development mode"
	@echo "  make dev-down            - Stop development services"
	@echo "  make dev-logs            - Show development logs"
	@echo "  make shell               - Access app container shell"
	@echo "  make redis-cli           - Access Redis CLI"
	@echo "  make grafana             - Open Grafana dashboard"
	@echo "  make prometheus          - Open Prometheus UI"
	@echo "  make loki                - Check Loki logs UI"
	@echo "  make health              - Check service health status"
	@echo "  make lint                - Run code linters"
	@echo "  make format              - Format code"
	@echo "  make install-deps        - Install dependencies locally"
	@echo "  make poetry-install      - Install with Poetry"

# Production commands
build:
	docker-compose -f docker-compose.yml build

up:
	docker-compose -f docker-compose.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@docker-compose -f docker-compose.yml ps
	@echo ""
	@echo "✅ Services are running:"
	@echo "   - API: http://localhost:8000"
	@echo "   - Health: http://localhost:8000/health"
	@echo "   - Metrics: http://localhost:8000/metrics"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000 (admin/admin)"
	@echo "   - Loki: http://localhost:3100"
	@echo ""
	@echo "Opening Grafana dashboard..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

down:
	docker-compose -f docker-compose.yml down

logs:
	docker-compose -f docker-compose.yml logs -f

# Testing commands
test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	docker-compose -f docker-compose.yml exec app pytest tests/unit -v

test-integration:
	@echo "Running integration tests..."
	docker-compose -f docker-compose.yml exec app pytest tests/integration -v

test-all:
	@echo "Running all tests with coverage..."
	docker-compose -f docker-compose.yml exec app pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Docker-based testing with isolated environment
test-docker:
	@echo "🐳 Building test environment..."
	@docker-compose -f docker-compose.test.yml build
	@echo ""
	@echo "🚀 Starting test dependencies..."
	@sleep 2
	@echo ""
	@echo "🧪 Running all tests in Docker..."
	@docker-compose -f docker-compose.test.yml run --rm test pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html:coverage
	@echo ""
	@echo "🧹 Cleaning up test environment..."
	@docker-compose -f docker-compose.test.yml down -v
	@echo ""
	@echo "✅ Tests completed! Coverage report available in ./coverage/"

# CI-friendly test command
test-ci:
	@echo "🏗️  CI Test Pipeline Starting..."
	@echo "Step 1/4: Building test Docker image..."
	@docker-compose -f docker-compose.test.yml build --no-cache
	@echo ""
	@echo "Step 2/4: Starting test environment..."
	@docker-compose -f docker-compose.test.yml up -d
	@sleep 3
	@echo ""
	@echo "Step 3/4: Running tests..."
	@docker-compose -f docker-compose.test.yml run --rm test pytest tests/ -v --tb=short --junitxml=test-results.xml --cov=src --cov-report=xml --cov-report=term
	@echo ""
	@echo "Step 4/4: Cleanup..."
	@docker-compose -f docker-compose.test.yml down -v
	@echo "✅ CI pipeline completed!"

# Quick setup for new developers
setup-test:
	@echo "🚀 Quick Setup for New Developers"
	@echo ""
	@echo "📋 Checking requirements..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Docker from https://docker.com"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found. Please install Docker Compose"; exit 1; }
	@command -v make >/dev/null 2>&1 || { echo "❌ Make not found. Please install Make"; exit 1; }
	@echo "✅ All requirements satisfied"
	@echo ""
	@echo "🐳 Building Docker images..."
	@docker-compose -f docker-compose.yml build --quiet
	@docker-compose -f docker-compose.test.yml build --quiet
	@echo ""
	@echo "🧪 Running tests in Docker..."
	@docker-compose -f docker-compose.test.yml run --rm test pytest tests/ -v --tb=short --maxfail=3
	@echo ""
	@echo "✅ Setup complete! Available commands:"
	@echo "   - make test-docker    # Run all tests in Docker (recommended)"
	@echo "   - make test-ci        # Run tests in CI mode"
	@echo "   - make up             # Start the application"
	@echo "   - make help           # Show all available commands"

test-load:
	@echo "Running load test with 300 concurrent connections..."
	@command -v hey >/dev/null 2>&1 || { echo "hey not installed. Install with: go install github.com/rakyll/hey@latest"; exit 1; }
	hey -n 10000 -c 300 -q 10 http://localhost:8000/api/v1/prices/eth-usdt

test-stress:
	@echo "Running stress test for 60 seconds..."
	@command -v hey >/dev/null 2>&1 || { echo "hey not installed. Install with: go install github.com/rakyll/hey@latest"; exit 1; }
	hey -z 60s -c 300 http://localhost:8000/api/v1/prices/eth-usdt

k6-test:
	@echo "Running k6 load tests..."
	@command -v k6 >/dev/null 2>&1 || { echo "k6 not installed. Install from: https://k6.io/docs/getting-started/installation"; exit 1; }
	k6 run tests/load/k6_test.js

locust-test:
	@echo "Running locust load tests in standalone mode..."
	@echo "Building test image with locust..."
	@docker-compose -f docker-compose.test.yml build test
	@echo "Starting Locust web UI..."
	@echo "Locust web UI will be available at http://localhost:8089"
	@echo "Press Ctrl+C to stop"
	docker-compose -f docker-compose.test.yml run --rm -p 8089:8089 test locust -f tests/load/locustfile.py --host=http://host.docker.internal:8000 --web-host=0.0.0.0 --web-port=8089

# Cluster mode Locust commands for high-performance testing
locust-cluster-up:
	@echo "🚀 Starting Locust in cluster mode (master + 4 workers)..."
	@echo "Building images..."
	@docker-compose -f docker-compose.test.yml build locust-master locust-worker
	@echo "Starting Locust master..."
	@docker-compose -f docker-compose.test.yml up -d locust-master
	@echo "Starting Locust workers..."
	@docker-compose -f docker-compose.test.yml up -d --scale locust-worker=4 locust-worker
	@echo ""
	@echo "✅ Locust cluster is running!"
	@echo "   - Web UI: http://localhost:8089"
	@echo "   - Workers: 4 (use 'make locust-scale N=X' to change)"
	@echo ""
	@echo "Opening Locust web UI..."
	@open http://localhost:8089 2>/dev/null || xdg-open http://localhost:8089 2>/dev/null || echo "Please open http://localhost:8089 in your browser"

locust-scale:
	@if [ -z "$(N)" ]; then echo "Usage: make locust-scale N=8"; exit 1; fi
	@echo "Scaling Locust workers to $(N)..."
	@docker-compose -f docker-compose.test.yml up -d --scale locust-worker=$(N) locust-worker
	@echo "✅ Scaled to $(N) workers"

locust-cluster-down:
	@echo "Stopping Locust cluster..."
	@docker-compose -f docker-compose.test.yml stop locust-master locust-worker
	@docker-compose -f docker-compose.test.yml rm -f locust-master locust-worker

locust-cluster-logs:
	@docker-compose -f docker-compose.test.yml logs -f locust-master locust-worker

# Pre-configured load test scenarios
locust-basic:
	@echo "Running basic load test (300 users over 30 seconds)..."
	@docker-compose -f docker-compose.test.yml run --rm test \
		locust -f tests/load/locustfile.py --host=http://host.docker.internal:8000 \
		--headless --users=300 --spawn-rate=10 --run-time=30s \
		--html=tests/load/reports/basic-test.html

locust-stress:
	@echo "Running stress test (500 users, high spawn rate)..."
	@docker-compose -f docker-compose.test.yml run --rm test \
		locust -f tests/load/locustfile.py --host=http://host.docker.internal:8000 \
		--headless --users=500 --spawn-rate=50 --run-time=2m \
		--html=tests/load/reports/stress-test.html

locust-endurance:
	@echo "Running endurance test (300 users for 10 minutes)..."
	@docker-compose -f docker-compose.test.yml run --rm test \
		locust -f tests/load/locustfile.py --host=http://host.docker.internal:8000 \
		--headless --users=300 --spawn-rate=5 --run-time=10m \
		--html=tests/load/reports/endurance-test.html

benchmark:
	@echo "Running performance benchmark suite..."
	@echo "Building test image..."
	@docker-compose -f docker-compose.test.yml build test
	@echo "Running benchmark..."
	docker-compose -f docker-compose.test.yml run --rm test python tests/load/performance_benchmark.py --url=http://host.docker.internal:8000

benchmark-quick:
	@echo "Running quick performance benchmark..."
	@echo "Building test image..."
	@docker-compose -f docker-compose.test.yml build test
	@echo "Running quick benchmark..."
	docker-compose -f docker-compose.test.yml run --rm test python tests/load/performance_benchmark.py --url=http://host.docker.internal:8000 --quick

# Cleanup
clean:
	docker-compose -f docker-compose.yml down -v
	docker system prune -f

# Scaling
scale:
	@if [ -z "$(N)" ]; then echo "Usage: make scale N=3"; exit 1; fi
	docker-compose -f docker-compose.yml up -d --scale app=$(N)
	@echo "Scaled to $(N) instances"

# Development commands
dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Utility commands
shell:
	docker-compose -f docker-compose.yml exec app /bin/bash

redis-cli:
	docker-compose -f docker-compose.yml exec redis redis-cli

# Code quality
lint:
	@echo "Running linters..."
	docker-compose -f docker-compose.yml exec app ruff check src/ tests/
	docker-compose -f docker-compose.yml exec app mypy src/

format:
	@echo "Formatting code..."
	docker-compose -f docker-compose.yml exec app black src/ tests/
	docker-compose -f docker-compose.yml exec app ruff check --fix src/ tests/

# Local development
install-deps:
	@echo "Installing dependencies with Poetry..."
	@command -v poetry >/dev/null 2>&1 || { echo "Poetry not installed. Install from: https://python-poetry.org/docs/#installation"; exit 1; }
	poetry install --with dev

poetry-install: install-deps

# Monitoring commands
grafana:
	@echo "Opening Grafana dashboard..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

prometheus:
	@echo "Opening Prometheus UI..."
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "Please open http://localhost:9090 in your browser"

loki:
	@echo "Loki logs can be viewed in Grafana..."
	@echo "Direct Loki API: http://localhost:3100"
	@echo "Opening Grafana for logs viewing..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

# Health check
health:
	@echo "Checking service health..."
	@echo ""
	@echo "API Health:"
	@curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "❌ API is not responding"
	@echo ""
	@echo "Prometheus Health:"
	@curl -s http://localhost:9090/-/healthy 2>/dev/null && echo "✅ Prometheus is healthy" || echo "❌ Prometheus is not healthy"
	@echo ""
	@echo "Grafana Health:"
	@curl -s http://localhost:3000/api/health | jq . 2>/dev/null || echo "❌ Grafana is not responding"
	@echo ""
	@echo "Loki Health:"
	@curl -s http://localhost:3100/ready 2>/dev/null && echo "✅ Loki is ready" || echo "❌ Loki is not ready"

# Docker management
prune:
	@echo "Pruning Docker system..."
	docker system prune -af --volumes

# Show running containers
ps:
	docker-compose -f docker-compose.yml ps

# Restart specific service
restart:
	@if [ -z "$(SERVICE)" ]; then echo "Usage: make restart SERVICE=app"; exit 1; fi
	docker-compose -f docker-compose.yml restart $(SERVICE)

# View specific service logs
log:
	@if [ -z "$(SERVICE)" ]; then echo "Usage: make log SERVICE=app"; exit 1; fi
	docker-compose -f docker-compose.yml logs -f $(SERVICE)