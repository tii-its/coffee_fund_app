"""
Test money moves API endpoints
"""
import pytest
from app.core.enums import MoneyMoveType, MoneyMoveStatus
from uuid import uuid4


@pytest.fixture
def test_user(client):
    """Create a test user"""
    user_data = {
        "display_name": "Test User",
        "role": "user",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


@pytest.fixture
def test_treasurer(client):
    """Create a test treasurer"""
    user_data = {
        "display_name": "Test Treasurer", 
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


@pytest.fixture
def test_treasurer2(client):
    """Create a second test treasurer"""
    user_data = {
        "display_name": "Test Treasurer 2", 
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=money_move_data
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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=money_move_data
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_money_move_creator_not_found(client, test_user):
    """Test creating money move with invalid creator"""
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test"
    }
    response = client.post(
        f"/money-moves/?creator_id={uuid4()}", 
        json=money_move_data
    )
    assert response.status_code == 404
    assert "Creator not found" in response.json()["detail"]


def test_create_money_move_non_treasurer_creator(client, test_user):
    """Test creating money move with non-treasurer creator"""
    # Create another regular user
    user2_data = {
        "display_name": "Regular User 2",
        "role": "user",
        "is_active": True
    }
    user2_response = client.post("/users/", json=user2_data)
    user2 = user2_response.json()
    
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test"
    }
    response = client.post(
        f"/money-moves/?creator_id={user2['id']}", 
        json=money_move_data
    )
    assert response.status_code == 403
    assert "Only treasurers can create money moves" in response.json()["detail"]


def test_get_money_moves(client, test_user, test_treasurer, sample_money_move_data):
    """Test getting all money moves"""
    # Create a money move first
    client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
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
    # Create a pending money move
    client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
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
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    # Confirm with different treasurer
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer2['id']}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_by"] == test_treasurer2["id"]
    assert data["confirmed_at"] is not None


def test_confirm_money_move_not_found(client, test_treasurer):
    """Test confirming non-existent money move"""
    response = client.patch(
        f"/money-moves/{uuid4()}/confirm?confirmer_id={test_treasurer['id']}"
    )
    assert response.status_code == 404
    assert "Money move not found" in response.json()["detail"]


def test_confirm_money_move_not_pending(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test confirming non-pending money move"""
    # Create and confirm a money move
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    client.patch(
        f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer2['id']}"
    )
    
    # Try to confirm again
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer2['id']}"
    )
    assert response.status_code == 400
    assert "Money move is not pending" in response.json()["detail"]


def test_confirm_money_move_self_confirmation(client, test_user, test_treasurer, sample_money_move_data):
    """Test self-confirmation not allowed"""
    # Create a money move
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    # Try to confirm with same user who created it
    response = client.patch(
        f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer['id']}"
    )
    assert response.status_code == 400
    assert "Cannot confirm own money move" in response.json()["detail"]


def test_reject_money_move(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test rejecting a money move"""
    # Create a money move
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    # Reject with different treasurer
    response = client.patch(
        f"/money-moves/{money_move_id}/reject?rejector_id={test_treasurer2['id']}"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "rejected"
    assert data["confirmed_by"] == test_treasurer2["id"]
    assert data["confirmed_at"] is not None


def test_reject_money_move_not_found(client, test_treasurer):
    """Test rejecting non-existent money move"""
    response = client.patch(
        f"/money-moves/{uuid4()}/reject?rejector_id={test_treasurer['id']}"
    )
    assert response.status_code == 404
    assert "Money move not found" in response.json()["detail"]


def test_reject_money_move_not_pending(client, test_user, test_treasurer, test_treasurer2, sample_money_move_data):
    """Test rejecting non-pending money move"""
    # Create and reject a money move
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=sample_money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    client.patch(
        f"/money-moves/{money_move_id}/reject?rejector_id={test_treasurer2['id']}"
    )
    
    # Try to reject again
    response = client.patch(
        f"/money-moves/{money_move_id}/reject?rejector_id={test_treasurer2['id']}"
    )
    assert response.status_code == 400
    assert "Money move is not pending" in response.json()["detail"]