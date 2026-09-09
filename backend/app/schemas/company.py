import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NominatedDirectorBase(BaseModel):
    director_name: str = Field(..., description="Full legal name of the nominated Director")
    din: str = Field(..., description="Director Identification Number (DIN, 8 digits)")
    designation: str = Field("Whole-time Director", description="Corporate designation")
    form_i_notice_date: date = Field(..., description="Date on which Form I notice of nomination was served to Controller")
    form_i_reference: Optional[str] = Field(None, description="Form I reference or acknowledgement number")
    effective_from: date = Field(..., description="Effective date of Section 49(2) nomination")
    effective_to: Optional[date] = Field(None, description="Nomination cessation date if applicable")
    is_active: bool = Field(True, description="Whether nomination is currently in effect")


class NominatedDirectorCreate(NominatedDirectorBase):
    pass


class NominatedDirectorResponse(NominatedDirectorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CompanyBase(BaseModel):
    cin: str = Field(..., description="Corporate Identification Number (e.g. L15400MH2000PLC123456)")
    company_name: str = Field(..., description="Registered legal name of corporate entity")
    registered_office: str = Field(..., description="Registered corporate office premises address")
    state: str = Field(..., description="State of incorporation / registered office")
    email: Optional[str] = Field(None, description="Corporate legal compliance email")
    phone: Optional[str] = Field(None, description="Corporate contact number")
    is_active: bool = Field(True, description="Whether company is active on MCA records")


class CompanyCreate(CompanyBase):
    nominated_directors: Optional[List[NominatedDirectorCreate]] = Field(default_factory=list)


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nominated_directors: List[NominatedDirectorResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Section49LiabilityAssessment(BaseModel):
    company_id: Optional[uuid.UUID] = None
    company_name: str
    cin: Optional[str] = None
    statutory_basis: str = "Section 49, Legal Metrology Act, 2009 (Offences by Companies)"
    has_nominated_director: bool
    nominated_director: Optional[NominatedDirectorResponse] = None
    liability_determination: str = Field(
        ...,
        description="NOMINATED_DIRECTOR_LIABLE, PERSON_IN_CHARGE_DEFAULT_LIABLE, UNREGISTERED_COMPANY_NEEDS_REVIEW",
    )
    notice_recipient_name: str
    notice_recipient_designation: str
    rationale: str
    disclaimer: str = (
        "Statutory liability assessment under Section 49 of Legal Metrology Act, 2009. "
        "Where a company has nominated a Director under Section 49(2) via Form I, notice lies against such Director. "
        "In the absence of a nominated director, liability defaults to every person in charge under Section 49(1)."
    )

