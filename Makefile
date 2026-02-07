.PHONY: all build up down logs clean dev test seed precompute deploy help

# Default target
all: help

# Build all services
build:
	docker compose build

# Start all services (Docker)
up:
	docker compose up -d

# Start with logs (Docker)
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

# Pre-compute deployment data (images, directions, demo)
precompute:
	cd ml && uv run python ../scripts/precompute.py

# Pre-compute with demo audio
precompute-demo:
	cd ml && uv run python ../scripts/precompute.py --demo-audio $(DEMO_AUDIO)

# Seed alias (points to precompute now)
seed: precompute

# Run worker locally (requires frontend build)
worker:
	cd worker && bun run dev

# Run frontend dev server
frontend:
	cd frontend && bun run dev

# Run ML service locally
ml:
	cd ml && uv run uvicorn src.http_server:app --port 8000

# Run frontend tests
test-frontend:
	cd frontend && bun test

# Run ML tests
test-ml:
	cd ml && uv run pytest

# Run all tests
test: test-frontend test-ml

# Health check
health:
	@echo "Checking services..."
	@curl -s http://localhost:8787/health | jq . || echo "Worker not responding"

# Deploy ML to Cloud Run
deploy-ml:
	gcloud builds submit --tag gcr.io/$(GCP_PROJECT)/evoke-ml ./ml
	gcloud run deploy evoke-ml \
		--image gcr.io/$(GCP_PROJECT)/evoke-ml \
		--region us-central1 \
		--allow-unauthenticated \
		--memory 2Gi --cpu 2 \
		--min-instances 0 --max-instances 1 \
		--timeout 300 --cpu-boost

# Deploy Worker to Cloudflare
deploy-worker:
	cd frontend && bun run build
	cd worker && bun run deploy

# Deploy all
deploy: deploy-ml deploy-worker

# Help
help:
	@echo "Evoke - Music to Visual Inspiration"
	@echo ""
	@echo "Usage:"
	@echo "  make build             Build Docker images"
	@echo "  make up                Start Docker services (detached)"
	@echo "  make dev               Start Docker services with logs"
	@echo "  make down              Stop Docker services"
	@echo "  make logs              View service logs"
	@echo "  make clean             Remove containers and volumes"
	@echo "  make worker            Run Hono worker locally (:8787)"
	@echo "  make frontend          Run frontend dev server (:3000)"
	@echo "  make ml                Run ML service locally (:8000)"
	@echo "  make precompute        Pre-compute deployment data"
	@echo "  make test              Run all tests"
	@echo "  make health            Check service health"
	@echo "  make deploy            Deploy all services"
