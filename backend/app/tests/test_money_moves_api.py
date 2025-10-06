"""
Test money moves API endpoints
"""
import pytest
from app.core.enums import MoneyMoveType, MoneyMoveStatus
from uuid import uuid4


@pytest.fixture
def test_user(client, admin_bootstrap):
    """Create a test user via admin wrapper"""
    import time
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Test User {int(time.time()*1000)}",
            "role": "user",
            "is_active": True,
            "pin": "testpin123"
        }
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def test_treasurer(client, admin_bootstrap):
    import time
    treasurer_pin = "treasurerPIN123"
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Test Treasurer {int(time.time()*1000)}",
            "role": "treasurer",
            "is_active": True,
            "pin": treasurer_pin
        }
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    data["_headers"] = {"x-actor-id": data["id"], "x-actor-pin": treasurer_pin}
    return data


@pytest.fixture
def test_treasurer2(client, admin_bootstrap):
    import time
    treasurer_pin = "treasurerPIN456"
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Test Treasurer 2 {int(time.time()*1000)}",
            "role": "treasurer",
            "is_active": True,
            "pin": treasurer_pin
        }
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    data["_headers"] = {"x-actor-id": data["id"], "x-actor-pin": treasurer_pin}
    return data


@pytest.fixture
def sample_money_move_data(test_user):
    """Sample money move data"""
    return {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test deposit"
    }


def test_create_money_move_deposit(client, test_user, test_treasurer, sample_money_move_data):
    """Test creating a deposit money move"""
    response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["type"] == "deposit"
    assert data["user_id"] == sample_money_move_data["user_id"]
    assert data["amount_cents"] == 1000
    assert data["note"] == "Test deposit"
    assert data["status"] == "pending"
    assert data["created_by"] == test_treasurer["id"]
    assert data["confirmed_at"] is None
    assert data["confirmed_by"] is None


def test_create_money_move_payout(client, test_user, test_treasurer):
    """Test creating a payout money move"""
    money_move_data = {
        "type": "payout",
        "user_id": test_user["id"],
        "amount_cents": 500,
        "note": "Test payout"
    }
    response = client.post(
        "/money-moves/",
        json=money_move_data,
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["type"] == "payout"
    assert data["amount_cents"] == 500


def test_create_money_move_user_not_found(client, test_treasurer):
    """Test creating money move with invalid user"""
    money_move_data = {
        "type": "deposit",
        "user_id": str(uuid4()),
        "amount_cents": 1000,
        "note": "Test"
    }
    response = client.post(
        "/money-moves/",
        json=money_move_data,
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_money_move_invalid_headers(client, test_user):
    """Test creating money move with invalid treasurer headers"""
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test"
    }
    response = client.post(
        "/money-moves/",
        json=money_move_data,
        headers={"x-actor-id": str(uuid4()), "x-actor-pin": "wrong"},
    )
    assert response.status_code in (403, 404)


def test_create_money_move_non_treasurer_creator(client, test_user, admin_bootstrap):
    """Test creating money move with non-treasurer creator"""
    # Create another regular user
    import time
    user2_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Regular User 2 {int(time.time()*1000)}",
            "role": "user",
            "is_active": True,
            "pin": "testpin123"
        }
    }
    user2 = client.post("/users/", json=user2_payload).json()
    
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test"
    }
    response = client.post(
        "/money-moves/",
        json=money_move_data,
        headers={"x-actor-id": user2["id"], "x-actor-pin": "testpin123"},
    )
    assert response.status_code == 403
    assert "Only treasurers" in response.json()["detail"]


