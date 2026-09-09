import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.seizure import SeizureItem, SeizureRecord
from app.models.user import User
from app.schemas.seizure import SeizureRecordCreate, SeizureRecordResponse
from app.services.seizure_service import (
    build_panchnama_pdf,
    compute_seizure_seal_hash,
    generate_seizure_memo_number,
)

router = APIRouter()


@router.post(
    "/",
    response_model=SeizureRecordResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Section 15 Seizures & Panchnama"],
)
async def create_seizure_record(
    data: SeizureRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes and records a formal statutory seizure and Panchnama under Section 15 of Legal Metrology Act, 2009.
    """
    memo_num = generate_seizure_memo_number()
    seizure_dt = data.seizure_date or datetime.now(timezone.utc)
    seal_hash = compute_seizure_seal_hash(
        memo_number=memo_num,
        premises_name=data.premises_name,
        officer_id=str(current_user.id),
        timestamp=seizure_dt.isoformat(),
        item_count=len(data.items),
    )

    record = SeizureRecord(
        seizure_memo_number=memo_num,
        inspection_id=data.inspection_id,
        batch_id=data.batch_id,
        premises_name=data.premises_name.strip(),
        premises_address=data.premises_address.strip(),
        seizure_date=seizure_dt,
        statutory_grounds=data.statutory_grounds.strip(),
        inspecting_officer_id=current_user.id,
        witness_1_name=data.witness_1.name.strip(),
        witness_1_address=data.witness_1.address.strip(),
        witness_1_phone=data.witness_1.phone,
        witness_2_name=data.witness_2.name.strip(),
        witness_2_address=data.witness_2.address.strip(),
        witness_2_phone=data.witness_2.phone,
        custody_location=data.custody_location.strip(),
        status="SEIZED_IN_CUSTODY",
        sha256_seal_hash=seal_hash,
        officer_remarks=data.officer_remarks,
    )
    db.add(record)
    await db.flush()

    for item in data.items:
        s_item = SeizureItem(
            seizure_id=record.id,
            commodity_name=item.commodity_name.strip(),
            brand_name=item.brand_name.strip() if item.brand_name else None,
            batch_lot_number=item.batch_lot_number.strip() if item.batch_lot_number else None,
            declared_net_quantity=item.declared_net_quantity,
            total_packages_seized=item.total_packages_seized,
            sample_packages_taken=item.sample_packages_taken,
            sample_seal_tag_number=item.sample_seal_tag_number,
            mrp=item.mrp,
        )
        db.add(s_item)

    await db.commit()
    await db.refresh(record)
    return record


@router.get(
    "/",
    response_model=List[SeizureRecordResponse],
    tags=["Section 15 Seizures & Panchnama"],
)
async def list_seizure_records(
    inspection_id: Optional[uuid.UUID] = Query(None, description="Filter by linked inspection"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists statutory seizure records with optional filters.
    """
    stmt = select(SeizureRecord).options(selectinload(SeizureRecord.items))
    if inspection_id:
        stmt = stmt.where(SeizureRecord.inspection_id == inspection_id)
    if status_filter:
        stmt = stmt.where(SeizureRecord.status == status_filter)

    stmt = stmt.order_by(SeizureRecord.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/{seizure_id}",
    response_model=SeizureRecordResponse,
    tags=["Section 15 Seizures & Panchnama"],
)
async def get_seizure_record(
    seizure_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a single seizure record with itemized inventory.
    """
    stmt = (
        select(SeizureRecord)
        .where(SeizureRecord.id == seizure_id)
        .options(selectinload(SeizureRecord.items))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seizure record '{seizure_id}' not found.",
        )
    return record


@router.get(
    "/{seizure_id}/panchnama-pdf",
    tags=["Section 15 Seizures & Panchnama"],
)
async def download_panchnama_pdf(
    seizure_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates and downloads official Form VI Seizure Memo / Panchnama PDF.
    """
    stmt = (
        select(SeizureRecord)
        .where(SeizureRecord.id == seizure_id)
        .options(selectinload(SeizureRecord.items))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seizure record '{seizure_id}' not found.",
        )

    pdf_bytes = build_panchnama_pdf(record, current_user)
    filename = f"Panchnama_FormVI_{record.seizure_memo_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

