import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import ReportType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.user import User


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type", native_enum=True),
        default=ReportType.PDF,
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="reports")
    generator: Mapped["User"] = relationship("User", back_populates="reports")

