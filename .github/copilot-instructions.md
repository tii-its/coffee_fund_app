# copilot-instructions.md — Coffee Fund Web App (MVP)

This file gives **targeted, actionable guidance** to a GitHub Copilot agent working on this repository. Keep suggestions **short, specific, and project-aware**.

---

## Big Picture
- Build a small **Coffee Fund Web App** to track product consumption and cash movements for a team.
- Roles: **User**, **Treasurer (Verwalter)**. Every user (including treasurers) has a **mandatory per-user PIN** stored hashed. There is **no global Admin/Treasurer PIN** anymore.
- All **money movements** (deposits, payouts) use a **two-person confirmation rule** (created by Treasurer, confirmed by different Treasurer). (Future enhancement: optional user confirmation step – currently balance changes on treasurer confirmation.)
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
  - (Removed: ADMIN_PIN / TREASURER_PIN – per-user PINs only)
- **Dev up:** `make dev` (uses docker-compose.dev.yml)
- **Test:** `make test` (backend + frontend), `make test-backend`, `make test-frontend`
- **Migrations:** `make migrate` (upgrade), `make migrate-generate msg="description"`
- **Linting:** `make lint` (check), `make lint-fix` (auto-fix)
- **Logs/Shell:** `make logs-backend`, `make shell-backend`, `make shell-db`
 - **Frontend tests (direct in running dev containers):**
   ```bash
   docker compose -f infra/docker-compose.dev.yml exec frontend npm test --silent -- --run
   ```

---

## Data Model (Authoritative)
> Implement with SQLAlchemy. Use snake_case in DB. All IDs are UUIDs.

### users
- id (uuid, pk)
- display_name (str)
- email (str, unique, required in current implementation)
- qr_code (str?, optional)
- role (enum: user/treasurer)
- is_active (bool)
- created_at (ts)
- pin_hash (str, required) — SHA-256 hash of user's PIN

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
- confirmed_at (ts)
- confirmed_by (fk users): must be different from created_by, must be a treasurer
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

## Roles
- **User**: Can access dashboard, kiosk
- **Treasurer**: All User rights + access products and treasurer page; initiates & confirms money moves (with two-person rule)
- **Admin**: A special, unique and preconfigured user required for user CRUD, rotating the Admin PIN itself. Cannot be removed.

## UI / UX Notes
- **Kiosk mode**: Fast booking in 2–3 clicks. User → Product → Confirm.
- **Multi-user concurrency**: Ensure backend handles multiple parallel sessions without race conditions (use transactions).  
- **Internationalization**: Use i18next in frontend, store strings in `/src/i18n/de.json` and `/src/i18n/en.json`. Default language: German. User can switch in UI.  
- **Treasurer dashboard**: Requires Treasurer role. List of all balances, pending confirmations, product mgmt, CSV export, money movement approvals
- **Dashboard**: Overview of coffee fund balance, Allows selection of user which leads to user dashboard; top 3 coffee consumers, List of users below threshold, 
- **User dashboard**: Part of dashboard, Current balance, consumption history, topping up deposits/payouts, change user PIN
**Users page**: Accessible to Treasurers (future: may require re-auth with treasurer's own PIN). List all users, create new users (must supply a PIN), edit existing users (can rotate their PIN), deactivate users.
- **Products**: Requrires Treasurer role. List, create, edit, deactivate products.

---

## Common Patterns & Debugging Tips

### Database Issues
- **Enum Conflicts**: If SQLAlchemy enum errors occur, ensure `values_callable=lambda x: [e.value for e in x]` in model definitions
- **Migration Failures**: Use raw SQL for enum creation in Alembic: `op.execute("CREATE TYPE IF NOT EXISTS...")`
- **Test Database**: Tests use SQLite with custom TypeDecorators for UUID/JSON compatibility

### Service Layer
- **Balance Logic**: `confirmed_deposits - confirmed_payouts - all_consumptions`
- **Audit Trail**: Every mutation logged with actor_id + metadata.
- **Two-Person Rule**: Money moves require different treasurer for creation vs confirmation.
- **User Creation**: Requires per-user PIN (mandatory). Email required (current impl) for uniqueness.
- **PIN Management**: Only per-user. No global rotation target; removal of legacy admin/tresurer reset flow.

### Frontend Components
- **UserCreateModal**: Supply display name, email, role, PIN.
- **UserEditModal**: Can change display name, email, role, active flag, and optionally set a new PIN.
- (Removed) Global Admin PIN gating — remove any stale UI expecting it.

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
- Run tests with Makefile/container:  
  ```bash
  make test-backend
  make test-frontend
  ```
---

## Acceptance Criteria
1. Multiple users can log consumptions simultaneously without data conflicts.
2. UI language toggle (DE/EN) works across sessions.
3. Coffee booking flow: Select user -> select product -> confirm (≤3 clicks).
4. Treasurer dashboard lists balances, pending money moves, product management, CSV export.
5. Money moves enforce two-person rule (creator ≠ confirmer); pending until confirmed.
6. All mutations recorded in `audit` with actor + metadata.
7. Every user has a PIN; user creation fails without PIN; PIN changes hashed.
8. No reliance on any global/shared PIN.

## Migration Notes (Legacy Cleanup)
- Removed endpoints: `/users/verify-pin`, `/users/change-pin` (global variants) replaced by `/users/verify-user-pin`, `/users/change-user-pin`.
- Removed config/env: `ADMIN_PIN`, `TREASURER_PIN` — delete from `.env.example` and code once references are gone.
- Remove Makefile targets: `admin-pin-reset` (or equivalent) – obsolete.
- Ensure frontend no longer prompts for a global PIN; per-user PIN entry occurs only in contexts that logically require it (e.g., PIN change, maybe future sensitive action confirmation).

## Pending Enhancements (Post-Refactor)
- Add per-action PIN re-verification for sensitive treasurer operations.
- Add rate limiting / lockout after repeated wrong PIN attempts.
- Introduce optional email notifications for large deposits/payouts.
- Replace `datetime.utcnow()` with timezone-aware `datetime.now(datetime.UTC)`.
---
