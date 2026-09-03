import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GeoValidationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    expected_state: Optional[str] = None
    expected_district: Optional[str] = None


class GeoValidationResponse(BaseModel):
    is_valid_coordinate: bool
    in_bounds: bool
    matched_region: str
    confidence: float
    geofence_status: str  # VALIDATED, OUT_OF_JURISDICTION, UNVERIFIED_COORDINATES
    disclaimer: str = (
        "GPS coordinate verification provides field inspection audit provenance. "
        "Boundaries are validated against official Indian administrative territorial bounds (6°N to 38°N, 68°E to 98°E)."
    )


class OfflineInspectionItem(BaseModel):
    client_temp_id: str = Field(..., description="Client-generated unique draft identifier")
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    created_at_local: Optional[str] = None
    commodity_name: Optional[str] = None
    manufacturer_name: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    package_type: str = "STANDARD"
    review_notes: Optional[str] = None


class OfflineSyncBatchRequest(BaseModel):
    device_id: Optional[str] = None
    offline_inspections: List[OfflineInspectionItem] = Field(..., min_length=1)


class OfflineSyncBatchResponse(BaseModel):
    synced_count: int
    failed_count: int
    synced_records: List[Dict[str, Any]]
    synced_at: datetime

