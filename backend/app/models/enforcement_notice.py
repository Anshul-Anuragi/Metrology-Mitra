import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class EnforcementNotice(Base):
    __tablename__ = "enforcement_notices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notice_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    notice_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SHOW_CAUSE_NOTICE"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFTED", index=True
    )
    offence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    statutory_sections: Mapped[Optional[dict | list]] = mapped_column(JSONB, nullable=True)
    compounding_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    challan_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    officer_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    compounded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship(
        "Inspection", back_populates="enforcement_notices"
    )

