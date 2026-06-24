from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardBreakdown, DashboardMetrics
from app.services.dashboard import get_breakdown, get_metrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def metrics_route(db: DbSession, _: CurrentUser) -> DashboardMetrics:
    return get_metrics(db)


@router.get("/breakdown", response_model=DashboardBreakdown)
def breakdown_route(db: DbSession, _: CurrentUser) -> DashboardBreakdown:
    return get_breakdown(db)
