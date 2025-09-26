import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models import User, Product
from app.core.enums import UserRole

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_models.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_user_model(db_session):
    """Test user model creation and relationships"""
    user = User(
        display_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.display_name == "Test User"
    assert user.role == UserRole.USER
    assert user.is_active == True
    assert user.created_at is not None


def test_product_model(db_session):
    """Test product model creation"""
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    
    assert product.id is not None
    assert product.name == "Coffee"
    assert product.price_cents == 150
    assert product.is_active == True
    assert product.created_at is not None