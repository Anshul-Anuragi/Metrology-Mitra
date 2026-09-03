import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class GravimetricTest(Base):
    __tablename__ = "gravimetric_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("inspection_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    nominal_quantity_value = Column(Float, nullable=False)
    nominal_quantity_unit = Column(String(20), nullable=False, default="g")
    declared_tare_weight = Column(Float, nullable=False, default=0.0)
    mpe_value = Column(Float, nullable=False, default=0.0)
    sample_units_data = Column(JSONB, nullable=True)
    sample_mean_net_quantity = Column(Float, nullable=True)
    sample_std_dev = Column(Float, nullable=True)
    defective_units_count = Column(Integer, nullable=False, default=0)
    lot_decision = Column(String(50), nullable=False, default="INCOMPLETE")
    statutory_standard = Column(String(255), nullable=False, default="LMPC Rules, 2011 — Schedule IV & Rule 24")
    disclaimer = Column(Text, nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    inspection = relationship("Inspection", back_populates="gravimetric_tests")
    batch = relationship("InspectionBatch", back_populates="gravimetric_tests")
    created_by = relationship("User", back_populates="gravimetric_tests")

