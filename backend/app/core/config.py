from typing import Optional, List
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee"
    secret_key: str = "change-me-in-production"
    threshold_cents: int = 1000
    csv_export_limit: int = 50000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database settings
    echo_sql: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()