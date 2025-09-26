import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
import os
from uuid import uuid4

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user_data():
    return {
        "display_name": "Test User",
        "role": "user",
        "is_active": True
    }


@pytest.fixture
def sample_product_data():
    return {
        "name": "Coffee",
        "price_cents": 150,
        "is_active": True
    }


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/settings/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_settings(client):
    """Test settings endpoint"""
    response = client.get("/settings/")
    assert response.status_code == 200
    data = response.json()
    assert "threshold_cents" in data
    assert "csv_export_limit" in data


def test_create_user(client, sample_user_data):
    """Test user creation"""
    response = client.post("/users/", json=sample_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == sample_user_data["display_name"]
    assert data["role"] == sample_user_data["role"]
    assert "id" in data


def test_get_users(client, sample_user_data):
    """Test getting users"""
    # Create a user first
    client.post("/users/", json=sample_user_data)
    
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_product(client, sample_product_data):
    """Test product creation"""
    response = client.post("/products/", json=sample_product_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_product_data["name"]
    assert data["price_cents"] == sample_product_data["price_cents"]
    assert "id" in data


def test_get_products(client, sample_product_data):
    """Test getting products"""
    # Create a product first
    client.post("/products/", json=sample_product_data)
    
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0