from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID


class Consumption(Base):
    __tablename__ = "consumptions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(), ForeignKey("products.id"), nullable=False, index=True)
    qty = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="consumptions")
    product = relationship("Product", back_populates="consumptions")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_consumptions")

    def __repr__(self):
        return f"<Consumption(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, qty={self.qty})>"