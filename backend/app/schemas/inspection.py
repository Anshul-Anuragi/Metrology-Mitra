import uuid
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import ComplianceResult, ImageType, InspectionStatus
from app.schemas.declaration import DeclarationResponse
from app.schemas.product import ProductResponse
from app.schemas.user import UserResponse
from app.schemas.violation import ComplianceCheckResponse, EvidenceResponse, ViolationResponse


class InspectionImageBase(BaseModel):
    image_url: str
    image_type: ImageType = ImageType.OTHER
    sequence_number: int
    resolution_width: int | None = None
    resolution_height: int | None = None
    sha256_hash: str | None = None
    quality_gate_result: Dict[str, Any] | None = None


class InspectionImageCreate(BaseModel):
    image_type: ImageType = ImageType.OTHER
    sequence_number: int | None = None
    resolution_width: int | None = None
    resolution_height: int | None = None


class InspectionImageResponse(InspectionImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    created_at: datetime


class InspectionCreate(BaseModel):
    product_id: uuid.UUID | None = None
    store_name: str | None = None
    store_address: str | None = None
    district: str | None = None
    state: str | None = None
    gps_latitude: float | None = Field(None, ge=-90.0, le=90.0, description="Latitude must be between -90 and 90")
    gps_longitude: float | None = Field(None, ge=-180.0, le=180.0, description="Longitude must be between -180 and 180")


class InspectionStatusUpdate(BaseModel):
    status: InspectionStatus
    overall_result: ComplianceResult | None = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspector_id: uuid.UUID
    product_id: uuid.UUID | None = None
    store_name: str | None = None
    store_address: str | None = None
    district: str | None = None
    state: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    status: InspectionStatus
    overall_result: ComplianceResult | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    review_notes: str | None = None
    reviewed_by_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    finalized_by_id: uuid.UUID | None = None
    finalized_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InspectionDetailResponse(InspectionResponse):
    inspector: UserResponse | None = None
    product: ProductResponse | None = None
    images: List[InspectionImageResponse] = []
    declaration: DeclarationResponse | None = None
    compliance_checks: List[ComplianceCheckResponse] = []
    violations: List[ViolationResponse] = []
    evidence_items: List[EvidenceResponse] = []


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: uuid.UUID
    overall_result: ComplianceResult
    status: InspectionStatus
    total_checks: int
    passed_checks: int
    failed_checks: int
    review_checks: int
    checks: List[ComplianceCheckResponse] = []
