import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import ComplianceResult, InspectionStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.compliance_check import ComplianceCheck
    from app.models.declaration import Declaration
    from app.models.enforcement_notice import EnforcementNotice
    from app.models.evidence import Evidence
    from app.models.gravimetric_test import GravimetricTest
    from app.models.inspection_batch import InspectionBatch
    from app.models.inspection_image import InspectionImage
    from app.models.product import Product
    from app.models.report import Report
    from app.models.user import User
    from app.models.violation import Violation
    from app.models.dossier import DossierInspection



class Inspection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inspections"

    inspector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspection_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Location & Enforcement Metadata
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    store_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    gps_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Language / Script perception
    language_detected: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Offline synchronization provenance (Phase 2.5)
    offline_client_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Inspection lifecycle & verdict
    status: Mapped[InspectionStatus] = mapped_column(
        Enum(InspectionStatus, name="inspection_status", native_enum=True),
        default=InspectionStatus.CREATED,
        nullable=False,
        index=True,
    )
    overall_result: Mapped[ComplianceResult | None] = mapped_column(
        Enum(ComplianceResult, name="compliance_result", native_enum=True),
        default=ComplianceResult.PENDING,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Inspector Adjudication & Finalization Tracking
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Corporate & Seizure linkages (Phase 2.7 & 2.8)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    inspector: Mapped["User"] = relationship("User", foreign_keys=[inspector_id], back_populates="inspections", lazy="selectin")

    reviewed_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_id])
    finalized_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[finalized_by_id])
    product: Mapped["Product | None"] = relationship("Product", back_populates="inspections")
    batch: Mapped["InspectionBatch | None"] = relationship("InspectionBatch", back_populates="inspections")
    company: Mapped["Company | None"] = relationship("Company", back_populates="inspections")
    images: Mapped[List["InspectionImage"]] = relationship(
        "InspectionImage", back_populates="inspection", cascade="all, delete-orphan"
    )
    declaration: Mapped["Declaration | None"] = relationship(
        "Declaration", back_populates="inspection", uselist=False, cascade="all, delete-orphan"
    )
    compliance_checks: Mapped[List["ComplianceCheck"]] = relationship(
        "ComplianceCheck", back_populates="inspection", cascade="all, delete-orphan"
    )
    violations: Mapped[List["Violation"]] = relationship(
        "Violation", back_populates="inspection", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="inspection", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="inspection", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="inspection", cascade="all, delete-orphan"
    )
    enforcement_notices: Mapped[List["EnforcementNotice"]] = relationship(
        "EnforcementNotice", back_populates="inspection", cascade="all, delete-orphan"
    )
    gravimetric_tests: Mapped[List["GravimetricTest"]] = relationship(
        "GravimetricTest", back_populates="inspection", cascade="all, delete-orphan"
    )
    seizure_records: Mapped[List["SeizureRecord"]] = relationship(
        "SeizureRecord", back_populates="inspection"
    )
    dossier_links: Mapped[List["DossierInspection"]] = relationship(
        "DossierInspection", back_populates="inspection", cascade="all, delete-orphan", lazy="selectin"
    )



# Composite index for querying inspections by date & status
Index("ix_inspections_status_created_at", Inspection.status, Inspection.created_at.desc())
Index("ix_inspections_state_district", Inspection.state, Inspection.district)
