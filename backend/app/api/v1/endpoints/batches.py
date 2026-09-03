import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.enums import UserRole
from app.models.inspection import Inspection
from app.models.inspection_batch import InspectionBatch
from app.models.user import User
from app.schemas.batch import BatchCreate, BatchDetailResponse, BatchResponse, BatchUpdate
from app.schemas.inspection import InspectionResponse
from app.services.batch_service import calculate_schedule_iv_sampling_stats, generate_batch_export_bundle

router = APIRouter()


@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED, tags=["Batch Inspections"])
async def create_inspection_batch(
    batch_in: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    batch = InspectionBatch(
        name=batch_in.name,
        lot_size=batch_in.lot_size,
        sample_size=batch_in.sample_size,
        store_name=batch_in.store_name,
        store_address=batch_in.store_address,
        district=batch_in.district,
        state=batch_in.state,
        created_by_id=current_user.id,
        status="IN_PROGRESS",
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    return batch


@router.get("/", response_model=List[BatchResponse], tags=["Batch Inspections"])
async def list_inspection_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(InspectionBatch)
    if current_user.role == UserRole.INSPECTOR:
        stmt = stmt.where(InspectionBatch.created_by_id == current_user.id)
    if status_filter:
        stmt = stmt.where(InspectionBatch.status == status_filter)

    stmt = stmt.order_by(InspectionBatch.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{batch_id}", response_model=BatchDetailResponse, tags=["Batch Inspections"])
async def get_batch_detail(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(InspectionBatch)
        .where(InspectionBatch.id == batch_id)
        .options(selectinload(InspectionBatch.inspections))
    )
    res = await db.execute(stmt)
    batch = res.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection batch with ID '{batch_id}' not found.",
        )

    if current_user.role == UserRole.INSPECTOR and batch.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: You can only view your own batches.",
        )

    sched_stats = calculate_schedule_iv_sampling_stats(
        batch.lot_size, batch.sample_size, batch.inspections
    )

    insp_responses = [InspectionResponse.model_validate(i) for i in batch.inspections]

    return BatchDetailResponse(
        id=batch.id,
        name=batch.name,
        lot_size=batch.lot_size,
        sample_size=batch.sample_size,
        store_name=batch.store_name,
        store_address=batch.store_address,
        district=batch.district,
        state=batch.state,
        created_by_id=batch.created_by_id,
        status=batch.status,
        summary_stats=sched_stats,
        inspections=insp_responses,
        schedule_iv_compliance=sched_stats,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.post("/{batch_id}/inspections/{inspection_id}", response_model=BatchDetailResponse, tags=["Batch Inspections"])
async def attach_inspection_to_batch(
    batch_id: uuid.UUID,
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(InspectionBatch)
        .where(InspectionBatch.id == batch_id)
        .options(selectinload(InspectionBatch.inspections))
    )
    batch = (await db.execute(stmt)).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    insp_stmt = select(Inspection).where(Inspection.id == inspection_id)
    inspection = (await db.execute(insp_stmt)).scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")

    inspection.batch_id = batch.id
    await db.commit()
    await db.refresh(batch)

    sched_stats = calculate_schedule_iv_sampling_stats(
        batch.lot_size, batch.sample_size, batch.inspections
    )
    insp_responses = [InspectionResponse.model_validate(i) for i in batch.inspections]

    return BatchDetailResponse(
        id=batch.id,
        name=batch.name,
        lot_size=batch.lot_size,
        sample_size=batch.sample_size,
        store_name=batch.store_name,
        store_address=batch.store_address,
        district=batch.district,
        state=batch.state,
        created_by_id=batch.created_by_id,
        status=batch.status,
        summary_stats=sched_stats,
        inspections=insp_responses,
        schedule_iv_compliance=sched_stats,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.get("/{batch_id}/export-bundle", tags=["Batch Inspections"])
async def download_batch_export_bundle(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zip_bytes, filename = await generate_batch_export_bundle(db, batch_id, current_user)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

