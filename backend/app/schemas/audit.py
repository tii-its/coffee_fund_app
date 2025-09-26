from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional
from app.schemas.users import UserResponse


class AuditResponse(BaseModel):
    id: UUID
    actor_id: UUID
    action: str
    entity: str
    entity_id: UUID
    meta_json: Optional[Dict[str, Any]] = None
    at: datetime
    actor: UserResponse

    model_config = ConfigDict(from_attributes=True)