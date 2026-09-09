import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    """
    Corporate entity record for tracking corporate liability under Section 49
    of the Legal Metrology Act, 2009 (Offences by Companies).
    """
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cin: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    registered_office: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    nominated_directors: Mapped[List["NominatedDirector"]] = relationship(
        "NominatedDirector", back_populates="company", cascade="all, delete-orphan", lazy="selectin"
    )
    inspections: Mapped[List["Inspection"]] = relationship("Inspection", back_populates="company")
    dossiers: Mapped[List["InvestigationDossier"]] = relationship(
        "InvestigationDossier", back_populates="company", lazy="selectin"
    )



class NominatedDirector(Base):
    """
    Director nominated under Section 49(2) of the Legal Metrology Act, 2009
    via Form I resolution to be responsible for compliance of packaged commodities.
    """
    __tablename__ = "nominated_directors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    director_name: Mapped[str] = mapped_column(String(255), nullable=False)
    din: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Director Identification Number
    designation: Mapped[str] = mapped_column(String(100), default="Whole-time Director", nullable=False)
    form_i_notice_date: Mapped[date] = mapped_column(Date, nullable=False)  # Date of notice to Controller
    form_i_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship("Company", back_populates="nominated_directors")
