"""
Test audit service functionality
"""
import pytest
from app.models import User, Audit
from app.services.audit import AuditService
from app.core.enums import UserRole, AuditAction
import uuid


@pytest.fixture
def db_test_user(db_session):
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
    treasurer = User(
        display_name="Test Treasurer",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer)
    db_session.commit()
    db_session.refresh(treasurer)
    return treasurer


def test_log_action_basic(db_session, db_test_user):
    """Test basic audit logging functionality"""
    entity_id = uuid.uuid4()
    meta_data = {"test": "value", "number": 42}
    
    audit_entry = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="create",
        entity="test_entity",
        entity_id=entity_id,
        meta_data=meta_data
    )
    
    assert audit_entry.id is not None
    assert audit_entry.actor_id == db_test_user.id
    assert audit_entry.action == "create"
    assert audit_entry.entity == "test_entity"
    assert audit_entry.entity_id == entity_id
    assert audit_entry.meta_json == meta_data
    assert audit_entry.at is not None
    
    # Verify it was saved to database
    saved_audit = db_session.query(Audit).filter(Audit.id == audit_entry.id).first()
    assert saved_audit is not None
    assert saved_audit.meta_json == meta_data


def test_log_action_without_metadata(db_session, db_test_user):
    """Test audit logging without metadata"""
    entity_id = uuid.uuid4()
    
    audit_entry = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="delete",
        entity="simple_entity",
        entity_id=entity_id
    )
    
    assert audit_entry.meta_json is None
    assert audit_entry.action == "delete"
    assert audit_entry.entity == "simple_entity"


def test_log_consumption_created(db_session, db_test_treasurer, db_test_user):
    """Test logging consumption creation"""
    consumption_id = uuid.uuid4()
    product_name = "Coffee"
    qty = 2
    amount_cents = 300
    
    audit_entry = AuditService.log_consumption_created(
        db=db_session,
        actor_id=db_test_treasurer.id,
        consumption_id=consumption_id,
        user_id=db_test_user.id,
        product_name=product_name,
        qty=qty,
        amount_cents=amount_cents
    )
    
    assert audit_entry.actor_id == db_test_treasurer.id
    assert audit_entry.action == AuditAction.CREATE
    assert audit_entry.entity == "consumption"
    assert audit_entry.entity_id == consumption_id
    
    # Check metadata
    meta = audit_entry.meta_json
    assert meta["user_id"] == str(db_test_user.id)
    assert meta["product_name"] == product_name
    assert meta["qty"] == qty
    assert meta["amount_cents"] == amount_cents


def test_log_money_move_created_deposit(db_session, db_test_treasurer, db_test_user):
    """Test logging money move (deposit) creation"""
    money_move_id = uuid.uuid4()
    amount_cents = 1000
    note = "Test deposit"
    
    audit_entry = AuditService.log_money_move_created(
        db=db_session,
        actor_id=db_test_treasurer.id,
        money_move_id=money_move_id,
        move_type="deposit",
        user_id=db_test_user.id,
        amount_cents=amount_cents,
        note=note
    )
    
    assert audit_entry.actor_id == db_test_treasurer.id
    assert audit_entry.action == AuditAction.CREATE
    assert audit_entry.entity == "money_move"
    assert audit_entry.entity_id == money_move_id
    
    # Check metadata
    meta = audit_entry.meta_json
    assert meta["type"] == "deposit"
    assert meta["user_id"] == str(db_test_user.id)
    assert meta["amount_cents"] == amount_cents
    assert meta["note"] == note


def test_log_money_move_created_payout_no_note(db_session, db_test_treasurer, db_test_user):
    """Test logging money move (payout) creation without note"""
    money_move_id = uuid.uuid4()
    amount_cents = 500
    
    audit_entry = AuditService.log_money_move_created(
        db=db_session,
        actor_id=db_test_treasurer.id,
        money_move_id=money_move_id,
        move_type="payout",
        user_id=db_test_user.id,
        amount_cents=amount_cents
    )
    
    assert audit_entry.entity == "money_move"
    
    # Check metadata
    meta = audit_entry.meta_json
    assert meta["type"] == "payout"
    assert meta["note"] is None


