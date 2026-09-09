import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SeizureRecord(Base):
    """
    Statutory record of search, seizure, and Panchnama executed under Section 15
    of the Legal Metrology Act, 2009 and Rule 29 of LMPC Rules, 2011.
    """
    __tablename__ = "seizure_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    seizure_memo_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    inspection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    premises_name: Mapped[str] = mapped_column(String(255), nullable=False)
    premises_address: Mapped[str] = mapped_column(Text, nullable=False)
    seizure_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    statutory_grounds: Mapped[str] = mapped_column(
        Text, default="Non-compliance with mandatory declarations under Rule 6 and Section 15(1)(b) of Legal Metrology Act, 2009", nullable=False
    )
    inspecting_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # 2 Independent Pancha / Witnesses required by law
    witness_1_name: Mapped[str] = mapped_column(String(255), nullable=False)
    witness_1_address: Mapped[str] = mapped_column(Text, nullable=False)
    witness_1_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    witness_2_name: Mapped[str] = mapped_column(String(255), nullable=False)
    witness_2_address: Mapped[str] = mapped_column(Text, nullable=False)
    witness_2_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    custody_location: Mapped[str] = mapped_column(
        String(255), default="Department of Legal Metrology Safe Custody Room", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="SEIZED_IN_CUSTODY", nullable=False
    )  # SEIZED_IN_CUSTODY, SAMPLES_SENT_FOR_TESTING, RELEASED_BY_COURT, COMPOUNDED_CONFISCATED
    sha256_seal_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    officer_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    items: Mapped[List["SeizureItem"]] = relationship(
        "SeizureItem", back_populates="seizure_record", cascade="all, delete-orphan", lazy="selectin"
    )
    inspecting_officer: Mapped["User"] = relationship("User", foreign_keys=[inspecting_officer_id], lazy="selectin")
    inspection: Mapped[Optional["Inspection"]] = relationship("Inspection", foreign_keys=[inspection_id], back_populates="seizure_records")


class SeizureItem(Base):
    """
    Itemized inventory of commodities seized and test samples drawn during a Section 15 seizure.
    """
    __tablename__ = "seizure_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    seizure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seizure_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commodity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    batch_lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    declared_net_quantity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_packages_seized: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_packages_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_seal_tag_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mrp: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    seizure_record: Mapped["SeizureRecord"] = relationship("SeizureRecord", back_populates="items")
