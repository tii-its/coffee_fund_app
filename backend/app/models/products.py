from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    price_cents = Column(Integer, nullable=False)
    icon = Column(String(10), nullable=True, default='☕')
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    consumptions = relationship("Consumption", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price_cents={self.price_cents})>"