import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.provenance import (
    GeoValidationRequest,
    GeoValidationResponse,
    OfflineSyncBatchRequest,
    OfflineSyncBatchResponse,
)
from app.services.provenance_service import compute_inspection_provenance_hash, verify_geocoordinates
from app.services.rule_engine import evaluate_inspection

router = APIRouter()


@router.post(
    "/geovalidate",
    response_model=GeoValidationResponse,
    tags=["Field Geofence & Provenance"],
)
async def validate_gps_coordinates(
    request: GeoValidationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validates field officer inspection GPS coordinates against Indian administrative bounds.
    """
    return verify_geocoordinates(
        lat=request.latitude,
        lon=request.longitude,
        state=request.expected_state,
        district=request.expected_district,
    )


@router.post(
    "/sync-offline",
    response_model=OfflineSyncBatchResponse,
    tags=["Field Geofence & Provenance"],
)
async def sync_offline_inspections(
    batch_req: OfflineSyncBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests and reconciles offline drafted inspection cases recorded on field devices.
    """
    synced_records = []
    failed_count = 0

    for item in batch_req.offline_inspections:
        try:
            # 1. Geovalidate if coordinates present
            geo_res = verify_geocoordinates(
                lat=item.gps_latitude,
                lon=item.gps_longitude,
                state=item.state,
                district=item.district,
            )

            # 2. Create Inspection
            insp = Inspection(
                inspector_id=current_user.id,
                store_name=item.store_name,
                store_address=item.store_address,
                district=item.district,
                state=item.state,
                gps_latitude=item.gps_latitude,
                gps_longitude=item.gps_longitude,
                geo_verified=geo_res.in_bounds,
                offline_client_id=item.client_temp_id,
                synced_at=datetime.now(timezone.utc),
                review_notes=item.review_notes,
            )
            db.add(insp)
            await db.flush()

            # 3. Create Declaration if declaration fields present
            if item.commodity_name or item.mrp or item.net_quantity or item.manufacturer_name:
                decl = Declaration(
                    inspection_id=insp.id,
                    commodity_name=item.commodity_name,
                    manufacturer_name=item.manufacturer_name,
                    net_quantity=item.net_quantity,
                    mrp=item.mrp,
                    package_type=item.package_type or "STANDARD",
                    is_human_verified=True,  # Inspector manually entered/drafted offline
                )
                db.add(decl)
                await db.flush()

                # Evaluate rules
                await evaluate_inspection(db=db, inspection=insp, declaration=decl)

            synced_records.append({
                "client_temp_id": item.client_temp_id,
                "inspection_id": str(insp.id),
                "status": "SYNCED",
                "geo_verified": geo_res.in_bounds,
                "provenance_hash": compute_inspection_provenance_hash(
                    str(insp.id),
                    str(current_user.id),
                    item.gps_latitude,
                    item.gps_longitude,
                    datetime.now(timezone.utc).isoformat(),
                ),
            })
        except Exception as e:
            failed_count += 1
            synced_records.append({
                "client_temp_id": item.client_temp_id,
                "status": "FAILED",
                "error": str(e),
            })

    await db.commit()

    return OfflineSyncBatchResponse(
        synced_count=len([r for r in synced_records if r.get("status") == "SYNCED"]),
        failed_count=failed_count,
        synced_records=synced_records,
        synced_at=datetime.now(timezone.utc),
    )