def test_get_money_moves(client, test_user, test_treasurer, sample_money_move_data):
    """Test getting all money moves"""
    # Create a money move first
    client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    
    response = client.get("/money-moves/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == sample_money_move_data["user_id"]


def test_get_money_moves_with_filters(client, test_user, test_treasurer, sample_money_move_data):
    """Test getting money moves with filters"""
    # Create a money move
    client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    
    # Filter by user_id
    response = client.get(f"/money-moves/?user_id={test_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    # Filter by status
    response = client.get("/money-moves/?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"
    
    # Filter by non-existent user
    response = client.get(f"/money-moves/?user_id={uuid4()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_get_pending_money_moves(client, test_user, test_treasurer, sample_money_move_data):
    """Test getting pending money moves"""
    # Create a pending money move using treasurer headers (remains pending until confirmed)
    client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    
    response = client.get("/money-moves/pending")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"


def test_get_money_move_by_id(client, test_user, test_treasurer, sample_money_move_data):
    """Test getting specific money move"""
    # Create a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    response = client.get(f"/money-moves/{money_move_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == money_move_id
    assert data["user_id"] == sample_money_move_data["user_id"]


def test_get_money_move_by_id_not_found(client):
    """Test getting non-existent money move"""
    response = client.get(f"/money-moves/{uuid4()}")
    assert response.status_code == 404
    assert "Money move not found" in response.json()["detail"]


def test_confirm_money_move(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test confirming a money move"""
    # Create a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    assert create_response.status_code == 201, f"Create failed: {create_response.status_code} {create_response.text}"
    money_move_json = create_response.json()
    assert "id" in money_move_json, f"Missing id in response: {money_move_json}"
    money_move_id = money_move_json["id"]
    
    # Confirm with different treasurer
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=test_treasurer2["_headers"],
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_by"] == test_treasurer2["id"]
    assert data["confirmed_at"] is not None


def test_confirm_money_move_not_found(client, test_treasurer):
    """Test confirming non-existent money move"""
    response = client.patch(
        f"/money-moves/{uuid4()}/confirm",
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 404
    assert "Money move not found" in response.json()["detail"]


def test_confirm_money_move_not_pending(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test confirming non-pending money move"""
    # Create and confirm a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=test_treasurer2["_headers"],
    )
    
    # Try to confirm again
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=test_treasurer2["_headers"],
    )
    assert response.status_code == 400
    assert "Money move is not pending" in response.json()["detail"]


def test_confirm_money_move_self_confirmation(client, test_user, test_treasurer, sample_money_move_data):
    """Test self-confirmation not allowed"""
    # Create a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    # Try to confirm with same user who created it
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 400
    assert "Cannot confirm own money move" in response.json()["detail"]


def test_reject_money_move(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test rejecting a money move"""
    # Create a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    # Reject with different treasurer
    response = client.patch(
        f"/money-moves/{money_move_id}/reject",
        headers=test_treasurer2["_headers"],
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "rejected"
    assert data["confirmed_by"] == test_treasurer2["id"]
    assert data["confirmed_at"] is not None


def test_reject_money_move_not_found(client, test_treasurer):
    """Test rejecting non-existent money move"""
    response = client.patch(
        f"/money-moves/{uuid4()}/reject",
        headers=test_treasurer["_headers"],
    )
    assert response.status_code == 404
    assert "Money move not found" in response.json()["detail"]


def test_reject_money_move_not_pending(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test rejecting non-pending money move"""
    # Create and reject a money move
    create_response = client.post(
        "/money-moves/",
        json=sample_money_move_data,
        headers=test_treasurer["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    client.patch(
        f"/money-moves/{money_move_id}/reject",
        headers=test_treasurer2["_headers"],
    )
    
    # Try to reject again
    response = client.patch(
        f"/money-moves/{money_move_id}/reject",
        headers=test_treasurer2["_headers"],
    )
    assert response.status_code == 400
    assert "Money move is not pending" in response.json()["detail"]


def test_create_user_money_move_request_deposit(client, test_user):
    """Test user creating a money move request for themselves"""
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1500,
        "note": "User self-deposit request"
    }
    response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": test_user["id"], "x-actor-pin": "testpin123"},
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["type"] == "deposit"
    assert data["user_id"] == test_user["id"]
    assert data["amount_cents"] == 1500
    assert data["note"] == "User self-deposit request"
    assert data["status"] == "pending"
    assert data["created_by"] == test_user["id"]
    assert data["confirmed_at"] is None
    assert data["confirmed_by"] is None


def test_create_user_money_move_request_payout(client, test_user):
    """Test user creating a payout money move request for themselves"""
    money_move_data = {
        "type": "payout",
        "user_id": test_user["id"],
        "amount_cents": 500,
        "note": "User self-payout request"
    }
    response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": test_user["id"], "x-actor-pin": "testpin123"},
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["type"] == "payout"
    assert data["user_id"] == test_user["id"]
    assert data["amount_cents"] == 500
    assert data["note"] == "User self-payout request"
    assert data["status"] == "pending"
    assert data["created_by"] == test_user["id"]


def test_create_user_money_move_request_for_other_user_forbidden(client, test_user, admin_bootstrap):
    """Test user cannot create money move request for another user"""
    # Create another user
    import time
    user2_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Test User 2 {int(time.time()*1000)}",
            "role": "user",
            "is_active": True,
            "pin": "testpin456"
        }
    }
    user2 = client.post("/users/", json=user2_payload).json()
    
    money_move_data = {
        "type": "deposit",
        "user_id": user2["id"],  # Different user ID
        "amount_cents": 1000,
        "note": "Trying to create for another user"
    }
    response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": test_user["id"], "x-actor-pin": "testpin123"},
    )
    assert response.status_code == 403
    assert "Users can only create money moves for themselves" in response.json()["detail"]


def test_create_user_money_move_request_invalid_pin(client, test_user):
    """Test user money move request with invalid PIN"""
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test with wrong PIN"
    }
    response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": test_user["id"], "x-actor-pin": "wrongpin"},
    )
    assert response.status_code == 403
    assert "Invalid user PIN" in response.json()["detail"]


def test_create_user_money_move_request_inactive_user(client, admin_bootstrap):
    """Test inactive user cannot create money move request"""
    # Create inactive user
    import time
    inactive_user_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": f"Inactive User {int(time.time()*1000)}",
            "role": "user",
            "is_active": False,
            "pin": "testpin789"
        }
    }
    inactive_user = client.post("/users/", json=inactive_user_payload).json()
    
    money_move_data = {
        "type": "deposit",
        "user_id": inactive_user["id"],
        "amount_cents": 1000,
        "note": "Inactive user request"
    }
    response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": inactive_user["id"], "x-actor-pin": "testpin789"},
    )
    assert response.status_code == 403
    assert "User is not active" in response.json()["detail"]


def test_user_created_money_move_can_be_confirmed_by_treasurer(client, test_user, test_treasurer):
    """Test that a user-created money move can be confirmed by a treasurer"""
    # User creates a money move request
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 2000,
        "note": "User request to be confirmed by treasurer"
    }
    create_response = client.post(
        "/money-moves/user-request",
        json=money_move_data,
        headers={"x-actor-id": test_user["id"], "x-actor-pin": "testpin123"},
    )
    assert create_response.status_code == 201
    money_move_id = create_response.json()["id"]
    
    # Treasurer confirms it
    confirm_response = client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=test_treasurer["_headers"],
    )
    assert confirm_response.status_code == 200
    
    data = confirm_response.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_by"] == test_treasurer["id"]
    assert data["created_by"] == test_user["id"]  # Created by user
    assert data["confirmed_at"] is not None