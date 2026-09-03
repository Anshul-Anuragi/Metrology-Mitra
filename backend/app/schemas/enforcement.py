import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CompoundingCalculationRequest(BaseModel):
    offence_count: int = Field(1, ge=1, le=10, description="1 for first offence, 2 for second offence, etc.")
    violation_rule_codes: List[str] = Field(default_factory=list, description="Violated rule codes")
    is_repeat_within_three_years: bool = Field(False, description="Whether repeat offence is within 3 years")
    reference_date: Optional[str] = Field(None, description="ISO date for regulatory effective date evaluation (defaults to current date)")


class CompoundingCalculationResponse(BaseModel):
    offence_count: int
    assessment_status: str = Field(..., description="COMPOUNDABLE, NON_COMPOUNDABLE, NEEDS_REVIEW, NOT_DETERMINABLE")
    statutory_section: str
    compounding_amount_reference: Optional[float] = Field(None, description="Prescribed reference statutory ceiling amount under Section 36(1)")
    base_compounding_fee: Optional[float] = Field(None, description="Backward-compatible alias for compounding_amount_reference")
    max_statutory_penalty: Optional[float] = Field(None, description="Maximum statutory penalty ceiling under Section 36")
    is_compoundable: Optional[bool] = Field(None, description="Whether offence is compoundable under Section 48")
    amount_determinable: bool = Field(True, description="False if authoritative statutory data is insufficient or discretionary")
    statutory_citations: List[str]
    source_legislation: str = "Legal Metrology Act, 2009"
    source_version: str = "Act No. 1 of 2010"
    effective_from: str = "2011-04-01"
    effective_to: Optional[str] = None
    legal_rationale: str
    disclaimer: str = (
        "Statutory Assessment & Reference Only. Compounding of offences under Section 48 is discretionary "
        "and subject to final determination and order by the authorized Legal Metrology Officer. "
        "The system does not issue autonomous penalty orders or final compounding amounts."
    )


class EnforcementNoticeCreate(BaseModel):
    inspection_id: uuid.UUID
    notice_type: str = Field("SHOW_CAUSE_NOTICE", description="SHOW_CAUSE_NOTICE, DRAFT_COMPOUNDING_SUMMONS, ADJUDICATION_ORDER")
    offence_count: int = Field(1, ge=1, le=10)
    officer_remarks: Optional[str] = None


class EnforcementNoticeUpdate(BaseModel):
    status: Optional[str] = None
    compounding_amount: Optional[float] = None
    challan_reference: Optional[str] = None
    officer_remarks: Optional[str] = None


class EnforcementNoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    notice_number: str
    notice_type: str
    status: str
    offence_count: int
    statutory_sections: Optional[List[str] | Dict[str, Any]] = None
    compounding_amount: Optional[float] = None
    challan_reference: Optional[str] = None
    officer_remarks: Optional[str] = None
    issued_at: Optional[datetime] = None
    compounded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
