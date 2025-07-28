# Makefile
.PHONY: help build up down logs test test-load clean scale dev-up dev-down shell

help:
	@echo "Available commands:"
	@echo "  make build       - Build all production Docker images"
	@echo "  make up          - Start all services in production mode"
	@echo "  make down        - Stop all services in production mode"
	@echo "  make logs        - Show logs from all services"
	@echo "  make test        - Run unit tests"
	@echo "  make test-load   - Run load tests with hey"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make scale N=X   - Scale application to X instances"
	@echo "  make dev-build   - Build development Docker images"
	@echo "  make dev-up      - Start services in development mode"
	@echo "  make dev-down    - Stop development services"
	@echo "  make shell       - Access app container shell"

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
	@echo "   - Metrics: http://localhost:8001/metrics"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000 (admin/admin)"
	@echo "   - Loki: http://localhost:3100"

down:
	docker-compose -f docker-compose.yml down

logs:
	docker-compose -f docker-compose.yml logs -f

# Testing commands
test:
	docker-compose -f docker-compose.yml exec app pytest tests/unit -v

test-integration:
	docker-compose -f docker-compose.yml exec app pytest tests/integration -v

test-load:
	@echo "Running load test with 300 concurrent connections..."
	@command -v hey >/dev/null 2>&1 || { echo "hey not installed. Install with: go install github.com/rakyll/hey@latest"; exit 1; }
	hey -n 10000 -c 300 -q 10 http://localhost:8000/api/v1/prices/eth-usdt

test-stress:
	@echo "Running stress test for 60 seconds..."
	hey -z 60s -c 300 http://localhost:8000/api/v1/prices/eth-usdt

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
	docker-compose -f docker-compose.yml exec app ruff check src/
	docker-compose -f docker-compose.yml exec app mypy src/

format:
	@echo "Formatting code..."
	docker-compose -f docker-compose.yml exec app black src/ tests/
	docker-compose -f docker-compose.yml exec app ruff check --fix src/