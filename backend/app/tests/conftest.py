"""
Test configuration and fixtures.
Provides shared database setup and utilities for all test files.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import sqlite3
import uuid

from app.main import app
from app.db.session import get_db, Base
# Import all models to ensure they're registered with Base.metadata
from app.models import User, Product, Consumption, MoneyMove, Audit
from app.core.enums import UserRole, MoneyMoveType, MoneyMoveStatus, AuditAction


# Custom TypeDecorator for UUID compatibility with SQLite
class UUID(TypeDecorator):
    """Platform-independent UUID type. Uses PostgreSQL's UUID type, otherwise uses CHAR(36)."""
    
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# Custom JSON TypeDecorator for SQLite
class JSON(TypeDecorator):
    """JSON type for SQLite compatibility."""
    
    impl = CHAR
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            import json
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            import json
            return json.loads(value)
        return value


# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        # Safety net: make sure all tables exist (idempotent). In some edge cases
        # (import order or earlier fixture failures) the in-memory schema may not
        # yet have been created when a direct service call uses this override.
        # create_all is cheap with SQLite and ensures stability for direct
        # BalanceService calls inside integration tests.
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    return engine


@pytest.fixture(scope="session")
def test_db():
    """Create test database tables."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Clear all tables to ensure isolation from prior API client tests
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(test_db):
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    # Clear all tables before each client-based test to ensure isolation between
    # API tests that don't use the db_session fixture. This avoids state bleed
    # causing count/order assertions to fail.
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up override
    app.dependency_overrides = {}


# Database model fixtures (return database objects)


@pytest.fixture
def db_test_user(db_session):
    """Create a test user in database."""
    user = User(
        display_name="Test User",
        email="test.user@example.com",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture  
def db_test_treasurer(db_session):
    """Create a test treasurer in database."""
    treasurer = User(
        display_name="Test Treasurer",
        email="test.treasurer@example.com",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer)
    db_session.commit()
    db_session.refresh(treasurer)
    return treasurer


@pytest.fixture
def db_test_treasurer2(db_session):
    """Create a second test treasurer in database."""
    treasurer = User(
        display_name="Test Treasurer 2", 
        email="test.treasurer2@example.com",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer)
    db_session.commit()
    db_session.refresh(treasurer)
    return treasurer


@pytest.fixture
def db_test_product(db_session):
    """Create a test product in database."""
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# API fixtures (return API response dictionaries with 'id' fields)
@pytest.fixture
def test_user(client):
    """Create a test user via API and return response."""
    import time
    user_data = {
        "display_name": "API Test User",
        "email": f"api.test.user.{int(time.time()*1000)}@example.com",
        "role": "user",
        "is_active": True,
        "pin": "testpin123"  # PIN is now required for all users
    }
    response = client.post("/users/", json=user_data)
    if response.status_code != 201:
        # If user exists, try with a timestamp to make it unique
        import time
        user_data["display_name"] = f"API Test User {int(time.time() * 1000)}"
        response = client.post("/users/", json=user_data)
    
    if response.status_code != 201:
        print(f"Failed to create user. Status: {response.status_code}, Response: {response.text}")
        raise AssertionError(f"Expected 201, got {response.status_code}: {response.text}")
    
    response_data = response.json()
    if 'id' not in response_data:
        raise AssertionError(f"Response missing 'id' field: {response_data}")
    
    return response_data


@pytest.fixture
def test_treasurer(client):
    """Create a test treasurer via API and return response."""
    import time
    treasurer_data = {
        "display_name": "API Test Treasurer",
        "email": f"api.test.treasurer.{int(time.time()*1000)}@example.com",
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=treasurer_data)
    if response.status_code != 201:
        # If user exists, try with a timestamp to make it unique
        import time
        treasurer_data["display_name"] = f"API Test Treasurer {int(time.time() * 1000)}"
        response = client.post("/users/", json=treasurer_data)
    
    if response.status_code != 201:
        print(f"Failed to create treasurer. Status: {response.status_code}, Response: {response.text}")
        raise AssertionError(f"Expected 201, got {response.status_code}: {response.text}")
    
    response_data = response.json()
    if 'id' not in response_data:
        raise AssertionError(f"Response missing 'id' field: {response_data}")
    
    return response_data


@pytest.fixture
def test_product(client):
    """Create a test product via API and return response."""
    import time
    product_data = {
        "name": f"API Test Coffee {int(time.time()*1000)}",
        "price_cents": 150,
        "is_active": True
    }
    response = client.post("/products/", json=product_data)
    if response.status_code != 201:
        # If product exists, try with a timestamp to make it unique
        import time
        product_data["name"] = f"API Test Coffee {int(time.time() * 1000)}"
        response = client.post("/products/", json=product_data)
    
    if response.status_code != 201:
        print(f"Failed to create product. Status: {response.status_code}, Response: {response.text}")
        raise AssertionError(f"Expected 201, got {response.status_code}: {response.text}")
    
    response_data = response.json()
    if 'id' not in response_data:
        raise AssertionError(f"Response missing 'id' field: {response_data}")
    
    return response_data


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    import time
    ts = int(time.time()*1000)
    return {
        "display_name": "Test User",
        "email": f"test.user.{ts}@example.com",
        "role": "user", 
        "is_active": True,
        "pin": "testpin123"  # PIN is now required for all users
    }


@pytest.fixture
def sample_treasurer_data():
    """Sample treasurer data for testing."""
    import time
    ts = int(time.time()*1000)
    from app.core.config import settings
    return {
        "display_name": "Test Treasurer",
        "email": f"test.treasurer.{ts}@example.com",
        "role": "treasurer",
        "is_active": True,
        "pin": settings.treasurer_pin  # Use treasurer PIN for authorization
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Coffee",
        "price_cents": 150,
        "is_active": True
    }


@pytest.fixture
def sample_consumption_data(test_user, test_product):
    """Sample consumption data for testing."""
    return {
        "user_id": test_user["id"],
        "product_id": test_product["id"],
        "qty": 2,
        "unit_price_cents": 150
    }


@pytest.fixture
def sample_money_move_data(test_user):
    """Sample money move data for testing."""
    return {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test deposit"
    }