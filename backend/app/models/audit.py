from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.db.types import UUID, JSON


class Audit(Base):
    __tablename__ = "audit"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(), nullable=False)
    meta_json = Column(JSON(), nullable=True)
    at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    actor = relationship("User", back_populates="audit_entries")

    def __repr__(self):
        return f"<Audit(id={self.id}, actor_id={self.actor_id}, action='{self.action}', entity='{self.entity}', entity_id={self.entity_id})>"