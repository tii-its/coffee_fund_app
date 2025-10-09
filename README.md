# Coffee Fund Web App

A team coffee fund management application with consumption tracking and cash movement management.

## Features

* Product consumption tracking
* Cash deposits & payouts with enforced two-person confirmation (creator ≠ confirmer)
* Self-service top-up (user-initiated deposit request) via per‑user PIN (no traditional login session)
* Multi-user concurrent usage (kiosk, desktop, mobile)
* Internationalization (German/English) with runtime toggle
* Role-based access (User / Treasurer) — every user has a mandatory individual PIN (no global/shared PIN)
* Per-action PIN re-entry for sensitive flows (e.g. top-up modal)
* PIN management: user can change own PIN; admin can reset a user PIN to default (1234)
* Comprehensive audit logging
* Safe user deactivation / deletion rules (last remaining admin protected)

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
   (All sensitive actions rely on per-user PINs; no global/shared admin or treasurer PIN remains. Each privileged action can ask for the actor PIN again — no client-side PIN storage.)

## Per-User PIN Model

The application is intentionally stateless regarding authentication. Instead of persistent sessions:

1. A user is selected (e.g. on the Dashboard or Kiosk).
2. The user enters their personal PIN to gain temporary view access.
3. Additional sensitive actions (e.g. requesting a top-up) require re-entering the PIN inside the action modal.
4. Treasurer confirmations require a different treasurer’s PIN (two-person rule).

Implications:
* No browser session cookies for auth; each action validates intent explicitly.
* PINs are hashed (SHA-256) server-side; never logged or stored in plaintext.
* UI must not cache the PIN; components treat PIN input as ephemeral.

## Self-Service Top-Up Flow

Users can request a deposit for their own account without a treasurer initiating it:

1. Select user on Dashboard → enter PIN (grants access to that user context)
2. Click "Top Up Balance"
3. In the Top-Up modal enter amount, optional note, and re-enter PIN (second factor of intent)
4. A pending money move of type `deposit` is created (status = `pending`)
5. A different treasurer later confirms the pending move; only then balance updates

Validation Rules:
* Amount must be > 0; decimals accepted, converted to cents server-side
* PIN required if `requirePin=true` on the modal
* Note optional (500 chars max)

## Manual Testing Guide (Quick)

Below are condensed steps; see `docs/manual-testing.md` for comprehensive scenarios.

### User PIN Access + Top-Up Request
1. Start stack: `make dev` → open http://localhost:3000
2. Create a user (if none exist) with a PIN via Users page (as an existing admin/treasurer)
3. Go to Dashboard → select the user → enter their PIN
4. Press "Top Up Balance" → enter amount (e.g. 12.50), note, re-enter PIN → submit
5. Verify success toast & pending entry (Pending Confirmations section)

### Treasurer Confirmation
1. Log (select) a treasurer user with their PIN
2. Navigate to Treasurer page (or Dashboard pending list) to view pending money moves
3. Confirm the deposit with a different treasurer’s PIN (enforces two-person rule)
4. Balance should update after confirmation (backend invalidates queries; refresh if needed)

### Error Checks
* Wrong PIN → error toast + inline validation message
* Zero / negative amount → validation error prevents submit
* Reusing same treasurer as creator for confirmation → backend should reject

### Internationalization Toggle
1. Switch language (e.g. from DE to EN) using UI control (if present)
2. Ensure newly added keys (top-up modal labels, confirmation notice) are translated

## Added i18n Keys (Recent)

The following keys were recently added to support the self-service top-up integration test and improved UX:
```
common.optional
common.characters
common.equivalent
common.creating
moneyMove.amount
moneyMove.note
moneyMove.noteExample
moneyMove.confirmationRequired
moneyMove.invalidAmount
```
German equivalents reside in `frontend/src/i18n/de.json`.

## Testing Notes (Frontend)

* Use data-testid attributes for stable selectors in `TopUpBalanceModal`:
  - `topup-amount`, `topup-pin`, `topup-note`, `topup-submit`
* Integration test: `dashboard-topup.test.tsx` performs full flow (PIN verification + modal submit) without component mocking
* Prefer factories (`makeUser`) rather than inline object literals
* If translation text becomes brittle, fall back to test ids

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

- Frontend unit tests directly inside running dev containers:
   ```bash
   docker compose -f infra/docker-compose.dev.yml exec frontend npm test --silent -- --run
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