def test_log_money_move_confirmed(db_session, db_test_treasurer):
    """Test logging money move confirmation"""
    money_move_id = uuid.uuid4()
    
    audit_entry = AuditService.log_money_move_confirmed(
        db=db_session,
        actor_id=db_test_treasurer.id,
        money_move_id=money_move_id,
        status="confirmed"
    )
    
    assert audit_entry.actor_id == db_test_treasurer.id
    assert audit_entry.action == AuditAction.CONFIRM
    assert audit_entry.entity == "money_move"
    assert audit_entry.entity_id == money_move_id
    
    # Check metadata
    meta = audit_entry.meta_json
    assert meta["status"] == "confirmed"


def test_log_money_move_rejected(db_session, db_test_treasurer):
    """Test logging money move rejection"""
    money_move_id = uuid.uuid4()
    
    audit_entry = AuditService.log_money_move_confirmed(
        db=db_session,
        actor_id=db_test_treasurer.id,
        money_move_id=money_move_id,
        status="rejected"
    )
    
    assert audit_entry.actor_id == db_test_treasurer.id
    assert audit_entry.action == AuditAction.REJECT
    assert audit_entry.entity == "money_move"
    assert audit_entry.entity_id == money_move_id
    
    # Check metadata
    meta = audit_entry.meta_json
    assert meta["status"] == "rejected"


def test_multiple_audit_entries(db_session, db_test_user, db_test_treasurer):
    """Test creating multiple audit entries"""
    # Create multiple entries
    entries = []
    for i in range(3):
        entry = AuditService.log_action(
            db=db_session,
            actor_id=db_test_user.id if i % 2 == 0 else db_test_treasurer.id,
            action=f"action_{i}",
            entity=f"entity_{i}",
            entity_id=uuid.uuid4(),
            meta_data={"index": i}
        )
        entries.append(entry)
    
    # Verify all entries were created
    all_entries = db_session.query(Audit).all()
    assert len(all_entries) == 3
    
    # Check they have different IDs
    entry_ids = [entry.id for entry in all_entries]
    assert len(set(entry_ids)) == 3  # All unique


def test_audit_entry_timestamps(db_session, db_test_user):
    """Test that audit entries have proper timestamps"""
    import time
    
    # Create first entry
    entry1 = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="first",
        entity="test",
        entity_id=uuid.uuid4()
    )
    
    time.sleep(0.001)  # Small delay to ensure different timestamps
    
    # Create second entry
    entry2 = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="second",
        entity="test",
        entity_id=uuid.uuid4()
    )
    
    # Timestamps should be different (or at least not reversed)
    assert entry2.at >= entry1.at


def test_audit_service_complex_metadata(db_session, db_test_user):
    """Test audit service with complex metadata"""
    complex_data = {
        "user_info": {
            "name": "Test User",
            "actions": ["login", "logout"]
        },
        "transaction_details": {
            "amount": 1000,
            "currency": "EUR",
            "items": [
                {"name": "Coffee", "qty": 2},
                {"name": "Tea", "qty": 1}
            ]
        },
        "flags": [True, False, True]
    }
    
    audit_entry = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="complex_action",
        entity="complex_entity",
        entity_id=uuid.uuid4(),
        meta_data=complex_data
    )
    
    # Verify complex data is preserved
    saved_meta = audit_entry.meta_json
    assert saved_meta["user_info"]["name"] == "Test User"
    assert saved_meta["user_info"]["actions"] == ["login", "logout"]
    assert saved_meta["transaction_details"]["amount"] == 1000
    assert saved_meta["transaction_details"]["items"][0]["name"] == "Coffee"
    assert saved_meta["flags"] == [True, False, True]


def test_audit_service_actor_relationship(db_session, db_test_user):
    """Test that audit entries maintain proper relationship to actor"""
    audit_entry = AuditService.log_action(
        db=db_session,
        actor_id=db_test_user.id,
        action="test",
        entity="test",
        entity_id=uuid.uuid4()
    )
    
    # Test relationship
    assert audit_entry.actor.display_name == "Test User"
    assert audit_entry.actor.role == UserRole.USER
    
    # Test reverse relationship
    assert len(db_test_user.audit_entries) == 1
    assert db_test_user.audit_entries[0].id == audit_entry.id