from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID


class StockPurchase(Base):
    __tablename__ = "stock_purchases"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    item_name = Column(String(255), nullable=False, index=True)
    supplier = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    total_amount_cents = Column(Integer, nullable=False)
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    receipt_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_cash_out_processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<StockPurchase(id={self.id}, item='{self.item_name}', total_cents={self.total_amount_cents})>"