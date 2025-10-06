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
- **User-Initiated Money Moves**: `POST /money-moves/user-request` allows users to create money moves for themselves only (requires user PIN, still needs treasurer confirmation)
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
- **User**: Can access dashboard, kiosk; can initiate money moves for their own account (requires treasurer confirmation)
- **Treasurer**: All User rights + access products and treasurer page; initiates & confirms money moves (with two-person rule)
- **Admin**: A special, unique and preconfigured user required for user CRUD, rotating the Admin PIN itself. Cannot be removed.

## UI / UX Notes
- **Kiosk mode**: Fast booking in 2–3 clicks. User → Product → Confirm.
- **Multi-user concurrency**: Ensure backend handles multiple parallel sessions without race conditions (use transactions).  
- **Internationalization**: Use i18next in frontend, store strings in `/src/i18n/de.json` and `/src/i18n/en.json`. Default language: German. User can switch in UI.  
- **Treasurer dashboard**: Requires Treasurer role. List of all balances, pending confirmations, product mgmt, CSV export, money movement approvals
- **Dashboard**: Overview of coffee fund balance, Allows selection of user which leads to user dashboard; top 3 coffee consumers, List of users below threshold, 
- **User dashboard**: Part of dashboard, Current balance, consumption history, topping up deposits/payouts, change user PIN, recover user PIN (self-service)
**Users page**: Accessible to Treasurers (future: may require re-auth with treasurer's own PIN). List all users, create new users (must supply a PIN), edit existing users (can rotate their PIN or reset to default), deactivate users. Users can initiate money moves for themselves via "Top Up Balance" button (visible only on their own user row).
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
- **PIN Recovery**: Users can recover their own PIN via Dashboard (requires current PIN verification). Admins can reset any user's PIN to default "1234" via Users page (requires admin PIN confirmation).

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

### Frontend Testing Conventions (Recent Additions)
These conventions reflect the current test suite (27 passing) and should be followed for new tests:

- **Global Test Setup**: `frontend/src/test-setup.ts` registers `@testing-library/jest-dom` matchers and stubs `window.alert` with a `vi.fn()` spy to suppress jsdom warnings. Always rely on that stub (do not re-mock per test unless necessary).
- **User Factory**: Use `makeUser` from `frontend/src/tests/factories.ts` to generate user objects instead of hard‑coding inline literals. Keeps tests concise and consistent.
- **Stable Selectors**: Destructive / multi-step confirmation buttons have data test ids:
  - `confirm-delete-btn` (initial delete confirmation)
  - `force-deactivate-btn` (second step after 409 related records response)
  Prefer `getByTestId` (or `findAllByTestId` when duplicates are expected) over brittle text queries for these actions.
- **Duplicate Elements**: Some components render buttons twice (e.g., once in list context, once in modal). Use plural queries like `findAllByText` / `findAllByTestId` and target the intended element explicitly if order matters.
- **Delete API Signature**: When mocking, the users delete mutation is invoked as: `usersApi.delete(userId, { actorId, pin }, forceBoolean)` where `forceBoolean` defaults to `false`. Tests expecting forced deletion must assert the second call with `true` after a simulated 409.
- **409 Two-Step Deletion Flow**: A new test (`user-deletion-related-records.test.tsx`) covers the scenario: first mutation returns 409 with a flag (backend shape), UI reveals related records + force button, second click calls API with `force=true` and succeeds. New tests for similar flows should emulate this pattern rather than inventing custom logic.
- **Minimal Modal Copy (Intentional)**: User-specific names are NOT interpolated in the confirmation modal (design decision – Option A). Do not reintroduce name-personalized assertions; keep tests generic.
- **BalanceCard Test Data**: Provide a nested `user` object if mocking balance responses (`balance.user.display_name`) to avoid undefined errors.
- **i18n Keys**: If text assertions become flaky due to translation changes, prefer test ids. Keep translation fixtures minimal—avoid hard coupling tests to full phrase wording unless verifying i18n itself.
- **PIN Gating Tests**: For dashboard PIN verification, ensure mocks align with the API contract and allow for multiple occurrences of PIN-related elements (use `findAllByTestId` or lenient assertions when components duplicate structure).
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
