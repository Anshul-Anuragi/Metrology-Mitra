import uuid
from typing import Any, Dict, TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Declaration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "declarations"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Statutory fields (stored as extracted text for fidelity, parsed later by rule engine)
    commodity_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    manufacturer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    packer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    importer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_imported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Quantities and Pricing
    net_quantity: Mapped[str | None] = mapped_column(Text, nullable=True)
    mrp: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_sale_price: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dates
    manufacturing_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    packing_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    best_before: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Consumer Grievance / Care Details
    consumer_care: Mapped[str | None] = mapped_column(Text, nullable=True)
    consumer_care_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    consumer_care_phone: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Physical / PDP measurements (for font size & numeral height validation)
    pdp_area_sq_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AI Perception & Human Verification Metadata
    field_confidences: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    raw_extractions: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_human_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Digital Listing & Measurement Integrations (Phase 1.8 & 1.9)
    digital_listing_data: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    measurement_data: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="declaration")
