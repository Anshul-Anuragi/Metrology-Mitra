import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import CheckResult
from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.inspection import Inspection
    from app.models.legal_rule import LegalRule
    from app.models.violation import Violation


class ComplianceCheck(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "compliance_checks"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    legal_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[CheckResult] = mapped_column(
        Enum(CheckResult, name="check_result", native_enum=True),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="compliance_checks")
    legal_rule: Mapped["LegalRule"] = relationship("LegalRule", back_populates="compliance_checks")
    violations: Mapped[list["Violation"]] = relationship(
        "Violation", back_populates="compliance_check", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="compliance_check"
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="check_compliance_confidence_range",
        ),
    )

