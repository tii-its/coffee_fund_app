from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee"
    secret_key: str = "change-me-in-production"
    threshold_cents: int = 1000
    csv_export_limit: int = 50000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Database settings
    echo_sql: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()