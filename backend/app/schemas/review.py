import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import ComplianceResult, InspectionStatus
from app.schemas.declaration import DeclarationResponse
from app.schemas.inspection import InspectionResponse
from app.schemas.violation import ComplianceCheckResponse, EvidenceResponse, ViolationResponse


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    inspection_id: uuid.UUID
    actor_user_id: Optional[uuid.UUID] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewSubmissionRequest(BaseModel):
    review_action: str = Field(
        ...,
        description="CONFIRM | CORRECT | REQUEST_RETAKE | MARK_UNRESOLVED",
    )
    review_notes: Optional[str] = Field(None, description="Inspector verification notes")
    declaration_overrides: Optional[Dict[str, Any]] = Field(
        None, description="Corrections to declaration fields (e.g. mrp, net_quantity, address)"
    )


class FinalizeInspectionRequest(BaseModel):
    override_result: Optional[ComplianceResult] = Field(
        None, description="Optional manual verdict override by authorized inspector"
    )
    finalization_notes: Optional[str] = Field(
        None, description="Closing statutory remarks or justification for override"
    )


class ReviewWorkspaceResponse(BaseModel):
    inspection_id: uuid.UUID
    status: InspectionStatus
    overall_result: Optional[ComplianceResult]
    review_notes: Optional[str]
    reviewed_at: Optional[datetime]
    finalized_at: Optional[datetime]
    can_finalize: bool
    blocking_reasons: List[str]
    total_checks: int
    passed_checks: int
    failed_checks: int
    review_checks: int
    declaration: Optional[DeclarationResponse]
    checks: List[ComplianceCheckResponse]
    violations: List[ViolationResponse]
    evidence_items: List[EvidenceResponse]
    audit_logs: List[AuditLogResponse]
