import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.gravimetric_test import GravimetricTest
    from app.models.inspection import Inspection
    from app.models.user import User


class InspectionBatch(Base):
    __tablename__ = "inspection_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    store_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    store_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="IN_PROGRESS", index=True
    )
    summary_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
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
    created_by: Mapped["User"] = relationship("User", back_populates="batches")
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection", back_populates="batch", cascade="all"
    )
    gravimetric_tests: Mapped[List["GravimetricTest"]] = relationship(
        "GravimetricTest", back_populates="batch", cascade="all"
    )

