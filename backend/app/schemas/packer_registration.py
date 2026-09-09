import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PackerRegistrationBase(BaseModel):
    registration_number: str = Field(..., description="Official Rule 27 registration number (e.g. DL-LM-REG-2023-089)")
    entity_name: str = Field(..., description="Name of registered pre-packer/manufacturer/importer")
    registered_address: str = Field(..., description="Premises address registered with Legal Metrology controller/director")
    jurisdiction_level: str = Field("CENTRAL_DIRECTOR", description="CENTRAL_DIRECTOR or STATE_CONTROLLER")
    state: str = Field(..., description="State or Union Territory of registration")
    issuing_authority: str = Field("Director of Legal Metrology, GoI", description="Issuing statutory authority")
    registered_categories: List[str] = Field(default_factory=list, description="List of commodity categories authorized to pack")
    valid_from: date = Field(..., description="Registration effective date")
    valid_to: Optional[date] = Field(None, description="Registration expiry date if applicable")
    is_active: bool = Field(True, description="Whether registration is currently active and not revoked")


class PackerRegistrationCreate(PackerRegistrationBase):
    pass


class PackerRegistrationResponse(PackerRegistrationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    certificate_sha256: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RegistrationVerifyRequest(BaseModel):
    registration_number: Optional[str] = Field(None, description="Rule 27 registration number if printed on package")
    entity_name: Optional[str] = Field(None, description="Manufacturer/packer entity name extracted from label")
    state: Optional[str] = Field(None, description="State of manufacture or inspection venue")
    commodity_category: Optional[str] = Field(None, description="Category of commodity inspected")


class RegistrationVerifyResponse(BaseModel):
    verification_status: str = Field(
        ...,
        description="REGISTERED_VALID, EXPIRED, UNREGISTERED_VIOLATION, ADDRESS_MISMATCH, NEEDS_REVIEW",
    )
    registration_number: Optional[str] = None
    matched_entity_name: Optional[str] = None
    registered_address: Optional[str] = None
    jurisdiction_level: Optional[str] = None
    state: Optional[str] = None
    is_active: bool = False
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_compliant: bool
    statutory_citation: str = "Rule 27, Legal Metrology (Packaged Commodities) Rules, 2011"
    rationale: str
    disclaimer: str = (
        "Statutory pre-packer registry verification under Rule 27 of LMPC Rules, 2011 "
        "(mandating ₹500 fee, application within 90 days of pre-packing/importing, and registration with Director/Controller). "
        "Status reflects local database records and requires physical premises verification during field inspection."
    )

