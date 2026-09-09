import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.enums import CheckResult, ComplianceResult, InspectionStatus, ViolationSeverity


class EvidenceFacetStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionRecommendationCategory(str, Enum):
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    VERIFICATION = "VERIFICATION"
    LEGAL_WORKFLOW = "LEGAL_WORKFLOW"
    SUPERVISORY_ACTION = "SUPERVISORY_ACTION"


class EvidenceFacet(BaseModel):
    name: str = Field(..., description="Human-readable name of the evidentiary facet")
    facet_code: str = Field(..., description="Unique machine-readable facet identifier")
    status: EvidenceFacetStatus = Field(..., description="Completeness state of the facet")
    score: float = Field(..., ge=0.0, le=100.0, description="Score achieved for this facet (0-100)")
    weight: float = Field(..., ge=0.0, description="Relative application workflow weight")
    is_required: bool = Field(..., description="Whether this facet is required for this inspection type")
    is_applicable: bool = Field(..., description="Whether this facet applies to the inspected commodity")
    evidence_present: List[str] = Field(default_factory=list, description="List of observed/present evidence items")
    evidence_missing: List[str] = Field(default_factory=list, description="List of missing evidence items")
    actionable_gap: Optional[str] = Field(None, description="Actionable recommendation to satisfy this facet")


class EvidenceGap(BaseModel):
    code: str = Field(..., description="Unique code for the evidence gap")
    title: str = Field(..., description="Short summary title of the gap")
    description: str = Field(..., description="Detailed description of the missing evidence")
    severity: ViolationSeverity = Field(default=ViolationSeverity.MEDIUM, description="Operational urgency of the gap")
    action: str = Field(..., description="Actionable instruction to resolve the gap")
    facet_code: str = Field(..., description="Associated evidentiary facet code")
    is_blocking: bool = Field(default=False, description="Whether this gap blocks confident finalization")


class EvidenceCompleteness(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Composite Evidence Completeness Index (0-100)")
    status: str = Field(..., description="Overall completeness category: EXCELLENT, ADEQUATE, PARTIAL, INCOMPLETE, EMPTY")
    facets: List[EvidenceFacet] = Field(default_factory=list, description="Six standard evidentiary facets")
    gaps: List[EvidenceGap] = Field(default_factory=list, description="List of detected evidence gaps")
    disclaimer: str = Field(
        default="Evidence Completeness measures the sufficiency of collected inspection data for decision-support. It does NOT represent statutory legal compliance.",
        description="Statutory clarity disclaimer",
    )


class PriorityFactor(BaseModel):
    code: str = Field(..., description="Factor code")
    description: str = Field(..., description="Explanation of how this factor contributed to the priority score")
    points_contributed: float = Field(..., description="Operational priority points assigned")
    severity: str = Field(default="INFO", description="Factor severity classification")


class CasePriority(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Operational Case Priority Score (0-100)")
    level: PriorityLevel = Field(..., description="Priority categorization: LOW, MEDIUM, HIGH, CRITICAL")
    factors: List[PriorityFactor] = Field(default_factory=list, description="Itemized contributing factors")
    summary: str = Field(..., description="High-level operational priority summary")
    disclaimer: str = Field(
        default="Operational prioritization weights. Not statutory thresholds and not legal conclusions.",
        description="Regulatory disclaimer",
    )


class ActionRecommendation(BaseModel):
    code: str = Field(..., description="Unique recommendation code")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed advisory rationale")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Urgency of the recommendation")
    category: ActionRecommendationCategory = Field(..., description="Functional recommendation category")
    is_advisory: bool = Field(default=True, description="Always true; non-binding decision-support guidance")
    related_rule: Optional[str] = Field(None, description="Related statutory rule citation where applicable")
    action_label: str = Field(..., description="Action button or next-step label")


class CaseIntelligenceResponse(BaseModel):
    inspection_id: uuid.UUID
    evidence_completeness: EvidenceCompleteness
    case_priority: CasePriority
    recommendations: List[ActionRecommendation]
    legal_context: Dict[str, Any]
    disclaimer: str = Field(
        default="Advisory decision-support guidance for authorized Legal Metrology Officers. Does not constitute autonomous enforcement or legal advice.",
        description="Mandatory legal-safety disclaimer",
    )


class SupervisorTriageItem(BaseModel):
    inspection_id: uuid.UUID
    created_at: datetime
    store_name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    inspector_name: Optional[str] = None
    inspector_id: Optional[uuid.UUID] = None
    entity_name: Optional[str] = None
    commodity_name: Optional[str] = None
    overall_result: ComplianceResult
    status: InspectionStatus
    evidence_completeness_score: float
    priority_score: float
    priority_level: PriorityLevel
    unresolved_review_count: int
    violation_count: int
    max_violation_severity: Optional[str] = None
    primary_attention_reason: str
    has_repeat_offence_history: bool


class SupervisorTriageResponse(BaseModel):
    total_items: int
    items: List[SupervisorTriageItem]
    priority_counts: Dict[str, int] = Field(default_factory=dict)
    disclaimer: str = Field(
        default="Operational supervisor triage queue. Does not alter underlying statutory inspection determinations.",
        description="Regulatory disclaimer",
    )

