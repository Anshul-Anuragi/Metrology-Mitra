import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.inspection import InspectionResponse


class BatchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Lot/Batch Name")
    lot_size: int = Field(1, ge=1, description="Total lot size at depot/store")
    sample_size: int = Field(1, ge=1, description="Number of sample packages to inspect")
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    summary_stats: Optional[Dict[str, Any]] = None


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    lot_size: int
    sample_size: int
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    created_by_id: uuid.UUID
    status: str
    summary_stats: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class BatchDetailResponse(BatchResponse):
    inspections: List[InspectionResponse] = []
    schedule_iv_compliance: Optional[Dict[str, Any]] = None

