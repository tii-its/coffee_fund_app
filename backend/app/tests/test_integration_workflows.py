"""
Integration tests for complete business workflows
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from app.services.balance import BalanceService
import uuid

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"

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


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def setup_users_and_product(client):
    """Set up basic test data: users and product"""
    # Create regular user
    user_data = {
        "display_name": "Coffee Consumer",
        "role": "user",
        "is_active": True
    }
    user_response = client.post("/users/", json=user_data)
    user = user_response.json()
    
    # Create two treasurers for two-person approval
    treasurer1_data = {
        "display_name": "Treasurer One",
        "role": "treasurer",
        "is_active": True
    }
    treasurer1_response = client.post("/users/", json=treasurer1_data)
    treasurer1 = treasurer1_response.json()
    
    treasurer2_data = {
        "display_name": "Treasurer Two", 
        "role": "treasurer",
        "is_active": True
    }
    treasurer2_response = client.post("/users/", json=treasurer2_data)
    treasurer2 = treasurer2_response.json()
    
    # Create product
    product_data = {
        "name": "Premium Coffee",
        "price_cents": 200,
        "is_active": True
    }
    product_response = client.post("/products/", json=product_data)
    product = product_response.json()
    
    return {
        "user": user,
        "treasurer1": treasurer1,
        "treasurer2": treasurer2,
        "product": product
    }


def test_complete_deposit_workflow(client, setup_users_and_product):
    """Test complete deposit workflow: create -> confirm -> verify balance"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    
    # Step 1: Check initial balance (should be 0)
    db = next(override_get_db())
    try:
        initial_balance = BalanceService.get_user_balance(db, user["id"])
        assert initial_balance == 0
    finally:
        db.close()
    
    # Step 2: Treasurer 1 creates a deposit request
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 2000,  # 20 euros
        "note": "Monthly coffee deposit"
    }
    
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    assert create_response.status_code == 200
    money_move = create_response.json()
    
    # Verify it's pending
    assert money_move["status"] == "pending"
    assert money_move["amount_cents"] == 2000
    assert money_move["confirmed_at"] is None
    
    # Step 3: Check that balance hasn't changed yet (pending deposits don't count)
    db = next(override_get_db())
    try:
        balance_after_create = BalanceService.get_user_balance(db, user["id"])
        assert balance_after_create == 0  # Still zero
    finally:
        db.close()
    
    # Step 4: Check pending money moves
    pending_response = client.get("/money-moves/pending")
    assert pending_response.status_code == 200
    pending_moves = pending_response.json()
    assert len(pending_moves) == 1
    assert pending_moves[0]["id"] == money_move["id"]
    
    # Step 5: Treasurer 2 confirms the deposit
    confirm_response = client.patch(
        f"/money-moves/{money_move['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    assert confirm_response.status_code == 200
    confirmed_move = confirm_response.json()
    
    # Verify it's now confirmed
    assert confirmed_move["status"] == "confirmed"
    assert confirmed_move["confirmed_by"] == treasurer2["id"]
    assert confirmed_move["confirmed_at"] is not None
    
    # Step 6: Check that balance has now updated
    db = next(override_get_db())
    try:
        final_balance = BalanceService.get_user_balance(db, user["id"])
        assert final_balance == 2000  # 20 euros
    finally:
        db.close()
    
    # Step 7: Check no more pending moves
    pending_response = client.get("/money-moves/pending")
    pending_moves = pending_response.json()
    assert len(pending_moves) == 0
    
    # Step 8: Verify audit trail exists
    audit_response = client.get(f"/audit/?actor_id={treasurer1['id']}")
    assert audit_response.status_code == 200
    audit_entries = audit_response.json()
    
    # Should have creation audit entry
    creation_entry = next((entry for entry in audit_entries if entry["action"] == "create"), None)
    assert creation_entry is not None
    assert creation_entry["entity"] == "money_move"


def test_deposit_rejection_workflow(client, setup_users_and_product):
    """Test deposit rejection workflow"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    
    # Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Test deposit for rejection"
    }
    
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    money_move = create_response.json()
    
    # Reject the deposit
    reject_response = client.patch(
        f"/money-moves/{money_move['id']}/reject?rejector_id={treasurer2['id']}"
    )
    assert reject_response.status_code == 200
    rejected_move = reject_response.json()
    
    assert rejected_move["status"] == "rejected"
    assert rejected_move["confirmed_by"] == treasurer2["id"]
    
    # Balance should still be 0
    db = next(override_get_db())
    try:
        balance = BalanceService.get_user_balance(db, user["id"])
        assert balance == 0
    finally:
        db.close()


def test_consumption_workflow(client, setup_users_and_product):
    """Test consumption workflow: deposit -> consume -> check balance"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Step 1: Add money to user account
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,  # 10 euros
        "note": "Initial deposit"
    }
    
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    money_move = create_response.json()
    
    # Confirm deposit
    client.patch(
        f"/money-moves/{money_move['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    
    # Verify balance
    db = next(override_get_db())
    try:
        balance_after_deposit = BalanceService.get_user_balance(db, user["id"])
        assert balance_after_deposit == 1000
    finally:
        db.close()
    
    # Step 2: User consumes coffee
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 3  # 3 coffees at 200 cents each = 600 cents
    }
    
    consume_response = client.post(
        f"/consumptions/?creator_id={treasurer1['id']}", 
        json=consumption_data
    )
    assert consume_response.status_code == 200
    consumption = consume_response.json()
    
    # Verify consumption details
    assert consumption["qty"] == 3
    assert consumption["unit_price_cents"] == 200  # Product price
    assert consumption["amount_cents"] == 600  # 3 * 200
    
    # Step 3: Check updated balance
    db = next(override_get_db())
    try:
        balance_after_consumption = BalanceService.get_user_balance(db, user["id"])
        assert balance_after_consumption == 400  # 1000 - 600
    finally:
        db.close()
    
    # Step 4: Check consumption history
    user_consumptions_response = client.get(f"/consumptions/user/{user['id']}/recent")
    assert user_consumptions_response.status_code == 200
    user_consumptions = user_consumptions_response.json()
    
    assert len(user_consumptions) == 1
    assert user_consumptions[0]["id"] == consumption["id"]


