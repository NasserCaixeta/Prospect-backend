from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SearchJobStatus, SearchResultAction


class SearchJob(Base):
    __tablename__ = "search_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    max_results: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    prioritize_without_site: Mapped[bool] = mapped_column(default=False, nullable=False)
    prioritize_with_phone: Mapped[bool] = mapped_column(default=False, nullable=False)
    include_bad_websites: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[SearchJobStatus] = mapped_column(
        Enum(SearchJobStatus), default=SearchJobStatus.PENDING, nullable=False, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    found_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    cancel_requested: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    created_by = relationship("User")
    results = relationship("SearchJobResult", back_populates="search_job", cascade="all, delete-orphan")


class SearchJobResult(Base):
    __tablename__ = "search_job_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    search_job_id: Mapped[int] = mapped_column(ForeignKey("search_jobs.id"), nullable=False)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"))
    action: Mapped[SearchResultAction] = mapped_column(Enum(SearchResultAction), nullable=False)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    search_job = relationship("SearchJob", back_populates="results")
    lead = relationship("Lead")
