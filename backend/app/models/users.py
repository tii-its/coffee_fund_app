from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True, unique=True)
    qr_code = Column(String(255), nullable=True, index=True)
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    consumptions = relationship("Consumption", foreign_keys="Consumption.user_id", back_populates="user")
    created_consumptions = relationship("Consumption", foreign_keys="Consumption.created_by", back_populates="creator")
    money_moves = relationship("MoneyMove", foreign_keys="MoneyMove.user_id", back_populates="user")
    created_money_moves = relationship("MoneyMove", foreign_keys="MoneyMove.created_by", back_populates="creator")
    confirmed_money_moves = relationship("MoneyMove", foreign_keys="MoneyMove.confirmed_by", back_populates="confirmer")
    audit_entries = relationship("Audit", back_populates="actor")

    def __repr__(self):
        return f"<User(id={self.id}, display_name='{self.display_name}', email='{self.email}', role='{self.role}')>"