def test_multiple_consumptions_and_balance_tracking(client, setup_users_and_product):
    """Test multiple consumptions and accurate balance tracking"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Add initial money
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 2000,  # 20 euros
        "note": "Large deposit"
    }
    
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    client.patch(
        f"/money-moves/{create_response.json()['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    
    # Multiple consumption sessions
    consumption_sessions = [
        {"qty": 2, "expected_cost": 400},  # 2 * 200
        {"qty": 1, "expected_cost": 200},  # 1 * 200
        {"qty": 3, "expected_cost": 600},  # 3 * 200
    ]
    
    total_spent = 0
    
    for i, session in enumerate(consumption_sessions):
        consumption_data = {
            "user_id": user["id"],
            "product_id": product["id"],
            "qty": session["qty"]
        }
        
        response = client.post(
            f"/consumptions/?creator_id={treasurer1['id']}", 
            json=consumption_data
        )
        assert response.status_code == 200
        
        consumption = response.json()
        assert consumption["amount_cents"] == session["expected_cost"]
        
        total_spent += session["expected_cost"]
        
        # Check balance after each consumption
        db = next(override_get_db())
        try:
            current_balance = BalanceService.get_user_balance(db, user["id"])
            expected_balance = 2000 - total_spent
            assert current_balance == expected_balance
        finally:
            db.close()
    
    # Final verification
    assert total_spent == 1200  # Total: 400 + 200 + 600
    
    db = next(override_get_db())
    try:
        final_balance = BalanceService.get_user_balance(db, user["id"])
        assert final_balance == 800  # 2000 - 1200
    finally:
        db.close()
    
    # Check consumption history
    all_consumptions_response = client.get(f"/consumptions/?user_id={user['id']}")
    all_consumptions = all_consumptions_response.json()
    assert len(all_consumptions) == 3


def test_payout_workflow(client, setup_users_and_product):
    """Test payout workflow: deposit -> consume -> payout remaining balance"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Initial deposit
    deposit_data = {
        "type": "deposit", 
        "user_id": user["id"],
        "amount_cents": 1500,
        "note": "Test deposit for payout"
    }
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    client.patch(
        f"/money-moves/{create_response.json()['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    
    # Consume some coffee
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 2  # 400 cents
    }
    client.post(
        f"/consumptions/?creator_id={treasurer1['id']}", 
        json=consumption_data
    )
    
    # Balance should be 1100 cents now
    db = next(override_get_db())
    try:
        balance_before_payout = BalanceService.get_user_balance(db, user["id"])
        assert balance_before_payout == 1100  # 1500 - 400
    finally:
        db.close()
    
    # Request payout
    payout_data = {
        "type": "payout",
        "user_id": user["id"],
        "amount_cents": 500,  # 5 euros payout
        "note": "Partial payout"
    }
    
    payout_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=payout_data
    )
    payout_move = payout_response.json()
    
    # Balance shouldn't change yet (pending)
    db = next(override_get_db())
    try:
        balance_after_request = BalanceService.get_user_balance(db, user["id"])
        assert balance_after_request == 1100  # Still same
    finally:
        db.close()
    
    # Confirm payout
    confirm_response = client.patch(
        f"/money-moves/{payout_move['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    assert confirm_response.status_code == 200
    
    # Balance should now be reduced
    db = next(override_get_db())
    try:
        final_balance = BalanceService.get_user_balance(db, user["id"])
        assert final_balance == 600  # 1100 - 500
    finally:
        db.close()


def test_self_confirmation_prevention(client, setup_users_and_product):
    """Test that users cannot confirm their own money moves"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    
    # Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Self-confirmation test"
    }
    
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    money_move = create_response.json()
    
    # Try to confirm with same treasurer
    confirm_response = client.patch(
        f"/money-moves/{money_move['id']}/confirm?confirmer_id={treasurer1['id']}"
    )
    
    assert confirm_response.status_code == 400
    assert "Cannot confirm own money move" in confirm_response.json()["detail"]
    
    # Verify it's still pending
    get_response = client.get(f"/money-moves/{money_move['id']}")
    move_data = get_response.json()
    assert move_data["status"] == "pending"


def test_export_integration_with_real_data(client, setup_users_and_product):
    """Test CSV export with actual transaction data"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Create transactions
    # 1. Deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 2000,
        "note": "Export test deposit"
    }
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    money_move_id = create_response.json()["id"]
    client.patch(f"/money-moves/{money_move_id}/confirm?confirmer_id={treasurer2['id']}")
    
    # 2. Consumption
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 2
    }
    client.post(
        f"/consumptions/?creator_id={treasurer1['id']}", 
        json=consumption_data
    )
    
    # Test exports
    # Export consumptions
    consumptions_export = client.get("/exports/consumptions")
    assert consumptions_export.status_code == 200
    assert "text/csv" in consumptions_export.headers["content-type"]
    csv_content = consumptions_export.text
    assert "Coffee Consumer" in csv_content
    assert "Premium Coffee" in csv_content
    
    # Export money moves
    money_moves_export = client.get("/exports/money-moves")
    assert money_moves_export.status_code == 200
    assert "text/csv" in money_moves_export.headers["content-type"]
    csv_content = money_moves_export.text
    assert "Coffee Consumer" in csv_content
    assert "Export test deposit" in csv_content
    assert "Confirmed" in csv_content
    
    # Export balances
    balances_export = client.get("/exports/balances")
    assert balances_export.status_code == 200
    assert "text/csv" in balances_export.headers["content-type"]
    csv_content = balances_export.text
    assert "Coffee Consumer" in csv_content
    # Balance should be 1600 cents = 16.00 euros (2000 - 400)
    assert "16.00" in csv_content


