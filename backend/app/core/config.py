from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee"
    secret_key: str = "change-me-in-production"
    threshold_cents: int = 1000
    csv_export_limit: int = 50000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> str:
        if isinstance(v, list):
            return ','.join(v)
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(',')]
    
    # Database settings
    echo_sql: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()