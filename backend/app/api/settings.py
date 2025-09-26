from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings():
    """Get application settings"""
    return {
        "threshold_cents": settings.threshold_cents,
        "csv_export_limit": settings.csv_export_limit,
    }


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Coffee Fund API is running"}