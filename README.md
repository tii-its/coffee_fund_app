# Coffee Fund Web App

A team coffee fund management application with consumption tracking and cash movement management.

## Features

- Track product consumption for team members
- Manage cash deposits and payouts with two-person confirmation
- Multi-user concurrent support (kiosk, desktop, mobile)
- Internationalization support (German/English)
- Role-based access (User/Treasurer)
- Audit logging for all actions

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start development environment:
   ```bash
   make dev
   ```

3. Run migrations:
   ```bash
   make migrate
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Commands

- `make dev` - Start development environment
- `make test` - Run all tests
- `make lint` - Run linting
- `make migrate` - Run database migrations
- `make clean` - Clean up containers and volumes
- `reset-treasurer-pin` Reset treasurer PIN to 1234

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, i18next
- **Testing**: Pytest, Vitest, Playwright
- **Development**: Docker Compose, Makefile

## Project layout

Top-level folders you will work with:

- `backend/` - FastAPI application, models, schemas, services, tests and alembic migrations
- `frontend/` - React + Vite single page app (TypeScript), i18n, components and pages
- `infra/` - docker-compose files and nginx reverse-proxy configuration

See the in-repo `/.github/copilot-instructions.md` for additional agent-focused guidelines.

## Setup & Development

Prerequisites: Docker (or Python 3.11 + Node 18+ to run services locally without Docker).

1. Copy environment file and edit secrets as needed:
    ```bash
    cp .env.example .env
    ```

2. Start the development stack (recommended):
    ```bash
    make dev
    ```

    This will build and start the backend, frontend and a local PostgreSQL container. The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

3. Run migrations after the database is up:
    ```bash
    make migrate
    ```

If you prefer to run services locally without Docker, run the backend with the virtualenv and the frontend with `npm run dev` inside `frontend/`.

## Running tests

- Run all tests (backend + frontend):
   ```bash
   make test
   ```

- Backend only (inside `backend/`):
   ```bash
   # from repo root
   make test-backend
   ```

- Frontend unit tests (Vitest) and E2E (Playwright) are configured in `frontend/`. See `frontend/package.json` and `frontend/vitest.config.ts` for details.

Notes about tests
- The backend tests run against SQLite in-memory for speed. Some database features (Postgres enums, JSON, UUID) are adapted for SQLite using custom TypeDecorators in `backend/app/tests/conftest.py`. If you see sqlite-related errors during tests, prefer running the failing test alone to inspect stack traces:

   ```bash
   # run a single pytest file
   pytest backend/app/tests/test_some_file.py -q
   ```

## Troubleshooting & common pitfalls

- KeyError 'id' in tests: many integration fixtures create resources via the API and expect a 201 response with an `id` field in the returned JSON. If an endpoint returns HTTP 200 or returns an error payload, tests that call `response.json()["id"]` will raise KeyError. To debug:
   - Re-run the failing test and inspect `response.status_code` and `response.text` or `response.json()` to see the payload.
   - Ensure API create endpoints use `status_code=201` and return Pydantic response models (not raw SQLAlchemy models) so the JSON shape is stable.

- SQLite "no such table" errors in tests: the test harness builds SQLAlchemy metadata using the in-memory engine. If model imports happen before the test fixture sets up the custom SQLite types, table creation may fail. Fixes:
   - Ensure `app.db.types` provides SQLite-compatible TypeDecorators, or
   - Monkeypatch/import test TypeDecorators before model imports in `conftest.py`.

- Enum conflicts / alembic migrations: PostgreSQL enum types are created with raw SQL in alembic migrations. If you change enum definitions, create a new migration and use `op.execute("CREATE TYPE IF NOT EXISTS ...")` patterns.

## Developer notes

- REST status codes: create endpoints should return HTTP 201 on success. Returning SQLAlchemy model instances directly can lead to inconsistent JSON shapes; prefer returning Pydantic schema objects (Pydantic v2 `.model_dump()`).
- Audit logging: all mutations should create an audit entry. Check `backend/app/services/audit.py` for helpers.

If you need help reproducing a failing test locally, open an issue with the failing test name and the traceback and we can triage it further.