from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import users, products, consumptions, money_moves, exports, audit, settings as settings_router

app = FastAPI(
    title="Coffee Fund API",
    description="A team coffee fund management API with consumption tracking and cash movement management",
    version="1.0.0"
)

# Run Alembic migrations at startup (Postgres only) to ensure new columns (e.g., users.email) exist
@app.on_event("startup")
def run_migrations() -> None:
    try:
        from app.db.session import engine
        if engine.url.get_backend_name().startswith("postgres"):
            from alembic import command
            from alembic.config import Config
            import pathlib
            # main.py is at backend/app/main.py -> alembic.ini is at backend/alembic.ini (one parent)
            alembic_ini = pathlib.Path(__file__).resolve().parent.parent / "alembic.ini"
            if alembic_ini.exists():
                cfg = Config(str(alembic_ini))
                cfg.set_main_option("sqlalchemy.url", str(engine.url))
                command.upgrade(cfg, "head")
            else:
                print(f"[startup] alembic.ini not found at {alembic_ini}")
    except Exception as e:
        print(f"[startup] Migration step skipped or failed: {e}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(consumptions.router)
app.include_router(money_moves.router)
app.include_router(exports.router)
app.include_router(audit.router)
app.include_router(settings_router.router)

@app.get("/")
def read_root():
    return {
        "message": "Coffee Fund API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }