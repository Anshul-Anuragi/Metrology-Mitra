import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import CheckResult, EvidenceType, ViolationSeverity, ViolationStatus
from app.schemas.rule import LegalRuleResponse


class EvidenceBase(BaseModel):
    evidence_type: EvidenceType = EvidenceType.BOUNDING_BOX
    description: str | None = None
    bounding_box: Dict[str, Any] | None = None


class EvidenceCreate(EvidenceBase):
    inspection_id: uuid.UUID
    compliance_check_id: uuid.UUID | None = None
    violation_id: uuid.UUID | None = None
    image_id: uuid.UUID | None = None


class EvidenceResponse(EvidenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    compliance_check_id: uuid.UUID | None = None
    violation_id: uuid.UUID | None = None
    image_id: uuid.UUID | None = None
    created_at: datetime


class ViolationBase(BaseModel):
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    title: str
    description: str
    rule_citation: str | None = None
    status: ViolationStatus = ViolationStatus.OPEN


class ViolationCreate(ViolationBase):
    inspection_id: uuid.UUID
    compliance_check_id: uuid.UUID


class ViolationResponse(ViolationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    compliance_check_id: uuid.UUID
    created_at: datetime


class ComplianceCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    legal_rule_id: uuid.UUID
    field_name: str | None = None
    observed_value: str | None = None
    result: CheckResult
    confidence: float | None = None
    reason: str | None = None
    checked_at: datetime
    legal_rule: Optional[LegalRuleResponse] = None
