from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SiteAnalysisStatus


class SiteAnalysis(Base):
    __tablename__ = "site_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[SiteAnalysisStatus] = mapped_column(Enum(SiteAnalysisStatus), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    analysis_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    manual_override_status: Mapped[SiteAnalysisStatus | None] = mapped_column(
        Enum(SiteAnalysisStatus)
    )
    manual_override_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead = relationship("Lead", back_populates="site_analyses")
