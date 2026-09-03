import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class ImageQualityResponse(BaseModel):
    image_id: uuid.UUID = Field(..., description="Unique ID of the evaluated inspection image")
    width: int = Field(..., description="Native image width in pixels")
    height: int = Field(..., description="Native image height in pixels")
    blur_score: float = Field(..., description="Laplacian variance sharpness metric (higher is sharper)")
    blur_status: str = Field(..., description="PASS | WARNING | FAIL based on focus quality")
    glare_ratio: float = Field(..., description="Ratio of specular saturated pixels (0.0 - 1.0)")
    glare_status: str = Field(..., description="PASS | WARNING | FAIL based on reflection intensity")
    glare_detected: bool = Field(..., description="True if specular glare exceeds warning threshold")
    exposure_mean: Optional[float] = Field(None, description="Average pixel luminance (0-255)")
    exposure_status: Optional[str] = Field("PASS", description="PASS | WARNING based on luminance")
    resolution_status: str = Field(..., description="PASS | WARNING | FAIL based on minimum dimensions")
    gate_decision: str = Field("READY_FOR_ANALYSIS", description="READY_FOR_ANALYSIS | RETAKE_RECOMMENDED | MANUAL_REVIEW")
    overall_status: str = Field(..., description="Advisory quality verdict: PASS | WARNING | FAIL")
    is_acceptable: bool = Field(..., description="Whether the image meets recommended extraction quality")
    guidance_message: str = Field(..., description="Actionable advisory guidance for the field inspector")
    actionable_reasons: List[str] = Field(default_factory=list, description="Specific feedback points")
    sha256_hash: Optional[str] = Field(None, description="Evidence integrity hash of the digital image file")
