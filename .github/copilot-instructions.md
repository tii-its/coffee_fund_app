# copilot-instructions.md — Coffee Fund Web App (MVP)

This file gives **targeted, actionable guidance** to a GitHub Copilot agent working on this repository. Keep suggestions **short, specific, and project-aware**.

---

## Big Picture
- Build a small **Coffee Fund Web App** to track product consumption and cash movements for a team.
- Roles: **User**, **Treasurer** (Verwalter).
- All **money movements** (deposits, payouts) use a **two-person confirmation rule** (created by Treasurer, confirmed by User). No SSO in MVP.
- App must be **usable simultaneously by multiple users** (concurrent sessions on kiosk, desktop, mobile).
- App must support **German and English** (i18n-ready UI, switchable).

---

## Tech Stack & Versions
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- **DB:** PostgreSQL 15 (SQLite in-memory for testing)
- **Frontend:** React 18 + Vite, TypeScript 5, i18next (for translations)
- **Testing:** Pytest + httpx (backend), Vitest + Playwright (frontend/E2E)
- **Packaging/Dev:** Docker Compose (dev/prod), Makefile, Ruff (lint), Black (format)

---

## Critical Implementation Patterns

### Database & Migrations
- **PostgreSQL Enums**: Use raw SQL in Alembic migrations for reliable enum creation:
  ```sql
  op.execute("CREATE TYPE IF NOT EXISTS userrole AS ENUM ('user', 'treasurer')")
  ```
- **SQLAlchemy Enum Fix**: Add `values_callable=lambda x: [e.value for e in x]` to prevent serialization issues:
  ```python
  Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]))
  ```
- **Cross-Database Testing**: Use custom TypeDecorators in `conftest.py` for SQLite compatibility:
  ```python
  # Handles UUID/JSON differences between PostgreSQL and SQLite
  ```

### Service Layer Architecture
- **Balance Calculation**: Centralized in `BalanceService` with SQL aggregation:
  ```python
  # money_moves (confirmed) - consumptions = current balance
  ```
- **Audit Logging**: Every action logged via `AuditService` with structured metadata
- **QR Code Generation**: Self-contained service for kiosk integration
- **CSV Export**: Proper FastAPI Response headers for file downloads

### API Patterns
- **UUID Primary Keys**: All entities use UUID for distributed-friendly IDs
- **Creator/Actor Tracking**: All mutations track who performed the action
- **Two-Person Confirmation**: Money moves require separate creator and confirmer
- **Pydantic v2**: Use `.model_dump()` instead of deprecated `.dict()`

### Testing Infrastructure
- **Centralized Fixtures**: Use `conftest.py` for shared database setup
- **Cross-Database Compatibility**: SQLite for speed, PostgreSQL patterns for production
- **Integration Tests**: Complete workflows in `test_integration_workflows.py`
- **Isolated Tests**: Each test gets fresh database state

---

## Repository Layout
```
/backend
  /app
    /core          # config, deps, security, utils
    /models        # SQLAlchemy models
    /schemas       # Pydantic schemas
    /api           # routers: consumptions, money_moves, products, users, exports, settings
    /services      # domain logic (balance, audit, csv export, qr-code)
    /db            # session, migrations (alembic)
    /tests         # pytest
    main.py        # FastAPI app factory
/frontend
  /src
    /pages         # Dashboard, Kiosk, Treasurer, Auth(optional)
    /components    # ProductGrid, UserPicker, PendingList, BalanceCard, DataTable
    /api           # typed client (OpenAPI-generated or hand-rolled)
    /store         # state (Zustand/Redux)
    /i18n          # translation files (de.json, en.json)
    /tests
  index.html, vite.config.ts
/infra
  docker-compose.dev.yml
  docker-compose.prod.yml
  nginx.conf (optional)
copilot.md
README.md
.env.example
Makefile
```

---

## Environment & Commands
- `.env.example` keys:
  - `DATABASE_URL=postgresql+psycopg://coffee:coffee@db:5432/coffee`
  - `SECRET_KEY=change-me`
  - `THRESHOLD_CENTS=1000`  # default 10€
  - `CSV_EXPORT_LIMIT=50000`
  - `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`
