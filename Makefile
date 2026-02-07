.PHONY: all build up down logs clean dev test seed precompute deploy help

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

# Pre-compute deployment data (images, directions, demo)
precompute:
	cd ml && uv run python ../scripts/precompute.py

# Pre-compute with demo audio
precompute-demo:
	cd ml && uv run python ../scripts/precompute.py --demo-audio $(DEMO_AUDIO)

# Seed alias (points to precompute now)
seed: precompute

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

# Deploy (build and push to Cloud Run)
deploy: deploy-ml deploy-backend deploy-frontend

deploy-ml:
	gcloud builds submit --tag gcr.io/$(GCP_PROJECT)/evoke-ml ./ml
	gcloud run deploy evoke-ml \
		--image gcr.io/$(GCP_PROJECT)/evoke-ml \
		--region us-central1 \
		--allow-unauthenticated \
		--use-http2 \
		--memory 2Gi --cpu 2 \
		--min-instances 0 --max-instances 1 \
		--timeout 300 --cpu-boost

deploy-backend:
	gcloud builds submit --tag gcr.io/$(GCP_PROJECT)/evoke-backend ./backend
	gcloud run deploy evoke-backend \
		--image gcr.io/$(GCP_PROJECT)/evoke-backend \
		--region us-central1 \
		--allow-unauthenticated \
		--memory 256Mi --cpu 1 \
		--min-instances 0 --max-instances 2

deploy-frontend:
	cd frontend && bun run build
	cd frontend && npx wrangler pages deploy dist --project-name evoke

# Help
help:
	@echo "Evoke - Music to Visual Inspiration"
	@echo ""
	@echo "Usage:"
	@echo "  make build             Build all Docker images"
	@echo "  make up                Start all services (detached)"
	@echo "  make dev               Start all services with logs"
	@echo "  make down              Stop all services"
	@echo "  make logs              View service logs"
	@echo "  make clean             Remove containers and volumes"
	@echo "  make init-data         Create data directories"
	@echo "  make download-models   Download ML models"
	@echo "  make precompute        Pre-compute deployment data"
	@echo "  make seed              Alias for precompute"
	@echo "  make test              Run all tests"
	@echo "  make health            Check service health"
	@echo "  make deploy            Deploy all services"
