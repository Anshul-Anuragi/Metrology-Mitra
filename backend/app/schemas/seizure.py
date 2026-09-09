import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SeizureItemCreate(BaseModel):
    commodity_name: str = Field(..., description="Name of seized packaged commodity")
    brand_name: Optional[str] = Field(None, description="Brand name if printed")
    batch_lot_number: Optional[str] = Field(None, description="Batch or lot code on seized packages")
    declared_net_quantity: Optional[str] = Field(None, description="Declared net quantity on label")
    total_packages_seized: int = Field(..., ge=1, description="Total count of non-compliant packages seized")
    sample_packages_taken: int = Field(0, ge=0, description="Number of sample packages drawn for laboratory testing")
    sample_seal_tag_number: Optional[str] = Field(None, description="Official seal tag number affixed to drawn test samples")
    mrp: Optional[str] = Field(None, description="Declared MRP on package")


class SeizureItemResponse(SeizureItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seizure_id: uuid.UUID


class WitnessData(BaseModel):
    name: str = Field(..., description="Full legal name of independent witness / pancha")
    address: str = Field(..., description="Residential address of witness")
    phone: Optional[str] = Field(None, description="Contact telephone number")


class SeizureRecordCreate(BaseModel):
    inspection_id: Optional[uuid.UUID] = Field(None, description="Linked inspection ID if originating from inspection")
    batch_id: Optional[uuid.UUID] = Field(None, description="Linked batch ID if originating from wholesale batch lot")
    premises_name: str = Field(..., description="Establishment / warehouse name where seizure took place")
    premises_address: str = Field(..., description="Physical address of inspection premises")
    seizure_date: Optional[datetime] = Field(None, description="Date and time of seizure execution")
    statutory_grounds: str = Field(
        "Non-compliance with mandatory declarations under Rule 6 and Section 15(1)(b) of Legal Metrology Act, 2009",
        description="Statutory legal basis for seizure",
    )
    witness_1: WitnessData = Field(..., description="First independent witness (mandatory under Section 15)")
    witness_2: WitnessData = Field(..., description="Second independent witness (mandatory under Section 15)")
    custody_location: str = Field(
        "Department of Legal Metrology Safe Custody Room",
        description="Physical location where seized inventory is stored under custody",
    )
    items: List[SeizureItemCreate] = Field(..., min_length=1, description="Itemized inventory of seized commodities")
    officer_remarks: Optional[str] = Field(None, description="Notes and observation of seizing officer")


class SeizureRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seizure_memo_number: str
    inspection_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    premises_name: str
    premises_address: str
    seizure_date: datetime
    statutory_grounds: str
    inspecting_officer_id: uuid.UUID
    witness_1_name: str
    witness_1_address: str
    witness_1_phone: Optional[str] = None
    witness_2_name: str
    witness_2_address: str
    witness_2_phone: Optional[str] = None
    custody_location: str
    status: str
    sha256_seal_hash: Optional[str] = None
    officer_remarks: Optional[str] = None
    items: List[SeizureItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    disclaimer: str = (
        "Statutory Seizure Record / Panchnama executed under Section 15 of Legal Metrology Act, 2009 and Rule 29. "
        "Generated documents remain draft administrative seizure memorandums subject to formal magisterial / judicial procedure."
    )

