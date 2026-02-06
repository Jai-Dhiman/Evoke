.PHONY: all build up down logs clean dev test seed help

# Default target
all: help

# Build all services
build:
	docker compose build

# Start all services
up:
	docker compose up -d

# Start with logs
dev:
	docker compose up

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Clean up volumes and containers
clean:
	docker compose down -v --remove-orphans
	rm -rf data/

# Initialize data directory
init-data:
	mkdir -p data/images data/audio data/embeddings

# Download ML models
download-models:
	./scripts/download_models.sh

# Seed Milvus with sample data
seed:
	docker compose exec ml python /app/scripts/seed_milvus.py

# Run backend tests
test-backend:
	cd backend && go test ./...

# Run frontend tests
test-frontend:
	cd frontend && bun test

# Run ML tests
test-ml:
	cd ml && uv run pytest

# Run all tests
test: test-backend test-frontend test-ml

# Health check
health:
	@echo "Checking services..."
	@curl -s http://localhost:8080/health | jq . || echo "Backend not responding"

# Help
help:
	@echo "Evoke - Music to Visual Inspiration"
	@echo ""
	@echo "Usage:"
	@echo "  make build           Build all Docker images"
	@echo "  make up              Start all services (detached)"
	@echo "  make dev             Start all services with logs"
	@echo "  make down            Stop all services"
	@echo "  make logs            View service logs"
	@echo "  make clean           Remove containers and volumes"
	@echo "  make init-data       Create data directories"
	@echo "  make download-models Download ML models"
	@echo "  make seed            Seed Milvus with sample embeddings"
	@echo "  make test            Run all tests"
	@echo "  make health          Check service health"
