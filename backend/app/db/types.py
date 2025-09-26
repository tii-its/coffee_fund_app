"""
Custom database types for cross-database compatibility.
"""
import uuid
from sqlalchemy import TypeDecorator, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB


class UUID(TypeDecorator):
    """
    Platform-independent GUID type.
    
    Uses PostgreSQL UUID when available, otherwise uses a String(36).
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


class JSON(TypeDecorator):
    """
    Platform-independent JSON type.
    
    Uses PostgreSQL JSONB when available, otherwise uses standard JSON.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            # For SQLite and other databases, use the built-in JSON type
            from sqlalchemy import JSON as SQLAlchemyJSON
            return dialect.type_descriptor(SQLAlchemyJSON())