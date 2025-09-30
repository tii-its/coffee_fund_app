"""
Test consumption, money move, and audit models
"""
import pytest
from app.models import User, Product, Consumption, MoneyMove, Audit
from app.core.enums import UserRole, MoneyMoveType, MoneyMoveStatus
import uuid
from datetime import datetime


@pytest.fixture
def db_test_user(db_session):
    """Create a test user"""
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
    """Create a test treasurer"""
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
def db_test_product(db_session):
    """Create a test product"""
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# Consumption Model Tests
def test_consumption_model_creation(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test creating a consumption model"""
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=db_test_treasurer.id
    )
    
    db_session.add(consumption)
    db_session.commit()
    db_session.refresh(consumption)
    
    assert consumption.id is not None
    assert consumption.user_id == db_test_user.id
    assert consumption.product_id == db_test_product.id
    assert consumption.qty == 2
    assert consumption.unit_price_cents == 150
    assert consumption.amount_cents == 300
    assert consumption.created_by == db_test_treasurer.id
    assert consumption.at is not None


def test_consumption_model_relationships(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test consumption model relationships"""
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=1,
        unit_price_cents=150,
        amount_cents=150,
        created_by=db_test_treasurer.id
    )
    
    db_session.add(consumption)
    db_session.commit()
    db_session.refresh(consumption)
    
    # Test relationships
    assert consumption.user.display_name == "Test User"
    assert consumption.product.name == "Coffee"
    assert consumption.creator.display_name == "Test Treasurer"
    
    # Test reverse relationships
    assert len(db_test_user.consumptions) == 1
    assert db_test_user.consumptions[0].id == consumption.id
    
    assert len(db_test_product.consumptions) == 1
    assert db_test_product.consumptions[0].id == consumption.id
    
    assert len(db_test_treasurer.created_consumptions) == 1
    assert db_test_treasurer.created_consumptions[0].id == consumption.id


def test_consumption_model_repr(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test consumption model string representation"""
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=db_test_treasurer.id
    )
    
    db_session.add(consumption)
    db_session.commit()
    db_session.refresh(consumption)
    
    repr_str = repr(consumption)
    assert "Consumption" in repr_str
    assert str(consumption.id) in repr_str
    assert str(consumption.user_id) in repr_str
    assert str(consumption.product_id) in repr_str
    assert str(consumption.qty) in repr_str


def test_consumption_model_uuid_primary_key(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test that consumption has UUID primary key"""
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=1,
        unit_price_cents=150,
        amount_cents=150,
        created_by=db_test_treasurer.id
    )
    
    db_session.add(consumption)
    db_session.commit()
    db_session.refresh(consumption)
    
    # Should be a UUID
    assert isinstance(consumption.id, uuid.UUID)
    assert len(str(consumption.id)) == 36  # Standard UUID string length


# MoneyMove Model Tests
def test_money_move_model_creation_deposit(db_session, db_test_user, db_test_treasurer):
    """Test creating a deposit money move model"""
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        note="Test deposit",
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    
    db_session.add(money_move)
    db_session.commit()
    db_session.refresh(money_move)
    
    assert money_move.id is not None
    assert money_move.type == MoneyMoveType.DEPOSIT
    assert money_move.user_id == db_test_user.id
    assert money_move.amount_cents == 1000
    assert money_move.note == "Test deposit"
    assert money_move.created_by == db_test_treasurer.id
    assert money_move.status == MoneyMoveStatus.PENDING
    assert money_move.created_at is not None
    assert money_move.confirmed_at is None
    assert money_move.confirmed_by is None


