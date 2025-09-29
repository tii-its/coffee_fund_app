"""
Integration tests for complete business workflows
"""
import pytest
import uuid


@pytest.fixture
def setup_users_and_product(client):
    """Set up basic test data: users and product"""
    import time
    ts = int(time.time()*1000)
    # Create regular user
    user_data = {
        "display_name": "Coffee Consumer",
        "email": f"workflow.user.{ts}@example.com",
        "role": "user",
        "is_active": True,
        "pin": "testpin123"  # PIN is now required for all users
    }
    user_response = client.post("/users/", json=user_data)
    user = user_response.json()
    
    # Create two treasurers for two-person approval
    treasurer1_data = {
        "display_name": "Treasurer One",
        "email": f"workflow.treas1.{ts}@example.com",
        "role": "treasurer",
        "is_active": True,
        "pin": "treasOnePIN"
    }
    treasurer1_response = client.post("/users/", json=treasurer1_data)
    treasurer1 = treasurer1_response.json()
    
    treasurer2_data = {
        "display_name": "Treasurer Two", 
        "email": f"workflow.treas2.{ts}@example.com",
        "role": "treasurer",
        "is_active": True,
        "pin": "treasTwoPIN"
    }
    treasurer2_response = client.post("/users/", json=treasurer2_data)
    treasurer2 = treasurer2_response.json()
    
    # Create product
    product_data = {
        # Unique product name per test run to avoid duplicate name constraint collisions
        "name": f"Premium Coffee {ts}",
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
    
    # Step 1: Check initial balance (should be 0) via API
    balance_response = client.get(f"/users/{user['id']}/balance")
    assert balance_response.status_code == 200
    initial_balance = balance_response.json()["balance_cents"]
    assert initial_balance == 0
    
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
    assert create_response.status_code == 201
    money_move = create_response.json()
    
    # Verify it's pending
    assert money_move["status"] == "pending"
    assert money_move["amount_cents"] == 2000
    assert money_move["confirmed_at"] is None
    
    # Step 3: Check that balance hasn't changed yet (pending deposits don't count)
    # Use public API balance endpoint for consistency (avoids direct session mismatches)
    balance_after_create_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_create_resp.status_code == 200
    assert balance_after_create_resp.json()["balance_cents"] == 0
    
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
    balance_after_confirm_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_confirm_resp.status_code == 200
    assert balance_after_confirm_resp.json()["balance_cents"] == 2000
    
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
    balance_after_reject_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_reject_resp.status_code == 200
    assert balance_after_reject_resp.json()["balance_cents"] == 0


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
    balance_after_deposit_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_deposit_resp.status_code == 200
    assert balance_after_deposit_resp.json()["balance_cents"] == 1000
    
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
    assert consume_response.status_code == 201
    consumption = consume_response.json()
    
    # Verify consumption details
    assert consumption["qty"] == 3
    assert consumption["unit_price_cents"] == 200  # Product price
    assert consumption["amount_cents"] == 600  # 3 * 200
    
    # Step 3: Check updated balance
    balance_after_consumption_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_consumption_resp.status_code == 200
    assert balance_after_consumption_resp.json()["balance_cents"] == 400
    
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
        assert response.status_code == 201
        
        consumption = response.json()
        assert consumption["amount_cents"] == session["expected_cost"]
        
        total_spent += session["expected_cost"]
        
        # Check balance after each consumption
        balance_iter_resp = client.get(f"/users/{user['id']}/balance")
        assert balance_iter_resp.status_code == 200
        expected_balance = 2000 - total_spent
        assert balance_iter_resp.json()["balance_cents"] == expected_balance
    
    # Final verification
    assert total_spent == 1200  # Total: 400 + 200 + 600
    
    final_balance_resp = client.get(f"/users/{user['id']}/balance")
    assert final_balance_resp.status_code == 200
    assert final_balance_resp.json()["balance_cents"] == 800
    
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
    balance_before_payout_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_before_payout_resp.status_code == 200
    assert balance_before_payout_resp.json()["balance_cents"] == 1100
    
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
    balance_after_request_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_request_resp.status_code == 200
    assert balance_after_request_resp.json()["balance_cents"] == 1100
    
    # Confirm payout
    confirm_response = client.patch(
        f"/money-moves/{payout_move['id']}/confirm?confirmer_id={treasurer2['id']}"
    )
    assert confirm_response.status_code == 200
    
    # Balance should now be reduced
    final_balance_resp = client.get(f"/users/{user['id']}/balance")
    assert final_balance_resp.status_code == 200
    assert final_balance_resp.json()["balance_cents"] == 600


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