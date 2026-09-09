import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DossierPriority, DossierStatus
from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.inspection import Inspection
    from app.models.user import User


class InvestigationDossier(Base, UUIDPrimaryKeyMixin):
    """
    Market Surveillance Investigation Dossier.
    Operational case-management container grouping multiple inspection records
    for supervisory review, factual synthesis, and case intelligence.

    CRITICAL LEGAL INVARIANT:
    This model represents an operational case container and NEVER:
    1. Determines statutory legal compliance (that remains the sole authority of the deterministic Legal Rule Engine)
    2. Modifies or overrides individual inspection compliance results
    3. Declares collective guilt or director liability
    4. Authorizes or executes enforcement actions
    """
    __tablename__ = "investigation_dossiers"

    dossier_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_entity_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[DossierStatus] = mapped_column(
        SQLEnum(DossierStatus, name="dossier_status", create_type=False),
        default=DossierStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    priority: Mapped[DossierPriority] = mapped_column(
        SQLEnum(DossierPriority, name="dossier_priority", create_type=False),
        default=DossierPriority.NORMAL,
        nullable=False,
    )
    lead_supervisor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tags: Mapped[List[str]] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="dossiers", lazy="selectin"
    )
    lead_supervisor: Mapped["User"] = relationship(
        "User", foreign_keys=[lead_supervisor_id], back_populates="managed_dossiers", lazy="selectin"
    )
    dossier_inspections: Mapped[List["DossierInspection"]] = relationship(
        "DossierInspection",
        back_populates="dossier",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DossierInspection.added_at.asc()",
    )

    @property
    def inspections(self) -> List["DossierInspection"]:
        return self.dossier_inspections


class DossierInspection(Base, UUIDPrimaryKeyMixin):
    """
    Many-to-many link between an Investigation Dossier and an Inspection record.
    Provides operational relevance notes and tracking without mutating the underlying inspection.
    """
    __tablename__ = "dossier_inspections"

    dossier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigation_dossiers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    relevance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    dossier: Mapped["InvestigationDossier"] = relationship(
        "InvestigationDossier", back_populates="dossier_inspections", lazy="selectin"
    )
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="dossier_links", lazy="selectin"
    )
    added_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("dossier_id", "inspection_id", name="uq_dossier_inspection"),
    )

