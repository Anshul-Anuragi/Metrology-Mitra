import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PackerRegistration(Base):
    """
    Authoritative local registry of pre-packers, manufacturers, and importers
    registered under Rule 27 of the Legal Metrology (Packaged Commodities) Rules, 2011.
    """
    __tablename__ = "packer_registrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    registration_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    entity_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    registered_address: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction_level: Mapped[str] = mapped_column(
        String(50), default="CENTRAL_DIRECTOR", nullable=False
    )  # CENTRAL_DIRECTOR, STATE_CONTROLLER
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    issuing_authority: Mapped[str] = mapped_column(
        String(255), default="Director of Legal Metrology, GoI", nullable=False
    )
    registered_categories: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    certificate_sha256: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
