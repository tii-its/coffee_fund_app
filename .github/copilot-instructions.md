# copilot.md — Coffee Fund Web App (MVP)

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
- **DB:** PostgreSQL 15
- **Frontend:** React 18 + Vite, TypeScript 5, i18next (for translations)
- **Testing:** Pytest + httpx (backend), Vitest + Playwright (frontend/E2E)
- **Packaging/Dev:** Docker Compose (dev/prod), Makefile, Ruff (lint), Black (format)

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
- **Dev up:** `docker compose -f infra/docker-compose.dev.yml up --build`
- **Migrations:** `alembic revision --autogenerate -m "init"; alembic upgrade head`
- **Backend dev:** `uvicorn app.main:app --reload`
- **Frontend dev:** `npm i && npm run dev`
- **Tests:** `make test`

---

## Data Model (Authoritative)
> Implement with SQLAlchemy. Use snake_case in DB.

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

## Acceptance Criteria
1. Multiple users can log consumptions simultaneously without data conflicts.  
2. App UI can switch between German and English.  
3. User can book a coffee in ≤3 clicks.  
4. Treasurer can view balances, pending confirmations, export CSV.  
5. Deposits/payouts require confirmation by user before balance changes.  
6. All actions are logged in `audit` table.  

---
