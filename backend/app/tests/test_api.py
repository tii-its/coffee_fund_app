import pytest
from uuid import uuid4


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


def test_get_users_above_threshold(client):
    """Test getting users with balance above threshold via API"""
    # Test the new above-threshold endpoint
    response = client.get("/users/balances/above-threshold?threshold_cents=1000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should be empty initially since no users have balances set up
    assert len(data) == 0


def test_get_users_below_threshold(client):
    """Test getting users with balance below threshold via API"""
    # Test the existing below-threshold endpoint
    response = client.get("/users/balances/below-threshold?threshold_cents=1000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)