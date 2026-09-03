import uuid
from typing import Optional
from pydantic import BaseModel, Field


class MeasurementInput(BaseModel):
    pdp_area_cm2: Optional[float] = Field(None, description="Calculated Principal Display Panel area in cm²")
    pixel_height: Optional[float] = Field(None, description="Height of measured numerals in pixels")
    pixel_scale_mm_per_px: Optional[float] = Field(None, description="Calibrated scale factor (mm per pixel)")
    scale_source: Optional[str] = Field("REFERENCE_OBJECT", description="REFERENCE_OBJECT | INSPECTOR_CALIBRATED | UNAVAILABLE")
    scale_confidence: Optional[float] = Field(0.85, description="Confidence of the scale calibration (0.0 - 1.0)")
    is_blown_or_moulded: Optional[bool] = Field(False, description="Whether package is blown/moulded/perforated")


class MeasurementResponse(BaseModel):
    inspection_id: uuid.UUID
    pixel_height: Optional[float]
    physical_height_mm: Optional[float]
    scale_source: str
    scale_confidence: float
    measurement_confidence: float
    threshold_mm: float
    pdp_area_cm2: Optional[float]
    result: str  # PASS, REVIEW
    reason: str
    is_prototype: bool = True
    methodology: str = "Reference-assisted image measurement (Decision-support prototype)"

