import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import ComplianceResult, InspectionStatus, ReportType
from app.schemas.declaration import DeclarationResponse
from app.schemas.inspection import InspectionResponse
from app.schemas.violation import ComplianceCheckResponse, EvidenceResponse, ViolationResponse


class ReportCreate(BaseModel):
    report_type: ReportType = ReportType.PDF


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    report_number: str
    report_type: ReportType
    file_url: str
    generated_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class JSONExportBundle(BaseModel):
    export_version: str = "1.0.0"
    document_type: str = "LEGAL_METROLOGY_INSPECTION_RECORD_DRAFT"
    generated_at: datetime
    checksum_sha256: str
    report_number: str
    report_type: ReportType
    inspection: Dict[str, Any]
    inspector: Dict[str, Any]
    declaration: Optional[Dict[str, Any]] = None
    compliance_checks: List[Dict[str, Any]] = []
    violations: List[Dict[str, Any]] = []
    evidence_items: List[Dict[str, Any]] = []
    ocr_results: List[Dict[str, Any]] = []

