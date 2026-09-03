import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import ViolationSeverity, ViolationStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.compliance_check import ComplianceCheck
    from app.models.evidence import Evidence
    from app.models.inspection import Inspection


class Violation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "violations"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compliance_check_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[ViolationSeverity] = mapped_column(
        Enum(ViolationSeverity, name="violation_severity", native_enum=True),
        default=ViolationSeverity.MEDIUM,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_citation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ViolationStatus] = mapped_column(
        Enum(ViolationStatus, name="violation_status", native_enum=True),
        default=ViolationStatus.OPEN,
        nullable=False,
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="violations")
    compliance_check: Mapped["ComplianceCheck"] = relationship("ComplianceCheck", back_populates="violations")
    evidence_items: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="violation", cascade="all, delete-orphan"
    )

