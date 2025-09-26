.PHONY: dev test lint clean migrate build

# Development
dev:
	docker compose -f infra/docker-compose.dev.yml up --build

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
	docker compose -f infra/docker-compose.dev.yml exec backend pytest
	docker compose -f infra/docker-compose.dev.yml exec frontend npm test

test-backend:
	docker compose -f infra/docker-compose.dev.yml exec backend pytest

test-frontend:
	docker compose -f infra/docker-compose.dev.yml exec frontend npm test

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
	docker compose -f infra/docker-compose.dev.yml exec frontend bash

shell-db:
	docker compose -f infra/docker-compose.dev.yml exec db psql -U coffee -d coffee