def test_audit_trail_comprehensive(client, setup_users_and_product):
    """Test that all actions create proper audit trails"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Perform various actions
    # 1. Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Audit test deposit"
    }
    create_response = client.post(
        f"/money-moves/?creator_id={treasurer1['id']}", 
        json=deposit_data
    )
    money_move_id = create_response.json()["id"]
    
    # 2. Confirm deposit
    client.patch(f"/money-moves/{money_move_id}/confirm?confirmer_id={treasurer2['id']}")
    
    # 3. Create consumption
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 1
    }
    client.post(
        f"/consumptions/?creator_id={treasurer1['id']}", 
        json=consumption_data
    )
    
    # Check audit entries
    audit_response = client.get("/audit/")
    assert audit_response.status_code == 200
    audit_entries = audit_response.json()
    
    # Should have multiple entries
    assert len(audit_entries) >= 3
    
    # Check for different types of actions
    actions = [entry["action"] for entry in audit_entries]
    entities = [entry["entity"] for entry in audit_entries]
    
    assert "create" in actions
    assert "confirm" in actions
    assert "money_move" in entities
    assert "consumption" in entities
    
    # Check specific audit entries
    money_move_creation = next((entry for entry in audit_entries 
                               if entry["action"] == "create" and entry["entity"] == "money_move"), None)
    assert money_move_creation is not None
    assert money_move_creation["actor_id"] == treasurer1["id"]
    
    money_move_confirmation = next((entry for entry in audit_entries 
                                  if entry["action"] == "confirm" and entry["entity"] == "money_move"), None)
    assert money_move_confirmation is not None
    assert money_move_confirmation["actor_id"] == treasurer2["id"]
    
    consumption_creation = next((entry for entry in audit_entries 
                               if entry["action"] == "create" and entry["entity"] == "consumption"), None)
    assert consumption_creation is not None
    assert consumption_creation["actor_id"] == treasurer1["id"]