import uuid
from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class DeclarationBase(BaseModel):
    commodity_name: str | None = None
    manufacturer_name: str | None = None
    packer_name: str | None = None
    importer_name: str | None = None
    address: str | None = None
    country_of_origin: str | None = None
    is_imported: bool = False

    net_quantity: str | None = None
    mrp: str | None = None
    unit_sale_price: str | None = None

    manufacturing_date: str | None = None
    packing_date: str | None = None
    import_date: str | None = None
    expiry_date: str | None = None
    best_before: str | None = None

    consumer_care: str | None = None
    consumer_care_email: str | None = None
    consumer_care_phone: str | None = None

    pdp_area_sq_cm: float | None = None
    field_confidences: Dict[str, Any] | None = None
    raw_extractions: Dict[str, Any] | None = None
    is_human_verified: bool = False

    digital_listing_data: Dict[str, Any] | None = None
    measurement_data: Dict[str, Any] | None = None


class DeclarationCreate(DeclarationBase):
    inspection_id: uuid.UUID


class DeclarationUpdate(BaseModel):
    commodity_name: str | None = None
    manufacturer_name: str | None = None
    packer_name: str | None = None
    importer_name: str | None = None
    address: str | None = None
    country_of_origin: str | None = None
    is_imported: bool | None = None
    net_quantity: str | None = None
    mrp: str | None = None
    unit_sale_price: str | None = None
    manufacturing_date: str | None = None
    packing_date: str | None = None
    expiry_date: str | None = None
    best_before: str | None = None
    consumer_care: str | None = None
    consumer_care_email: str | None = None
    consumer_care_phone: str | None = None
    pdp_area_sq_cm: float | None = None
    field_confidences: Dict[str, Any] | None = None
    raw_extractions: Dict[str, Any] | None = None
    is_human_verified: bool | None = None
    digital_listing_data: Dict[str, Any] | None = None
    measurement_data: Dict[str, Any] | None = None


class DeclarationResponse(DeclarationBase):
    id: uuid.UUID
    inspection_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
