from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import users, products, consumptions, money_moves, exports, audit, settings as settings_router, stock_purchases

app = FastAPI(
    title="Coffee Fund API",
    description="A team coffee fund management API with consumption tracking and cash movement management",
    version="1.0.0"
)

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
app.include_router(stock_purchases.router)
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