import pytest
from app.models import User, Product, Consumption, MoneyMove
from app.services.balance import BalanceService
from app.core.enums import UserRole, MoneyMoveType, MoneyMoveStatus


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
def db_test_product(db_session):
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_balance_calculation_no_transactions(db_session, db_test_user):
    """Test balance calculation with no transactions"""
    balance = BalanceService.get_user_balance(db_session, str(db_test_user.id))
    assert balance == 0


def test_balance_calculation_with_deposit(db_session, db_test_user):
    """Test balance calculation with confirmed deposit"""
    # Create a confirmed deposit
    deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(deposit)
    db_session.commit()
    
    balance = BalanceService.get_user_balance(db_session, str(db_test_user.id))
    assert balance == 1000


def test_balance_calculation_with_consumption(db_session, db_test_user, db_test_product):
    """Test balance calculation with consumption"""
    # Create a confirmed deposit first
    deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(deposit)
    db_session.commit()
    
    # Create a consumption
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=db_test_user.id
    )
    db_session.add(consumption)
    db_session.commit()
    
    # Balance should be deposit minus consumption (1000 - 300 = 700)
    balance = BalanceService.get_user_balance(db_session, str(db_test_user.id))
    assert balance == 700


def test_balance_calculation_pending_deposit_ignored(db_session, db_test_user, db_test_product):
    """Test that pending deposits are ignored in balance calculation"""
    # Create a confirmed deposit first
    confirmed_deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        created_by=db_test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(confirmed_deposit)
    
    # Create a consumption
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=db_test_user.id
    )
    db_session.add(consumption)
    
    # Create a pending deposit
    pending_deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=500,
        created_by=db_test_user.id,
        status=MoneyMoveStatus.PENDING
    )
    db_session.add(pending_deposit)
    db_session.commit()
    
    # Balance should be confirmed deposit minus consumption = 700 (pending deposits don't count)
    balance = BalanceService.get_user_balance(db_session, str(db_test_user.id))
    assert balance == 700


def test_get_users_above_threshold(db_session):
    """Test getting users with balance above or equal to threshold"""
    # Create users with different balances
    user1 = User(display_name="User1", role=UserRole.USER, is_active=True)
    user2 = User(display_name="User2", role=UserRole.USER, is_active=True)  
    user3 = User(display_name="User3", role=UserRole.USER, is_active=True)
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    
    # Add money moves to give different balances
    # User1: 1500 cents (above threshold of 1000)
    deposit1 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user1.id,
        amount_cents=1500,
        created_by=user1.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    # User2: 1000 cents (equal to threshold)
    deposit2 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user2.id,
        amount_cents=1000,
        created_by=user2.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    # User3: 500 cents (below threshold)
    deposit3 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user3.id,
        amount_cents=500,
        created_by=user3.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    db_session.add_all([deposit1, deposit2, deposit3])
    db_session.commit()
    
    # Test above threshold (should include users with >= 1000 cents)
    above_threshold = BalanceService.get_users_above_threshold(db_session, 1000)
    assert len(above_threshold) == 2
    
    # Should include user1 and user2 (both >= 1000)
    user_names = [balance.user.display_name for balance in above_threshold]
    assert "User1" in user_names
    assert "User2" in user_names
    assert "User3" not in user_names
    
    # Check balances are correct
    for balance in above_threshold:
        if balance.user.display_name == "User1":
            assert balance.balance_cents == 1500
        elif balance.user.display_name == "User2":
            assert balance.balance_cents == 1000


def test_get_users_below_threshold(db_session):
    """Test getting users with balance below threshold"""
    # Create users with different balances
    user1 = User(display_name="User1", role=UserRole.USER, is_active=True)
    user2 = User(display_name="User2", role=UserRole.USER, is_active=True)  
    user3 = User(display_name="User3", role=UserRole.USER, is_active=True)
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    
    # Add money moves to give different balances
    # User1: 1500 cents (above threshold)
    deposit1 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user1.id,
        amount_cents=1500,
        created_by=user1.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    # User2: 1000 cents (equal to threshold)
    deposit2 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user2.id,
        amount_cents=1000,
        created_by=user2.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    # User3: 500 cents (below threshold)
    deposit3 = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=user3.id,
        amount_cents=500,
        created_by=user3.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    
    db_session.add_all([deposit1, deposit2, deposit3])
    db_session.commit()
    
    # Test below threshold (should include users with < 1000 cents)
    below_threshold = BalanceService.get_users_below_threshold(db_session, 1000)
    assert len(below_threshold) == 1
    
    # Should include only user3
    user_names = [balance.user.display_name for balance in below_threshold]
    assert "User3" in user_names
    assert "User1" not in user_names
    assert "User2" not in user_names
    
    # Check balance is correct
    assert below_threshold[0].balance_cents == 500