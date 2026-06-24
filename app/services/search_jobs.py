from typing import Protocol

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import SearchJobStatus, SearchResultAction
from app.models.search_job import SearchJob, SearchJobResult
from app.services.leads import upsert_scraped_lead


class Scraper(Protocol):
    def search(self, *, city: str, state: str, segment: str, max_results: int) -> list[dict]:
        ...


class EmptyScraper:
    def search(self, *, city: str, state: str, segment: str, max_results: int) -> list[dict]:
        return []


def create_search_job(
    db: Session,
    *,
    city: str,
    state: str,
    segment: str,
    max_results: int,
    created_by_user_id: int,
    prioritize_without_site: bool = False,
    prioritize_with_phone: bool = False,
    include_bad_websites: bool = True,
) -> SearchJob:
    job = SearchJob(
        city=city,
        state=state,
        segment=segment,
        max_results=max_results,
        prioritize_without_site=prioritize_without_site,
        prioritize_with_phone=prioritize_with_phone,
        include_bad_websites=include_bad_websites,
        created_by_user_id=created_by_user_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_search_job(db: Session, job_id: int) -> SearchJob:
    job = db.get(SearchJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search job not found")
    return job


def list_search_jobs(db: Session, *, offset: int = 0, limit: int = 50) -> tuple[list[SearchJob], int]:
    total = db.scalar(select(func.count()).select_from(SearchJob)) or 0
    items = list(db.scalars(select(SearchJob).order_by(SearchJob.id.desc()).offset(offset).limit(limit)))
    return items, total


def list_search_job_results(db: Session, job_id: int) -> list[SearchJobResult]:
    get_search_job(db, job_id)
    return list(
        db.scalars(
            select(SearchJobResult)
            .where(SearchJobResult.search_job_id == job_id)
            .order_by(SearchJobResult.id)
        )
    )


def cancel_search_job(db: Session, job_id: int) -> SearchJob:
    job = get_search_job(db, job_id)
    job.cancel_requested = True
    if job.status in {SearchJobStatus.PENDING, SearchJobStatus.RUNNING}:
        job.status = SearchJobStatus.CANCELED
    db.commit()
    db.refresh(job)
    return job


def record_job_result(
    db: Session,
    *,
    job: SearchJob,
    action: SearchResultAction,
    raw_data: dict | None = None,
    lead_id: int | None = None,
    error_message: str | None = None,
) -> SearchJobResult:
    result = SearchJobResult(
        search_job_id=job.id,
        lead_id=lead_id,
        action=action,
        raw_data=raw_data,
        error_message=error_message,
    )
    db.add(result)
    return result


def run_search_job(db: Session, job_id: int, scraper: Scraper | None = None) -> SearchJob:
    job = get_search_job(db, job_id)
    if job.cancel_requested:
        job.status = SearchJobStatus.CANCELED
        db.commit()
        db.refresh(job)
        return job
    job.status = SearchJobStatus.RUNNING
    db.commit()
    scraper = scraper or EmptyScraper()
    try:
        items = scraper.search(
            city=job.city,
            state=job.state,
            segment=job.segment,
            max_results=job.max_results,
        )
        job.found_count = len(items)
        for index, item in enumerate(items, start=1):
            if job.cancel_requested:
                job.status = SearchJobStatus.CANCELED
                break
            try:
                item = {
                    "city": job.city,
                    "state": job.state,
                    "segment": job.segment,
                    **item,
                }
                lead, action = upsert_scraped_lead(db, item)
                record_job_result(
                    db,
                    job=job,
                    action=SearchResultAction(action),
                    raw_data=item,
                    lead_id=lead.id,
                )
                job.saved_count += 1
            except Exception as exc:
                record_job_result(
                    db,
                    job=job,
                    action=SearchResultAction.FAILED,
                    raw_data=item,
                    error_message=str(exc),
                )
            job.progress = int(index / max(job.max_results, 1) * 100)
        if job.status != SearchJobStatus.CANCELED:
            job.status = SearchJobStatus.COMPLETED
            job.progress = 100
    except Exception as exc:
        job.status = SearchJobStatus.FAILED
        job.error_message = str(exc)
    db.commit()
    db.refresh(job)
    return job
