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
    # New admin PIN replacing deprecated treasurer PIN; fallback logic below.
    admin_pin: str = "1234"
    # Deprecated: treasurer_pin retained only for transitional env var mapping (do not use directly)
    treasurer_pin: str | None = None

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> str:
        if isinstance(v, list):
            return ','.join(v)
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(',')]

    def model_post_init(self, __context):  # type: ignore[override]
        """Post-init hook to maintain backward compatibility with legacy TREASURER_PIN env var.

        If ADMIN_PIN not explicitly provided but TREASURER_PIN is set, promote it to admin_pin
        and emit a concise warning so operators know to migrate their environment configs.
        """
        legacy_env = os.getenv("TREASURER_PIN")
        explicit_admin = os.getenv("ADMIN_PIN")
        if explicit_admin:
            # Nothing to do; admin pin explicitly set.
            return
        if legacy_env and (not self.admin_pin or self.admin_pin == "1234"):
            # Adopt legacy value
            self.admin_pin = legacy_env
            # Provide a one-time runtime notice (stdout) – acceptable for early MVP.
            print("[config] WARNING: TREASURER_PIN is deprecated. Use ADMIN_PIN instead. Using legacy value for admin_pin.")
        # For any lingering code referencing settings.treasurer_pin, keep it aligned.
        if self.treasurer_pin is None:
            self.treasurer_pin = self.admin_pin
    
    # Database settings
    echo_sql: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()