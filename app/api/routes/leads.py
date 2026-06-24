from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.models.enums import LeadStatus
from app.schemas.lead import LeadCreate, LeadListResponse, LeadRead, LeadUpdate
from app.schemas.lead_event import LeadEventCreate, LeadEventRead
from app.services.leads import (
    create_lead_event,
    create_manual_lead,
    export_leads_csv,
    get_lead,
    list_lead_events,
    list_leads,
    update_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads_route(
    db: DbSession,
    _: CurrentUser,
    city: str | None = None,
    segment: str | None = None,
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    with_phone: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> LeadListResponse:
    items, total = list_leads(
        db,
        city=city,
        segment=segment,
        current_status=status_filter,
        with_phone=with_phone,
        offset=offset,
        limit=limit,
    )
    return LeadListResponse(items=items, total=total)


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead_route(payload: LeadCreate, db: DbSession, _: CurrentUser) -> LeadRead:
    return create_manual_lead(db, payload)


@router.get("/export.csv")
def export_csv_route(db: DbSession, _: CurrentUser) -> Response:
    return Response(content=export_leads_csv(db), media_type="text/csv")


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead_route(lead_id: int, db: DbSession, _: CurrentUser) -> LeadRead:
    return get_lead(db, lead_id)


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead_route(
    lead_id: int,
    payload: LeadUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> LeadRead:
    return update_lead(db, lead_id, payload, current_user)


@router.post("/{lead_id}/events", response_model=LeadEventRead, status_code=status.HTTP_201_CREATED)
def create_event_route(
    lead_id: int,
    payload: LeadEventCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> LeadEventRead:
    return create_lead_event(db, lead_id=lead_id, payload=payload, user=current_user)


@router.get("/{lead_id}/events", response_model=list[LeadEventRead])
def list_events_route(lead_id: int, db: DbSession, _: CurrentUser) -> list[LeadEventRead]:
    return list_lead_events(db, lead_id)