def test_money_move_model_creation_payout(db_session, db_test_user, db_test_treasurer):
    """Test creating a payout money move model"""
    money_move = MoneyMove(
        type=MoneyMoveType.PAYOUT,
        user_id=db_test_user.id,
        amount_cents=500,
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    
    db_session.add(money_move)
    db_session.commit()
    db_session.refresh(money_move)
    
    assert money_move.type == MoneyMoveType.PAYOUT
    assert money_move.amount_cents == 500
    assert money_move.note is None  # Optional field


def test_money_move_model_confirmation(db_session, db_test_user, db_test_treasurer):
    """Test money move confirmation process"""
    # Create second treasurer for confirmation
    treasurer2 = User(
        display_name="Treasurer 2",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer2)
    db_session.commit()
    db_session.refresh(treasurer2)
    
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    
    db_session.add(money_move)
    db_session.commit()
    db_session.refresh(money_move)
    
    # Confirm the money move
    money_move.status = MoneyMoveStatus.CONFIRMED
    money_move.confirmed_at = datetime.utcnow()
    money_move.confirmed_by = treasurer2.id
    
    db_session.commit()
    db_session.refresh(money_move)
    
    assert money_move.status == MoneyMoveStatus.CONFIRMED
    assert money_move.confirmed_at is not None
    assert money_move.confirmed_by == treasurer2.id


def test_money_move_model_relationships(db_session, db_test_user, db_test_treasurer):
    """Test money move model relationships"""
    # Create confirmer
    confirmer = User(
        display_name="Confirmer",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(confirmer)
    db_session.commit()
    db_session.refresh(confirmer)
    
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.CONFIRMED,
        confirmed_by=confirmer.id,
        confirmed_at=datetime.utcnow()
    )
    
    db_session.add(money_move)
    db_session.commit()
    db_session.refresh(money_move)
    
    # Test relationships
    assert money_move.user.display_name == "Test User"
    assert money_move.creator.display_name == "Test Treasurer"
    assert money_move.confirmer.display_name == "Confirmer"
    
    # Test reverse relationships
    assert len(db_test_user.money_moves) == 1
    assert db_test_user.money_moves[0].id == money_move.id
    
    assert len(db_test_treasurer.created_money_moves) == 1
    assert db_test_treasurer.created_money_moves[0].id == money_move.id
    
    assert len(confirmer.confirmed_money_moves) == 1
    assert confirmer.confirmed_money_moves[0].id == money_move.id


def test_money_move_model_repr(db_session, db_test_user, db_test_treasurer):
    """Test money move model string representation"""
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    
    db_session.add(money_move)
    db_session.commit()
    db_session.refresh(money_move)
    
    repr_str = repr(money_move)
    assert "MoneyMove" in repr_str
    assert str(money_move.id) in repr_str
    assert "DEPOSIT" in repr_str
    assert str(money_move.user_id) in repr_str
    assert "1000" in repr_str


def test_money_move_model_statuses(db_session, db_test_user, db_test_treasurer):
    """Test different money move statuses"""
    # Test all status types
    statuses = [MoneyMoveStatus.PENDING, MoneyMoveStatus.CONFIRMED, MoneyMoveStatus.REJECTED]
    
    for status in statuses:
        money_move = MoneyMove(
            type=MoneyMoveType.DEPOSIT,
            user_id=db_test_user.id,
            amount_cents=1000,
            created_by=db_test_treasurer.id,
            status=status
        )
        
        db_session.add(money_move)
        db_session.commit()
        db_session.refresh(money_move)
        
        assert money_move.status == status


# Audit Model Tests
def test_audit_model_creation(db_session, db_test_user):
    """Test creating an audit model"""
    entity_id = uuid.uuid4()
    meta_data = {"test": "data", "number": 123}
    
    audit = Audit(
        actor_id=db_test_user.id,
        action="create",
        entity="test_entity",
        entity_id=entity_id,
        meta_json=meta_data
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    assert audit.id is not None
    assert audit.actor_id == db_test_user.id
    assert audit.action == "create"
    assert audit.entity == "test_entity"
    assert audit.entity_id == entity_id
    assert audit.meta_json == meta_data
    assert audit.at is not None


def test_audit_model_relationships(db_session, db_test_user):
    """Test audit model relationships"""
    audit = Audit(
        actor_id=db_test_user.id,
        action="create",
        entity="test_entity",
        entity_id=uuid.uuid4(),
        meta_json={"test": "data"}
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    # Test relationship
    assert audit.actor.display_name == "Test User"
    
    # Test reverse relationship
    assert len(db_test_user.audit_entries) == 1
    assert db_test_user.audit_entries[0].id == audit.id


def test_audit_model_repr(db_session, db_test_user):
    """Test audit model string representation"""
    entity_id = uuid.uuid4()
    audit = Audit(
        actor_id=db_test_user.id,
        action="create",
        entity="test_entity",
        entity_id=entity_id,
        meta_json={"test": "data"}
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    repr_str = repr(audit)
    assert "Audit" in repr_str
    assert str(audit.id) in repr_str
    assert "create" in repr_str
    assert "test_entity" in repr_str
    assert str(entity_id) in repr_str


def test_audit_model_json_metadata(db_session, db_test_user):
    """Test audit model JSON metadata handling"""
    complex_meta = {
        "string": "value",
        "number": 42,
        "boolean": True,
        "list": [1, 2, 3],
        "nested": {
            "inner": "value"
        }
    }
    
    audit = Audit(
        actor_id=db_test_user.id,
        action="update",
        entity="complex_entity",
        entity_id=uuid.uuid4(),
        meta_json=complex_meta
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    # JSON should be preserved correctly
    assert audit.meta_json == complex_meta
    assert audit.meta_json["string"] == "value"
    assert audit.meta_json["number"] == 42
    assert audit.meta_json["boolean"] is True
    assert audit.meta_json["list"] == [1, 2, 3]
    assert audit.meta_json["nested"]["inner"] == "value"


def test_audit_model_optional_metadata(db_session, db_test_user):
    """Test audit model with no metadata"""
    audit = Audit(
        actor_id=db_test_user.id,
        action="delete",
        entity="simple_entity",
        entity_id=uuid.uuid4()
        # meta_json is optional
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    assert audit.meta_json is None


def test_audit_model_uuid_fields(db_session, db_test_user):
    """Test that audit model has proper UUID fields"""
    entity_id = uuid.uuid4()
    audit = Audit(
        actor_id=db_test_user.id,
        action="create",
        entity="test_entity",
        entity_id=entity_id
    )
    
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    
    # Should be UUIDs
    assert isinstance(audit.id, uuid.UUID)
    assert isinstance(audit.actor_id, uuid.UUID)
    assert isinstance(audit.entity_id, uuid.UUID)
    assert audit.entity_id == entity_id