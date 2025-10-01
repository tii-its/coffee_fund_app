.PHONY: dev test lint clean migrate build

# Development
dev:
	docker compose -f infra/docker-compose.dev.yml up --build

dev-bg:
	docker compose -f infra/docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f infra/docker-compose.dev.yml down

# Production
build:
	docker compose -f infra/docker-compose.prod.yml build

prod:
	docker compose -f infra/docker-compose.prod.yml up -d

prod-down:
	docker compose -f infra/docker-compose.prod.yml down

# Database
migrate:
	docker compose -f infra/docker-compose.dev.yml exec backend alembic upgrade head

migrate-generate:
	docker compose -f infra/docker-compose.dev.yml exec backend alembic revision --autogenerate -m "$(msg)"

migrate-reset:
	docker compose -f infra/docker-compose.dev.yml exec backend alembic downgrade base
	docker compose -f infra/docker-compose.dev.yml exec backend alembic upgrade head

# Testing
test:
	docker compose -f infra/docker-compose.dev.yml up -d --build
	docker compose -f infra/docker-compose.dev.yml exec backend pytest
	docker compose -f infra/docker-compose.dev.yml exec frontend npm test
	docker compose -f infra/docker-compose.dev.yml down

test-backend:
	docker compose -f infra/docker-compose.dev.yml up -d --build
	docker compose -f infra/docker-compose.dev.yml exec backend pytest
	docker compose -f infra/docker-compose.dev.yml down

test-frontend:
	docker compose -f infra/docker-compose.dev.yml up -d --build
	docker compose -f infra/docker-compose.dev.yml exec frontend npm test
	docker compose -f infra/docker-compose.dev.yml down

test-frontend-typecheck:
	docker compose -f infra/docker-compose.dev.yml exec frontend npm run typecheck

test-e2e:
	docker compose -f infra/docker-compose.dev.yml exec frontend npm run test:e2e

# Linting
lint:
	docker compose -f infra/docker-compose.dev.yml exec backend ruff check app/
	docker compose -f infra/docker-compose.dev.yml exec backend black --check app/
	docker compose -f infra/docker-compose.dev.yml exec frontend npm run lint

lint-fix:
	docker compose -f infra/docker-compose.dev.yml exec backend ruff check --fix app/
	docker compose -f infra/docker-compose.dev.yml exec backend black app/
	docker compose -f infra/docker-compose.dev.yml exec frontend npm run lint:fix

# Cleanup
clean:
	docker compose -f infra/docker-compose.dev.yml down -v
	docker compose -f infra/docker-compose.prod.yml down -v
	docker system prune -f

# Logs
logs:
	docker compose -f infra/docker-compose.dev.yml logs -f

logs-backend:
	docker compose -f infra/docker-compose.dev.yml logs -f backend

logs-frontend:
	docker compose -f infra/docker-compose.dev.yml logs -f frontend

# Shell access
shell-backend:
	docker compose -f infra/docker-compose.dev.yml exec backend bash

shell-frontend:
	# Use bash if present, otherwise fall back to sh (Alpine images often lack bash)
	docker compose -f infra/docker-compose.dev.yml exec frontend sh -c 'if command -v bash >/dev/null 2>&1; then exec bash; else exec sh; fi'

shell-db:
	docker compose -f infra/docker-compose.dev.yml exec db psql -U coffee -d coffee

# (Removed) Global PIN reset targets: PINs are per-user and managed via user endpoints.

# Bootstrap initial admin (idempotent: only creates if none exists)
bootstrap-admin:
	docker compose -f infra/docker-compose.dev.yml exec backend python -m scripts.bootstrap_admin