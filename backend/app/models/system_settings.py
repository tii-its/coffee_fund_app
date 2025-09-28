from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean

from app.db.session import Base
from app.db.types import UUID  # cross-database UUID type


class SystemSettings(Base):
    """System-wide settings table"""
    __tablename__ = "system_settings"
    
    # Use custom UUID TypeDecorator for cross-db (PostgreSQL/SQLite) compatibility
    id = Column(UUID(), primary_key=True, default=uuid4)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_encrypted = Column(Boolean, default=False, nullable=False)