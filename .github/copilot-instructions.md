# Coffee Fund – Agent Quick Guide

Concise, project-specific rules so an AI agent can contribute productively without re-discovering architecture.

## 1. Purpose & Domain
Track consumptions and cash movements. Enforce per-user PIN security + two‑person confirmation for money moves. No global/shared PINs. German is default UI; English available.

## 2. Core Architecture
Backend (FastAPI + SQLAlchemy 2.x) with thin routers (`backend/app/api/*`) delegating to service layer (`backend/app/services/*`). Data integrity & balance math live in services, not routers. All entities use UUID PKs. Audit every mutation.

Frontend (React + Vite + TS). No persistent auth store: each privileged action explicitly supplies `x-actor-id` + `x-actor-pin` (see `frontend/src/api/client.ts` `withActor`). Modal-based PIN capture (promise pattern) replaces any global session notion.

## 3. Security & Auth Conventions
Per-action PIN only: never cache or store PINs in state, localStorage, or cookies. When adding new privileged API calls, require an `ActorHeaders` param and pass through `withActor` exactly like existing product / money move calls. Two-person rule: confirmer must differ from creator (enforced server-side – maintain that invariant in new endpoints).

## 4. Data & Migrations
Enums in migrations: always raw SQL `CREATE TYPE IF NOT EXISTS`. In models wrap Enum with `values_callable=lambda e: [x.value for x in e]` to avoid serialization issues. Testing uses SQLite: rely on custom TypeDecorators in `conftest.py` for UUID/JSON parity—don’t introduce Postgres-only features without an adapter.

## 5. Key Files
`backend/app/services/balance.py` – authoritative balance computation.
`backend/app/services/audit.py` – call on every mutation; include actor & minimal structured meta.
`frontend/src/api/client.ts` – single axios instance; NEVER add a global request interceptor for auth headers.
`frontend/src/components/*Modal*` – modal patterns; replicate promise-based approach for new secure prompts.

## 6. API & Schemas
Use Pydantic v2 `.model_dump()`. Return explicit schema objects (avoid leaking raw ORM). New routes follow pattern: router → service → commit → audit → return schema. For file exports use FastAPI `Response` with `Content-Disposition` (see `exports.py`).

## 7. Testing Strategy
Backend: Pytest fast path with in-memory SQLite. Add integration workflow tests rather than duplicating unit logic. Frontend: Vitest unit tests—spy on exported `api` (no complex axios module mocks). Use container command for CI parity:
```bash
docker compose -f infra/docker-compose.dev.yml exec frontend npm test --silent -- --run
```

## 8. Common Pitfalls
Missing PIN headers → 401: ensure tests explicitly add them. Enum alterations require new migration (never edit old). Race conditions: wrap multi-write operations in a transaction inside a service. Don’t reintroduce cached actor context.

## 9. Adding Features (Checklist)
1. Define/extend model + Alembic migration (raw SQL for enums). 
2. Add Pydantic schemas (request/response) with UUID fields. 
3. Implement service method (business logic + audit). 
4. Add router endpoint (validate roles, inject actor). 
5. Frontend: extend `api/client.ts` (add function with explicit `ActorHeaders` if privileged). 
6. Add modal-triggered PIN capture where user initiates action. 
7. Tests: backend (workflow), frontend (header injection + negative 401). 

## 10. Style & Lint
Run `make lint` before committing. Use Ruff + Black (backend) and ESLint/TS strictness (frontend). Prefer small, composable service functions.

## 11. When Unsure
Search existing service or router doing something similar; mirror structure. If a change would require persistent PIN storage—stop, redesign to stay per-action.

Feedback welcome: refine or extend this guide when new patterns stabilize.
