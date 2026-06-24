from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import DigitalPresence, LeadStatus, PotentialLevel


class LeadCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    segment: str | None = None
    category: str | None = None
    address: str | None = None
    website_url: str | None = None
    google_maps_url: str | None = None

    @model_validator(mode="after")
    def require_contact_or_source(self) -> "LeadCreate":
        if not self.phone and not self.website_url and not self.google_maps_url:
            raise ValueError("Lead needs phone, website_url, or google_maps_url")
        return self


class LeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    segment: str | None = None
    category: str | None = None
    address: str | None = None
    website_url: str | None = None
    google_maps_url: str | None = None
    digital_presence: DigitalPresence | None = None
    potential_score: int | None = Field(default=None, ge=0, le=100)
    potential_level: PotentialLevel | None = None
    current_status: LeadStatus | None = None
    assigned_to_user_id: int | None = None


class LeadRead(BaseModel):
    id: int
    name: str
    normalized_name: str
    phone: str | None
    normalized_phone: str | None
    whatsapp_probable: bool
    city: str | None
    state: str | None
    segment: str | None
    category: str | None
    address: str | None
    website_url: str | None
    google_maps_url: str | None
    rating: float | None
    review_count: int | None
    digital_presence: DigitalPresence
    potential_score: int
    potential_level: PotentialLevel
    current_status: LeadStatus
    assigned_to_user_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    items: list[LeadRead]
    total: int
