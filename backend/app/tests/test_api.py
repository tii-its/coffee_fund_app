import pytest


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


def test_create_user(client, sample_user_data, admin_bootstrap):
    """Test user creation via admin wrapper."""
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": sample_user_data
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["display_name"] == sample_user_data["display_name"]
    assert data["role"] == sample_user_data["role"]
    assert "id" in data


def test_get_users(client, sample_user_data, admin_bootstrap):
    """Test getting users (admin only)."""
    create_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": sample_user_data
    }
    client.post("/users/", json=create_payload)
    response = client.get("/users/", headers={"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list) and len(data) > 0


def test_create_product(client, sample_product_data, treasurer_context):
    """Test product creation (treasurer headers required)."""
    response = client.post("/products/", json=sample_product_data, headers=treasurer_context["headers"])
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == sample_product_data["name"]
    assert data["price_cents"] == sample_product_data["price_cents"]
    assert "id" in data


def test_get_products(client, sample_product_data, treasurer_context):
    """Test getting products"""
    client.post("/products/", json=sample_product_data, headers=treasurer_context["headers"])    
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) > 0


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