- **Dev up:** `make dev` (uses docker-compose.dev.yml)
- **Test:** `make test` (backend + frontend), `make test-backend`, `make test-frontend`
- **Migrations:** `make migrate` (upgrade), `make migrate-generate msg="description"`
- **Linting:** `make lint` (check), `make lint-fix` (auto-fix)
- **Logs/Shell:** `make logs-backend`, `make shell-backend`, `make shell-db`

---

## Data Model (Authoritative)
> Implement with SQLAlchemy. Use snake_case in DB. All IDs are UUIDs.

### users
- id (uuid, pk)
- display_name (str)
- qr_code (str?, optional)
- role (enum: user/treasurer)
- is_active (bool)
- created_at (ts)

### products
- id (uuid, pk)
- name (str)
- price_cents (int)
- is_active (bool)
- created_at (ts)

### consumptions
- id (uuid, pk)
- user_id (fk users)
- product_id (fk products)
- qty (int)
- unit_price_cents (int)
- amount_cents (int)
- at (ts)
- created_by (fk users)

### money_moves
- id (uuid, pk)
- type (enum: deposit/payout)
- user_id (fk users)
- amount_cents (int)
- note (str?)
- created_at (ts)
- created_by (fk users)
- confirmed_at (ts?)
- confirmed_by (fk users?)
- status (enum: pending/confirmed/rejected)

### audit
- id (uuid, pk)
- actor_id (fk users)
- action (str)
- entity (str)
- entity_id (uuid)
- meta_json (json)
- at (ts)

---

## UI / UX Notes
- **Kiosk mode**: Fast booking in 2–3 clicks. User → Product → Confirm.
- **Multi-user concurrency**: Ensure backend handles multiple parallel sessions without race conditions (use transactions).  
- **Internationalization**: Use i18next in frontend, store strings in `/src/i18n/de.json` and `/src/i18n/en.json`. Default language: German. User can switch in UI.  
- **Treasurer dashboard**: List of all balances, pending confirmations, product mgmt, CSV export.  
- **User dashboard**: Current balance, consumption history, pending confirmations.  

---

## Common Patterns & Debugging Tips

### Database Issues
- **Enum Conflicts**: If SQLAlchemy enum errors occur, ensure `values_callable=lambda x: [e.value for e in x]` in model definitions
- **Migration Failures**: Use raw SQL for enum creation in Alembic: `op.execute("CREATE TYPE IF NOT EXISTS...")`
- **Test Database**: Tests use SQLite with custom TypeDecorators for UUID/JSON compatibility

### Service Layer
- **Balance Logic**: BalanceService calculates: `confirmed_deposits - confirmed_payouts - all_consumptions`
- **Audit Trail**: Every mutation logged via AuditService with actor_id and structured metadata
- **Two-Person Rule**: Money moves need creator ≠ confirmer, enforced in API layer

### API Development
- **Response Objects**: Use FastAPI Response for file downloads with proper headers:
  ```python
  return Response(content=csv_data, media_type="text/csv", 
                 headers={"Content-Disposition": "attachment; filename=export.csv"})
  ```
- **Pydantic v2**: Always use `.model_dump()` instead of deprecated `.dict()`
- **UUID Handling**: All entity IDs are UUIDs, ensure proper serialization in schemas

### Testing Patterns
- **Centralized Setup**: Use fixtures from `conftest.py` for consistent database state
- **Integration Tests**: Test complete workflows in `test_integration_workflows.py`
- **Database Isolation**: Each test gets fresh database state via pytest fixtures

---

## Acceptance Criteria
1. Multiple users can log consumptions simultaneously without data conflicts.  
2. App UI can switch between German and English.  
3. User can book a coffee in ≤3 clicks.  
4. Treasurer can view balances, pending confirmations, export CSV.  
5. Deposits/payouts require confirmation by user before balance changes.  
6. All actions are logged in `audit` table.  

---
