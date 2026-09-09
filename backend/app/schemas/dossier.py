import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DossierPriority, DossierStatus


# =============================================================================
# INSPECTION LINK SCHEMAS
# =============================================================================

class DossierInspectionCreate(BaseModel):
    """Payload to link an existing inspection to an investigation dossier."""
    inspection_id: uuid.UUID
    relevance_notes: Optional[str] = Field(
        None,
        description="Operational context for why this inspection is grouped (non-legal observation)"
    )


class DossierInspectionResponse(BaseModel):
    """Representation of an inspection linked to a dossier."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dossier_id: uuid.UUID
    inspection_id: uuid.UUID
    added_by_id: Optional[uuid.UUID] = None
    relevance_notes: Optional[str] = None
    added_at: datetime

    # Denormalized inspection fields for fast UI rendering
    inspection_number: Optional[str] = None
    inspection_date: Optional[datetime] = None
    store_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    legal_result: Optional[str] = None
    inspection_status: Optional[str] = None
    inspector_name: Optional[str] = None


# =============================================================================
# DOSSIER CRUD SCHEMAS
# =============================================================================

class InvestigationDossierCreate(BaseModel):
    """Payload to create a new market surveillance investigation dossier."""
    title: str = Field(..., min_length=3, max_length=255, description="Operational investigation title")
    dossier_number: Optional[str] = Field(None, max_length=64, description="Optional manual identifier; auto-generated if omitted")
    description: Optional[str] = Field(None, description="Summary of market surveillance scope")
    target_entity_name: Optional[str] = Field(None, max_length=255, description="Raw operational brand/packer/retailer name")
    company_id: Optional[uuid.UUID] = Field(None, description="Explicitly verified corporate entity linkage under Section 49")
    status: Optional[DossierStatus] = Field(default=DossierStatus.ACTIVE, description="Initial workflow status")
    priority: Optional[DossierPriority] = Field(default=DossierPriority.NORMAL, description="Operational priority level")
    tags: Optional[List[str]] = Field(default_factory=list, description="Categorization tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operational metadata")


class InvestigationDossierUpdate(BaseModel):
    """Payload to update an existing investigation dossier."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    target_entity_name: Optional[str] = Field(None, max_length=255)
    company_id: Optional[uuid.UUID] = None
    status: Optional[DossierStatus] = None
    priority: Optional[DossierPriority] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class InvestigationDossierResponse(BaseModel):
    """Summary representation of an investigation dossier."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dossier_number: str
    title: str
    description: Optional[str] = None
    target_entity_name: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    status: DossierStatus
    priority: DossierPriority
    lead_supervisor_id: uuid.UUID
    lead_supervisor_name: Optional[str] = None
    tags: List[str] = []
    linked_inspections_count: int = 0
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class InvestigationDossierDetailResponse(InvestigationDossierResponse):
    """Detailed representation of an investigation dossier including links."""
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    dossier_inspections: List[DossierInspectionResponse] = []
    company_cin: Optional[str] = None


# =============================================================================
# DOSSIER SYNTHESIS SCHEMAS (READ-ONLY FACTUAL AGGREGATION)
# =============================================================================

class DossierSummaryCounts(BaseModel):
    """Factual inspection count aggregation."""
    total_inspections: int = 0
    completed_inspections: int = 0
    review_required_inspections: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    needs_review_count: int = 0
    pending_count: int = 0


class ObservedFindingSummary(BaseModel):
    """Aggregation of existing findings across linked inspections."""
    rule_code: str
    rule_name: str
    affected_inspection_count: int
    severity_levels: List[str] = []
    observation_label: str = "Observed finding pattern"


class RecordedSeizureSummary(BaseModel):
    """Arithmetic aggregation of recorded seizure items."""
    total_seizure_records: int = 0
    total_seized_quantity: float = 0.0
    seizure_items_count: int = 0
    description: str = "Recorded seizure quantity across linked inspection records"


class DossierNominatedDirectorReview(BaseModel):
    """Informational corporate governance reference for supervisor review."""
    director_name: str
    din: str
    designation: str
    form_i_notice_date: Optional[str] = None
    review_note: str = "Associated corporate record available for authorized officer review"


class DossierTimelineEvent(BaseModel):
    """Factual chronological event in the investigation lifecycle."""
    event_type: str
    timestamp: datetime
    description: str
    inspection_id: Optional[uuid.UUID] = None


class DossierSynthesisResponse(BaseModel):
    """
    Complete factual synthesis for an investigation dossier.

    CRITICAL LEGAL INVARIANT:
    This synthesis aggregates existing factual data only. It NEVER creates new statutory
    violations, alters individual inspection legal results, determines director liability,
    or authorizes prosecution/seizure.
    """
    dossier_id: uuid.UUID
    dossier_number: str
    title: str
    status: DossierStatus
    priority: DossierPriority
    target_entity_name: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    company_cin: Optional[str] = None
    lead_supervisor_id: uuid.UUID
    lead_supervisor_name: Optional[str] = None

    summary_counts: DossierSummaryCounts
    locations: List[str] = []
    observed_findings: List[ObservedFindingSummary] = []
    seizure_summary: RecordedSeizureSummary
    batch_count: int = 0
    evidence_completeness_average: float = 0.0
    timeline: List[DossierTimelineEvent] = []
    nominated_directors_review: List[DossierNominatedDirectorReview] = []

    repeat_history_note: str = "Historical non-compliant inspection records associated with the same stored entity name"
    historical_non_compliant_count: int = 0

    advisory_disclaimer: str = (
        "Operational case-management view. Individual inspection legal results remain authoritative. "
        "System-generated synthesis for authorized officer review."
    )

