.PHONY: install start stop build push deploy migrate test lint clean help

# Default registry and image prefix
REGISTRY ?= ghcr.io
ORG ?= kubegraf
TAG ?= latest

# Docker compose file
COMPOSE_FILE = docker-compose.yml

help: ## Show this help message
	@echo "SEO Automation Platform - Available Commands"
	@echo "============================================"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install all Python dependencies locally
	@echo "Installing shared dependencies..."
	pip install -r shared/requirements.txt 2>/dev/null || true
	@for service in scheduler keyword_discovery competitor_analysis content_generation seo_optimization publishing backlink_automation seo_analytics; do \
		echo "Installing $$service dependencies..."; \
		pip install -r services/$$service/requirements.txt 2>/dev/null || true; \
	done
	@echo "Installing dashboard dependencies..."
	pip install -r dashboard/requirements.txt 2>/dev/null || true
	@echo "Done!"

start: ## Start all services with Docker Compose
	@echo "Starting SEO Automation Platform..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "Services started. Dashboard available at http://localhost:8501"

stop: ## Stop all services
	@echo "Stopping all services..."
	docker compose -f $(COMPOSE_FILE) down

restart: ## Restart all services
	$(MAKE) stop
	$(MAKE) start

logs: ## Show logs for all services
	docker compose -f $(COMPOSE_FILE) logs -f

logs-scheduler: ## Show scheduler logs
	docker compose -f $(COMPOSE_FILE) logs -f scheduler

logs-content: ## Show content generation logs
	docker compose -f $(COMPOSE_FILE) logs -f content-generation

##@ Build

build: ## Build all Docker images
	@echo "Building all Docker images..."
	docker compose -f $(COMPOSE_FILE) build --parallel
	@echo "Build complete!"

build-push: ## Build and push all Docker images to registry
	$(MAKE) build
	$(MAKE) push

push: ## Push all Docker images to registry
	@echo "Pushing images to $(REGISTRY)/$(ORG)..."
	@for service in scheduler keyword-discovery competitor-analysis content-generation seo-optimization publishing backlink-automation seo-analytics dashboard; do \
		docker tag seo-automation-$$service:latest $(REGISTRY)/$(ORG)/seo-$$service:$(TAG); \
		docker push $(REGISTRY)/$(ORG)/seo-$$service:$(TAG); \
	done

##@ Database

migrate: ## Run database migrations
	@echo "Running Alembic migrations..."
	docker compose -f $(COMPOSE_FILE) run --rm scheduler alembic -c /app/migrations/alembic.ini upgrade head
	@echo "Migrations complete!"

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	docker compose -f $(COMPOSE_FILE) run --rm scheduler alembic -c /app/migrations/alembic.ini revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	docker compose -f $(COMPOSE_FILE) run --rm scheduler alembic -c /app/migrations/alembic.ini downgrade -1

##@ Kubernetes Deployment

deploy: ## Deploy to Kubernetes via Helm
	@echo "Deploying SEO Automation to Kubernetes..."
	helm upgrade --install seo-automation ./helm/seo-automation \
		--namespace seo-automation \
		--create-namespace \
		--values ./helm/seo-automation/values.yaml \
		--set image.tag=$(TAG)
	@echo "Deployment complete!"

deploy-dry-run: ## Dry run Helm deployment
	helm upgrade --install seo-automation ./helm/seo-automation \
		--namespace seo-automation \
		--create-namespace \
		--values ./helm/seo-automation/values.yaml \
		--dry-run --debug

k8s-apply: ## Apply raw Kubernetes manifests
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/postgres.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/ingress.yaml

k8s-delete: ## Delete Kubernetes resources
	kubectl delete -f k8s/ --ignore-not-found

##@ Pipeline

pipeline: ## Run the full SEO pipeline manually
	@echo "Triggering full SEO pipeline..."
	curl -X POST http://localhost:8000/trigger/full-pipeline

pipeline-keywords: ## Run keyword discovery only
	curl -X POST http://localhost:8001/run

pipeline-competitors: ## Run competitor analysis only
	curl -X POST http://localhost:8002/run

pipeline-content: ## Run content generation only
	curl -X POST http://localhost:8003/run

pipeline-optimize: ## Run SEO optimization only
	curl -X POST http://localhost:8004/run

pipeline-publish: ## Run publishing only
	curl -X POST http://localhost:8005/run

##@ Testing & Quality

test: ## Run all tests
	@echo "Running tests..."
	pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

lint: ## Run linting (flake8, black, isort)
	@echo "Running linters..."
	black --check services/ shared/ dashboard/
	isort --check-only services/ shared/ dashboard/
	flake8 services/ shared/ dashboard/ --max-line-length=100

format: ## Auto-format code
	black services/ shared/ dashboard/
	isort services/ shared/ dashboard/

type-check: ## Run type checking
	mypy services/ shared/ --ignore-missing-imports

##@ Utilities

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

status: ## Show status of all services
	docker compose -f $(COMPOSE_FILE) ps

shell-scheduler: ## Open shell in scheduler container
	docker compose -f $(COMPOSE_FILE) exec scheduler /bin/bash

shell-db: ## Open PostgreSQL shell
	docker compose -f $(COMPOSE_FILE) exec postgres psql -U seo_user -d seo_automation

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Scheduler: DOWN"
	@curl -s http://localhost:8001/health | python3 -m json.tool || echo "Keyword Discovery: DOWN"
	@curl -s http://localhost:8002/health | python3 -m json.tool || echo "Competitor Analysis: DOWN"
	@curl -s http://localhost:8003/health | python3 -m json.tool || echo "Content Generation: DOWN"
	@curl -s http://localhost:8004/health | python3 -m json.tool || echo "SEO Optimization: DOWN"
	@curl -s http://localhost:8005/health | python3 -m json.tool || echo "Publishing: DOWN"
	@curl -s http://localhost:8007/health | python3 -m json.tool || echo "SEO Analytics: DOWN"
