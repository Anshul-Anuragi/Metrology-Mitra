import hashlib
from typing import Optional, Tuple
from app.schemas.provenance import GeoValidationResponse


def verify_geocoordinates(
    lat: Optional[float],
    lon: Optional[float],
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> GeoValidationResponse:
    """
    Validates field GPS coordinates against official Indian territorial bounds (6°N to 38°N, 68°E to 98°E).
    """
    if lat is None or lon is None:
        return GeoValidationResponse(
            is_valid_coordinate=False,
            in_bounds=False,
            matched_region="UNKNOWN",
            confidence=0.0,
            geofence_status="UNVERIFIED_COORDINATES",
            disclaimer="GPS coordinates missing; field provenance unverified.",
        )

    # Validate within India bounding box
    is_in_india = (6.0 <= lat <= 38.0) and (68.0 <= lon <= 98.0)

    if not is_in_india:
        return GeoValidationResponse(
            is_valid_coordinate=True,
            in_bounds=False,
            matched_region="OUTSIDE_INDIAN_TERRITORY",
            confidence=0.1,
            geofence_status="OUT_OF_JURISDICTION",
            disclaimer="Coordinates fall outside the geographic territory of India.",
        )

    # Region approximation
    region_label = f"{district or ''}, {state or 'India'}".strip(", ") or "India (Valid Coordinates)"

    return GeoValidationResponse(
        is_valid_coordinate=True,
        in_bounds=True,
        matched_region=region_label,
        confidence=0.95,
        geofence_status="VALIDATED",
        disclaimer=f"GPS coordinates ({lat:.4f}°N, {lon:.4f}°E) successfully validated within jurisdiction.",
    )


def compute_inspection_provenance_hash(
    inspection_id: str,
    inspector_id: str,
    lat: Optional[float],
    lon: Optional[float],
    timestamp: str,
) -> str:
    """
    Generates a cryptographic SHA-256 fingerprint anchoring an inspection event
    to its inspector, timestamp, and geolocation.
    """
    raw_payload = f"INSP:{inspection_id}|INSPTR:{inspector_id}|LAT:{lat}|LON:{lon}|TIME:{timestamp}"
    return hashlib.sha256(raw_payload.encode()).hexdigest()

