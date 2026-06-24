from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.search_job import SearchJobCreate, SearchJobListResponse, SearchJobRead, SearchJobResultRead
from app.services.scraper import GoogleMapsScraper
from app.services.search_jobs import (
    Scraper,
    cancel_search_job,
    create_search_job,
    get_search_job,
    list_search_job_results,
    list_search_jobs,
    run_search_job,
)

router = APIRouter(prefix="/search-jobs", tags=["search-jobs"])


def get_scraper() -> Scraper:
    return GoogleMapsScraper()


@router.post("", response_model=SearchJobRead, status_code=status.HTTP_201_CREATED)
def create_job_route(
    payload: SearchJobCreate,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    scraper: Annotated[Scraper, Depends(get_scraper)],
) -> SearchJobRead:
    job = create_search_job(
        db,
        city=payload.city,
        state=payload.state,
        segment=payload.segment,
        max_results=payload.max_results,
        prioritize_without_site=payload.prioritize_without_site,
        prioritize_with_phone=payload.prioritize_with_phone,
        include_bad_websites=payload.include_bad_websites,
        created_by_user_id=current_user.id,
    )
    background_tasks.add_task(run_search_job, db, job.id, scraper)
    return job


@router.get("", response_model=SearchJobListResponse)
def list_jobs_route(db: DbSession, _: CurrentUser, offset: int = 0, limit: int = 50) -> SearchJobListResponse:
    items, total = list_search_jobs(db, offset=offset, limit=limit)
    return SearchJobListResponse(items=items, total=total)


@router.get("/{job_id}", response_model=SearchJobRead)
def get_job_route(job_id: int, db: DbSession, _: CurrentUser) -> SearchJobRead:
    return get_search_job(db, job_id)


@router.post("/{job_id}/cancel", response_model=SearchJobRead)
def cancel_job_route(job_id: int, db: DbSession, _: CurrentUser) -> SearchJobRead:
    return cancel_search_job(db, job_id)


@router.get("/{job_id}/results", response_model=list[SearchJobResultRead])
def list_results_route(job_id: int, db: DbSession, _: CurrentUser) -> list[SearchJobResultRead]:
    return list_search_job_results(db, job_id)
