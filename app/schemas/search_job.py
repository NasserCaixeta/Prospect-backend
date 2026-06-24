from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SearchJobStatus, SearchResultAction
from app.schemas.lead import LeadRead


class SearchJobCreate(BaseModel):
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=2, max_length=2)
    segment: str = Field(min_length=1, max_length=120)
    max_results: int = Field(default=10, ge=1, le=20)
    prioritize_without_site: bool = False
    prioritize_with_phone: bool = False
    include_bad_websites: bool = True


class SearchJobRead(BaseModel):
    id: int
    city: str
    state: str
    segment: str
    max_results: int
    prioritize_without_site: bool
    prioritize_with_phone: bool
    include_bad_websites: bool
    status: SearchJobStatus
    progress: int
    found_count: int
    saved_count: int
    error_message: str | None
    cancel_requested: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchJobResultRead(BaseModel):
    id: int
    action: SearchResultAction
    raw_data: dict | None
    error_message: str | None
    lead: LeadRead | None

    model_config = ConfigDict(from_attributes=True)


class SearchJobListResponse(BaseModel):
    items: list[SearchJobRead]
    total: int
