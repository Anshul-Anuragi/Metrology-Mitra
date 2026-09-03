import uuid
from typing import Any, Dict, TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import ImageType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.inspection import Inspection
    from app.models.ocr_result import OCRResult


class InspectionImage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inspection_images"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_type: Mapped[ImageType] = mapped_column(
        Enum(ImageType, name="image_type", native_enum=True),
        default=ImageType.OTHER,
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Digital File Integrity & Quality Gate (Phase 1.8)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_gate_result: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="images")
    ocr_result: Mapped["OCRResult | None"] = relationship(
        "OCRResult", back_populates="image", uselist=False, cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="image")

    __table_args__ = (
        UniqueConstraint("inspection_id", "sequence_number", name="unique_inspection_sequence"),
    )
