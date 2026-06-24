from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import DigitalPresence, LeadStatus
from app.models.lead import Lead
from app.schemas.dashboard import DashboardBreakdown, DashboardMetrics


def _count(db: Session, *filters) -> int:
    query = select(func.count()).select_from(Lead)
    for item in filters:
        query = query.where(item)
    return db.scalar(query) or 0


def get_metrics(db: Session) -> DashboardMetrics:
    return DashboardMetrics(
        total_leads=_count(db),
        leads_without_site=_count(db, Lead.digital_presence == DigitalPresence.SEM_SITE),
        bad_site_leads=_count(db, Lead.digital_presence == DigitalPresence.SITE_RUIM),
        leads_with_phone=_count(db, Lead.normalized_phone.is_not(None)),
        contacted_leads=_count(db, Lead.current_status == LeadStatus.CONTATADO),
        interested_leads=_count(db, Lead.current_status == LeadStatus.INTERESSADO),
        closed_leads=_count(db, Lead.current_status == LeadStatus.FECHADO),
    )


def _breakdown(db: Session, column) -> dict[str, int]:
    rows = db.execute(select(column, func.count()).group_by(column)).all()
    return {str(key): count for key, count in rows if key is not None}


def get_breakdown(db: Session) -> DashboardBreakdown:
    return DashboardBreakdown(
        by_city=_breakdown(db, Lead.city),
        by_segment=_breakdown(db, Lead.segment),
        by_status=_breakdown(db, Lead.current_status),
    )
