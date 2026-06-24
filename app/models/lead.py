from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DigitalPresence, LeadStatus, PotentialLevel


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("google_maps_url", name="uq_leads_google_maps_url"),
        UniqueConstraint(
            "normalized_name",
            "city",
            "normalized_phone",
            name="uq_leads_normalized_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(60))
    normalized_phone: Mapped[str | None] = mapped_column(String(40), index=True)
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True)
    segment: Mapped[str | None] = mapped_column(String(120), index=True)
    category: Mapped[str | None] = mapped_column(String(160))
    address: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(String(500))
    google_maps_url: Mapped[str | None] = mapped_column(String(1000), index=True)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    digital_presence: Mapped[DigitalPresence] = mapped_column(
        Enum(DigitalPresence), default=DigitalPresence.SITE_DESCONHECIDO, nullable=False
    )
    potential_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    potential_level: Mapped[PotentialLevel] = mapped_column(
        Enum(PotentialLevel), default=PotentialLevel.BAIXO, nullable=False
    )
    current_status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NOVO, nullable=False, index=True
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assigned_to = relationship("User", back_populates="assigned_leads")
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")
    site_analyses = relationship("SiteAnalysis", back_populates="lead", cascade="all, delete-orphan")

    @property
    def whatsapp_probable(self) -> bool:
        if not self.normalized_phone:
            return False
        digits = self.normalized_phone
        if digits.startswith("55") and len(digits) == 13:
            digits = digits[2:]
        return len(digits) == 11 and digits[2] == "9"
