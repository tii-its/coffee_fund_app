from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID
from app.core.enums import MoneyMoveType, MoneyMoveStatus


class MoneyMove(Base):
    __tablename__ = "money_moves"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(MoneyMoveType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(MoneyMoveStatus, values_callable=lambda x: [e.value for e in x]), default=MoneyMoveStatus.PENDING, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="money_moves")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_money_moves")
    confirmer = relationship("User", foreign_keys=[confirmed_by], back_populates="confirmed_money_moves")

    def __repr__(self):
        return f"<MoneyMove(id={self.id}, type='{self.type}', user_id={self.user_id}, amount_cents={self.amount_cents}, status='{self.status}')>"