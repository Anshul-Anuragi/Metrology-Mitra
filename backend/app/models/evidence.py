import uuid
from typing import Any, Dict, TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import EvidenceType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.compliance_check import ComplianceCheck
    from app.models.inspection import Inspection
    from app.models.inspection_image import InspectionImage
    from app.models.violation import Violation


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compliance_check_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_checks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    violation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("violations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspection_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type", native_enum=True),
        default=EvidenceType.BOUNDING_BOX,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="evidence_items")
    compliance_check: Mapped["ComplianceCheck | None"] = relationship(
        "ComplianceCheck", back_populates="evidence_items"
    )
    violation: Mapped["Violation | None"] = relationship("Violation", back_populates="evidence_items")
    image: Mapped["InspectionImage | None"] = relationship("InspectionImage", back_populates="evidence_items")

