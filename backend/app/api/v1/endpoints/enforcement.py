import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.enums import ComplianceResult, UserRole
from app.models.compliance_check import ComplianceCheck
from app.models.enforcement_notice import EnforcementNotice
from app.models.inspection import Inspection
from app.models.user import User
from app.models.violation import Violation
from app.schemas.enforcement import (
    CompoundingCalculationRequest,
    CompoundingCalculationResponse,
    EnforcementNoticeCreate,
    EnforcementNoticeResponse,
    EnforcementNoticeUpdate,
)
from app.services.enforcement_service import (
    build_compounding_challan_pdf,
    calculate_statutory_compounding_fee,
)

router = APIRouter()


@router.post(
    "/calculate-compounding",
    response_model=CompoundingCalculationResponse,
    tags=["Enforcement & Compounding"],
)
async def calculate_compounding(
    req: CompoundingCalculationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Computes statutory compounding assessment under Section 48 for Section 36 offences.
    """
    return calculate_statutory_compounding_fee(
        offence_count=req.offence_count,
        is_repeat_within_three_years=req.is_repeat_within_three_years,
        violation_rule_codes=req.violation_rule_codes,
        reference_date_str=req.reference_date,
    )


@router.post(
    "/notices",
    response_model=EnforcementNoticeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Enforcement & Compounding"],
)
async def create_enforcement_notice(
    notice_in: EnforcementNoticeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    insp_stmt = (
        select(Inspection)
        .where(Inspection.id == notice_in.inspection_id)
        .options(selectinload(Inspection.violations))
    )
    res = await db.execute(insp_stmt)
    inspection = res.scalar_one_or_none()

    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{notice_in.inspection_id}' not found.",
        )

    if current_user.role == UserRole.INSPECTOR and inspection.inspector_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: You can only draft notices for your own inspections.",
        )

    # Generate draft notice identifier
    year = datetime.now(timezone.utc).year
    state = (inspection.state or "DL").strip().upper()[:2]
    notice_num = f"DRAFT-NOT/{year}/{state}/{uuid.uuid4().hex[:6].upper()}"

    rule_codes = [v.rule_citation for v in inspection.violations if v.rule_citation] or ["LMPC Rules, 2011"]
    calc = calculate_statutory_compounding_fee(notice_in.offence_count, False, rule_codes)

    notice = EnforcementNotice(
        inspection_id=inspection.id,
        notice_number=notice_num,
        notice_type=notice_in.notice_type,
        status="DRAFTED",
        offence_count=notice_in.offence_count,
        statutory_sections=calc.statutory_citations,
        compounding_amount=calc.compounding_amount_reference,
        officer_remarks=notice_in.officer_remarks,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return notice


@router.get(
    "/notices",
    response_model=List[EnforcementNoticeResponse],
    tags=["Enforcement & Compounding"],
)
async def list_enforcement_notices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EnforcementNotice)
        .join(Inspection, EnforcementNotice.inspection_id == Inspection.id)
    )
    if current_user.role == UserRole.INSPECTOR:
        stmt = stmt.where(Inspection.inspector_id == current_user.id)
    if status_filter:
        stmt = stmt.where(EnforcementNotice.status == status_filter)

    stmt = stmt.order_by(EnforcementNotice.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/notices/{notice_id}",
    response_model=EnforcementNoticeResponse,
    tags=["Enforcement & Compounding"],
)
async def get_enforcement_notice(
    notice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EnforcementNotice).where(EnforcementNotice.id == notice_id)
    res = await db.execute(stmt)
    notice = res.scalar_one_or_none()

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enforcement notice with ID '{notice_id}' not found.",
        )
    return notice


@router.patch(
    "/notices/{notice_id}",
    response_model=EnforcementNoticeResponse,
    tags=["Enforcement & Compounding"],
)
async def update_enforcement_notice(
    notice_id: uuid.UUID,
    notice_in: EnforcementNoticeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EnforcementNotice).where(EnforcementNotice.id == notice_id)
    res = await db.execute(stmt)
    notice = res.scalar_one_or_none()

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enforcement notice with ID '{notice_id}' not found.",
        )

    update_data = notice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notice, field, value)

    if notice.status == "ISSUED" and not notice.issued_at:
        notice.issued_at = datetime.now(timezone.utc)
    elif notice.status == "COMPOUNDED" and not notice.compounded_at:
        notice.compounded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(notice)
    return notice


@router.get(
    "/notices/{notice_id}/challan-pdf",
    tags=["Enforcement & Compounding"],
)
async def download_compounding_challan_pdf(
    notice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EnforcementNotice)
        .where(EnforcementNotice.id == notice_id)
        .options(
            selectinload(EnforcementNotice.inspection).selectinload(Inspection.inspector)
        )
    )
    res = await db.execute(stmt)
    notice = res.scalar_one_or_none()

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enforcement notice '{notice_id}' not found.",
        )

    inspector = notice.inspection.inspector or current_user
    pdf_bytes = build_compounding_challan_pdf(notice, notice.inspection, inspector)

    filename = f"Challan_{notice.notice_number.replace('/', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

