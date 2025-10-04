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
from app.core.config import settings


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
    """Create a test user in database (no email field)."""
    user = User(
        display_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture  
def db_test_treasurer(db_session):
    """Create a test treasurer in database (no email field)."""
    treasurer = User(
        display_name="Test Treasurer",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer)
    db_session.commit()
    db_session.refresh(treasurer)
    return treasurer


@pytest.fixture
def db_test_treasurer2(db_session):
    """Create a second test treasurer in database (no email field)."""
    treasurer = User(
        display_name="Test Treasurer 2", 
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
def admin_bootstrap(client):
    """Create (or get) the bootstrap admin user and return (admin, pin)."""
    admin_pin = "AdminPIN123"
    payload = {
        "actor_id": str(uuid.uuid4()),  # ignored during bootstrap
        "actor_pin": "bootstrap-ignore",
        "user": {
            "display_name": "Bootstrap Admin",
            "role": "admin",
            "is_active": True,
            "pin": admin_pin
        }
    }
    # Try creation; if already exists, fetch list with headers (will fail without headers if we didn't create yet)
    resp = client.post("/users/", json=payload)
    if resp.status_code not in (201, 400):  # 400 could arise if second admin attempt blocked
        raise AssertionError(f"Unexpected admin bootstrap status {resp.status_code}: {resp.text}")
    # Retrieve admin via listing (needs headers). Provide headers using known admin creds.
    # First we need admin id: if creation succeeded, in resp.json(); else attempt list with guessed id not possible
    admin_id = None
    if resp.status_code == 201:
        admin_id = resp.json()["id"]
    else:
        # Attempt to list users by iterating possible; fallback: cannot easily get id without headers so assume creation succeeded earlier in session
        # For simplicity in test context, enforce creation success path
        raise AssertionError("Admin already existed unexpectedly during bootstrap in isolated test context")
    return {"id": admin_id, "pin": admin_pin}


@pytest.fixture
def admin_headers(admin_bootstrap):
    return {"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]}


@pytest.fixture
def test_user(client, admin_bootstrap):
    """Create a test user via API using admin wrapper."""
    import time
    user_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"API Test User {int(time.time()*1000)}",
            "role": "user",
            "is_active": True,
            "pin": "testpin123"
        }
    }
    response = client.post("/users/", json=user_payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def treasurer_context(client, admin_bootstrap):
    """Create a treasurer via admin wrapper and return (treasurer, headers)."""
    import time
    treasurer_pin = "treasurerPIN123"
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"API Test Treasurer {int(time.time()*1000)}",
            "role": "treasurer",
            "is_active": True,
            "pin": treasurer_pin
        }
    }
    resp = client.post("/users/", json=payload)
    assert resp.status_code == 201, resp.text
    treasurer = resp.json()
    headers = {"x-actor-id": treasurer["id"], "x-actor-pin": treasurer_pin}
    return {"treasurer": treasurer, "headers": headers}


@pytest.fixture
def test_product(client, treasurer_context):
    """Create a test product via API (treasurer headers) and return response."""
    import time
    product_data = {
        "name": f"API Test Coffee {int(time.time()*1000)}",
        "price_cents": 150,
        "is_active": True
    }
    response = client.post("/products/", json=product_data, headers=treasurer_context["headers"])
    assert response.status_code == 201, response.text
    return response.json()


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data (user sub-payload)."""
    import time
    ts = int(time.time()*1000)
    return {
        "display_name": f"Test User {ts}",
        "role": "user", 
        "is_active": True,
        "pin": "testpin123"
    }


@pytest.fixture
def sample_treasurer_data():
    """Sample treasurer data (user sub-payload)."""
    import time
    ts = int(time.time()*1000)
    return {
        "display_name": f"Test Treasurer {ts}",
        "role": "treasurer",
        "is_active": True,
        "pin": "treasurerPIN123"
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