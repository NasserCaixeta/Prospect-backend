from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import LeadEventType, LeadStatus


class LeadEventCreate(BaseModel):
    event_type: LeadEventType
    note: str | None = None
    new_status: LeadStatus | None = None


class LeadEventRead(BaseModel):
    id: int
    lead_id: int
    event_type: LeadEventType
    old_status: LeadStatus | None
    new_status: LeadStatus | None
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
