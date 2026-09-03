import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.enums import UserRole
from app.models.gravimetric_test import GravimetricTest
from app.models.user import User
from app.schemas.gravimetric import GravimetricTestCreate, GravimetricTestResponse
from app.services.gravimetric_service import build_gravimetric_test_pdf, evaluate_gravimetric_samples, get_statutory_mpe

router = APIRouter()


@router.post(
    "/tests",
    response_model=GravimetricTestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Physical Metrology & MPE"],
)
async def create_gravimetric_test(
    test_in: GravimetricTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates multi-sample physical scale weights against Rule 24 and Schedule IV Table 2 MPE tolerances.
    """
    samples_raw = [s.model_dump() for s in test_in.samples]
    eval_result = evaluate_gravimetric_samples(
        nominal_quantity=test_in.nominal_quantity_value,
        unit=test_in.nominal_quantity_unit,
        samples_data=samples_raw,
        default_tare=test_in.declared_tare_weight,
        lot_size=test_in.lot_size,
    )

    test = GravimetricTest(
        inspection_id=test_in.inspection_id,
        batch_id=test_in.batch_id,
        nominal_quantity_value=test_in.nominal_quantity_value,
        nominal_quantity_unit=test_in.nominal_quantity_unit,
        declared_tare_weight=test_in.declared_tare_weight,
        mpe_value=eval_result["mpe_value"],
        sample_units_data=eval_result["sample_units_data"],
        sample_mean_net_quantity=eval_result["sample_mean_net_quantity"],
        sample_std_dev=eval_result["sample_std_dev"],
        defective_units_count=eval_result["defective_units_count"],
        lot_decision=eval_result["lot_decision"],
        statutory_standard=eval_result["statutory_standard"],
        disclaimer=eval_result["disclaimer"],
        created_by_id=current_user.id,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    resp_data = GravimetricTestResponse.model_validate(test)
    resp_data.mpe_description = eval_result["mpe_description"]
    resp_data.double_mpe_defective_count = eval_result["double_mpe_defective_count"]
    return resp_data


@router.get(
    "/tests/{test_id}",
    response_model=GravimetricTestResponse,
    tags=["Physical Metrology & MPE"],
)
async def get_gravimetric_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(GravimetricTest).where(GravimetricTest.id == test_id)
    res = await db.execute(stmt)
    test = res.scalar_one_or_none()

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gravimetric test record '{test_id}' not found.",
        )

    _, mpe_desc = get_statutory_mpe(test.nominal_quantity_value, test.nominal_quantity_unit)
    resp_data = GravimetricTestResponse.model_validate(test)
    resp_data.mpe_description = mpe_desc
    return resp_data


@router.get(
    "/tests/{test_id}/pdf",
    tags=["Physical Metrology & MPE"],
)
async def download_gravimetric_test_pdf(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(GravimetricTest).where(GravimetricTest.id == test_id)
    res = await db.execute(stmt)
    test = res.scalar_one_or_none()

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gravimetric test record '{test_id}' not found.",
        )

    pdf_bytes = build_gravimetric_test_pdf(test, current_user)
    filename = f"Gravimetric_Test_{str(test.id)[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

