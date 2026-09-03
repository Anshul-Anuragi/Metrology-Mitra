import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SampleUnitWeightInput(BaseModel):
    unit_number: int = Field(..., ge=1, description="Sample unit sequence number (e.g. 1, 2, 3...)")
    gross_weight: float = Field(..., gt=0.0, description="Measured gross weight in specified units")
    tare_weight: Optional[float] = Field(None, ge=0.0, description="Measured or tare weight of container")


class SampleUnitWeightResult(BaseModel):
    unit_number: int
    gross_weight: float
    tare_weight: float
    net_weight: float
    error_value: float  # net_weight - nominal_quantity
    error_percent: float  # (error_value / nominal_quantity) * 100
    is_negative_error: bool
    exceeds_mpe: bool  # True if negative error > MPE (tolerable error exceeded)
    exceeds_double_mpe: bool  # True if negative error > 2 * MPE (critical defect)


class GravimetricTestCreate(BaseModel):
    inspection_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    nominal_quantity_value: float = Field(..., gt=0.0, description="Declared nominal net quantity on label (e.g. 500, 1, 5)")
    nominal_quantity_unit: str = Field("g", description="Unit of measurement: g, kg, ml, l")
    declared_tare_weight: float = Field(0.0, ge=0.0, description="Standard container tare weight if uniform across batch")
    samples: List[SampleUnitWeightInput] = Field(..., min_length=1, description="List of sample unit weights")
    lot_size: Optional[int] = Field(None, ge=1, description="Total lot size at inspection venue for Schedule IV sampling table")


class GravimetricTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    nominal_quantity_value: float
    nominal_quantity_unit: str
    declared_tare_weight: float
    mpe_value: float
    mpe_description: Optional[str] = None
    sample_units_data: Optional[List[Dict[str, Any]]] = None
    sample_mean_net_quantity: Optional[float] = None
    sample_std_dev: Optional[float] = None
    defective_units_count: int
    double_mpe_defective_count: int = 0
    lot_decision: str  # PASSED_MPE, FAILED_MEAN_DEFICIT, FAILED_EXCESSIVE_DEFECTIVES, FAILED_CRITICAL_DOUBLE_MPE, INCOMPLETE
    statutory_standard: str
    disclaimer: Optional[str] = None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

