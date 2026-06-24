import csv
import io
import re
import unicodedata
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import (
    DigitalPresence,
    LeadEventType,
    LeadStatus,
    SearchResultAction,
)
from app.models.lead import Lead
from app.models.lead_event import LeadEvent
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadUpdate
from app.schemas.lead_event import LeadEventCreate
from app.services.scoring import calculate_score


def normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value.strip().lower())


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    return digits or None


def _has_incomplete_data(lead: Lead) -> bool:
    return not bool(lead.phone and lead.city)


def _apply_score(lead: Lead) -> None:
    score, level = calculate_score(
        phone=lead.phone,
        digital_presence=lead.digital_presence,
        segment=lead.segment,
        review_count=lead.review_count,
        has_incomplete_data=_has_incomplete_data(lead),
    )
    lead.potential_score = score
    lead.potential_level = level


def _find_duplicate(db: Session, data: dict[str, Any]) -> Lead | None:
    google_maps_url = data.get("google_maps_url")
    if google_maps_url:
        existing = db.scalar(select(Lead).where(Lead.google_maps_url == google_maps_url))
        if existing:
            return existing
    normalized_name = normalize_text(data.get("name"))
    city = data.get("city")
    normalized_phone = normalize_phone(data.get("phone"))
    if normalized_name and city and normalized_phone:
        return db.scalar(
            select(Lead).where(
                Lead.normalized_name == normalized_name,
                Lead.city == city,
                Lead.normalized_phone == normalized_phone,
            )
        )
    return None


def create_manual_lead(db: Session, payload: LeadCreate) -> Lead:
    data = payload.model_dump()
    existing = _find_duplicate(db, data)
    if existing:
        return existing
    lead = Lead(
        **data,
        normalized_name=normalize_text(payload.name) or payload.name.lower(),
        normalized_phone=normalize_phone(payload.phone),
    )
    if not lead.website_url:
        lead.digital_presence = DigitalPresence.SEM_SITE
    _apply_score(lead)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def upsert_scraped_lead(db: Session, data: dict[str, Any]) -> tuple[Lead, str]:
    if not data.get("name") or not data.get("google_maps_url"):
        raise ValueError("Scraped lead requires name and google_maps_url")
    existing = _find_duplicate(db, data)
    if existing:
        for field in (
            "phone",
            "city",
            "state",
            "segment",
            "category",
            "address",
            "website_url",
            "google_maps_url",
            "rating",
            "review_count",
        ):
            value = data.get(field)
            if value and not getattr(existing, field):
                setattr(existing, field, value)
        existing.normalized_phone = existing.normalized_phone or normalize_phone(existing.phone)
        if existing.digital_presence == DigitalPresence.SITE_DESCONHECIDO and not existing.website_url:
            existing.digital_presence = DigitalPresence.SEM_SITE
        _apply_score(existing)
        db.commit()
        db.refresh(existing)
        return existing, SearchResultAction.UPDATED.value
    lead = Lead(
        name=data["name"],
        normalized_name=normalize_text(data["name"]) or data["name"].lower(),
        phone=data.get("phone"),
        normalized_phone=normalize_phone(data.get("phone")),
        city=data.get("city"),
        state=data.get("state"),
        segment=data.get("segment"),
        category=data.get("category"),
        address=data.get("address"),
        website_url=data.get("website_url"),
        google_maps_url=data.get("google_maps_url"),
        rating=data.get("rating"),
        review_count=data.get("review_count"),
        digital_presence=DigitalPresence.SITE_DESCONHECIDO
        if data.get("website_url")
        else DigitalPresence.SEM_SITE,
    )
    _apply_score(lead)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead, SearchResultAction.CREATED.value


def get_lead(db: Session, lead_id: int) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


def list_leads(
    db: Session,
    *,
    city: str | None = None,
    segment: str | None = None,
    current_status: LeadStatus | None = None,
    with_phone: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Lead], int]:
    query = select(Lead)
    count_query = select(func.count()).select_from(Lead)
    filters = []
    if city:
        filters.append(Lead.city == city)
    if segment:
        filters.append(Lead.segment == segment)
    if current_status:
        filters.append(Lead.current_status == current_status)
    if with_phone is True:
        filters.append(Lead.normalized_phone.is_not(None))
    if with_phone is False:
        filters.append(Lead.normalized_phone.is_(None))
    for item in filters:
        query = query.where(item)
        count_query = count_query.where(item)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.order_by(Lead.potential_score.desc(), Lead.id).offset(offset).limit(limit)))
    return items, total


def update_lead(db: Session, lead_id: int, payload: LeadUpdate, user: User) -> Lead:
    lead = get_lead(db, lead_id)
    old_status = lead.current_status
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(lead, field, value)
    if "name" in data:
        lead.normalized_name = normalize_text(lead.name) or lead.name.lower()
    if "phone" in data:
        lead.normalized_phone = normalize_phone(lead.phone)
    _apply_score(lead)
    if "current_status" in data and lead.current_status != old_status:
        db.add(
            LeadEvent(
                lead_id=lead.id,
                created_by_user_id=user.id,
                event_type=LeadEventType.STATUS_CHANGE,
                old_status=old_status,
                new_status=lead.current_status,
            )
        )
    db.commit()
    db.refresh(lead)
    return lead


def create_lead_event(
    db: Session,
    *,
    lead_id: int,
    payload: LeadEventCreate,
    user: User,
) -> LeadEvent:
    lead = get_lead(db, lead_id)
    old_status = lead.current_status
    if payload.new_status:
        lead.current_status = payload.new_status
    event = LeadEvent(
        lead_id=lead.id,
        created_by_user_id=user.id,
        event_type=payload.event_type,
        old_status=old_status if payload.new_status else None,
        new_status=payload.new_status,
        note=payload.note,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_lead_events(db: Session, lead_id: int) -> list[LeadEvent]:
    get_lead(db, lead_id)
    return list(db.scalars(select(LeadEvent).where(LeadEvent.lead_id == lead_id).order_by(LeadEvent.id)))


def export_leads_csv(db: Session) -> str:
    leads = db.scalars(select(Lead).order_by(Lead.id))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "city", "phone", "website_url", "google_maps_url", "status"])
    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.name,
                lead.city,
                lead.phone,
                lead.website_url,
                lead.google_maps_url,
                lead.current_status,
            ]
        )
    return output.getvalue()
