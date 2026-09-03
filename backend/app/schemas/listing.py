import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DigitalListingInput(BaseModel):
    title: Optional[str] = Field(None, description="Product listing title on digital marketplace")
    description: Optional[str] = Field(None, description="Product description text")
    price: Optional[float] = Field(None, description="Advertised retail price in INR")
    country_of_origin: Optional[str] = Field(None, description="Country of origin declared on marketplace")
    net_quantity: Optional[str] = Field(None, description="Declared net quantity on marketplace listing")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer/packer entity name declared")
    listing_url: Optional[str] = Field(None, description="URL or source of the e-commerce listing")


class DigitalListingItemResponse(BaseModel):
    field: str
    listing_value: Optional[str]
    package_value: Optional[str]
    status: str  # MATCH, DISCREPANCY, PARTIAL
    finding: str
    result: str  # PASS, REVIEW


class DigitalListingCrossCheckResponse(BaseModel):
    inspection_id: uuid.UUID
    has_contradictions: bool
    summary_verdict: str  # PASS, REVIEW
    summary_reason: str
    items: List[DigitalListingItemResponse]
    listing_data: Dict[str, Any]

