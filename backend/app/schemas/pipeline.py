import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.core.enums import ComplianceResult, InspectionStatus
from app.schemas.declaration import DeclarationResponse
from app.schemas.violation import ComplianceCheckResponse, EvidenceResponse, ViolationResponse


class PipelineExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: uuid.UUID
    status: InspectionStatus
    overall_result: ComplianceResult
    declaration: DeclarationResponse
    total_checks: int
    passed_checks: int
    failed_checks: int
    review_checks: int
    total_violations: int
    total_evidence_items: int
    checks: List[ComplianceCheckResponse] = []
    violations: List[ViolationResponse] = []
    evidence_items: List[EvidenceResponse] = []


class BenchmarkFieldMetric(BaseModel):
    precision: float
    recall: float
    f1_score: float


class BenchmarkReportResponse(BaseModel):
    total_samples: int
    field_precision: float
    field_recall: float
    field_f1: float
    compliance_accuracy: float
    per_field_metrics: Dict[str, BenchmarkFieldMetric]
    detailed_results: List[Dict[str, Any]]

