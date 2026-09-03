import uuid
from typing import Any, Dict, List, TYPE_CHECKING
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inspection_image import InspectionImage


class OCRResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ocr_results"

    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspection_images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_data: Mapped[List[Dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    image: Mapped["InspectionImage"] = relationship("InspectionImage", back_populates="ocr_result")

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="check_ocr_confidence_range",
        ),
    )

