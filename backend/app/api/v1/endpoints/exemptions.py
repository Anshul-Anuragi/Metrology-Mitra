import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.exemption import ExemptionEvaluationRequest, ExemptionEvaluationResponse
from app.services.exemption_service import evaluate_statutory_exemption
from app.services.rule_engine import evaluate_inspection

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=ExemptionEvaluationResponse,
    tags=["Statutory Exemptions & Special Packaging"],
)
async def evaluate_exemption_rules(
    request: ExemptionEvaluationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates statutory exemptions under Rule 26 (<= 10g small packages, agricultural bulk > 50kg, institutional consumer)
    and special packaging rules (Rules 21 & 22).
    """
    return evaluate_statutory_exemption(
        package_type=request.package_type,
        net_quantity_value=request.declared_net_quantity_value,
        net_quantity_unit=request.declared_net_quantity_unit,
        commodity_category=request.commodity_category,
        is_agricultural_farm_produce=request.is_agricultural_farm_produce,
        is_institutional_consumer=request.is_institutional_consumer,
        has_institutional_marking=request.has_institutional_marking,
        is_fast_food_takeout=request.is_fast_food_takeout,
        is_tobacco_product=request.is_tobacco_product,
        multi_piece_count=request.multi_piece_count,
        combination_items=request.combination_items,
    )


@router.post(
    "/apply/{inspection_id}",
    response_model=ExemptionEvaluationResponse,
    tags=["Statutory Exemptions & Special Packaging"],
)
async def apply_exemption_to_inspection(
    inspection_id: uuid.UUID,
    request: ExemptionEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Applies exemption classification to an inspection declaration and re-runs the rule engine.
    """
    stmt = (
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(selectinload(Inspection.declaration))
    )
    res = await db.execute(stmt)
    insp = res.scalar_one_or_none()

    if not insp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found.",
        )

    eval_resp = evaluate_statutory_exemption(
        package_type=request.package_type,
        net_quantity_value=request.declared_net_quantity_value,
        net_quantity_unit=request.declared_net_quantity_unit,
        commodity_category=request.commodity_category,
        is_agricultural_farm_produce=request.is_agricultural_farm_produce,
        is_institutional_consumer=request.is_institutional_consumer,
        has_institutional_marking=request.has_institutional_marking,
        is_fast_food_takeout=request.is_fast_food_takeout,
        is_tobacco_product=request.is_tobacco_product,
        multi_piece_count=request.multi_piece_count,
        combination_items=request.combination_items,
    )

    decl = insp.declaration
    if not decl:
        decl = Declaration(inspection_id=insp.id)
        db.add(decl)

    decl.package_type = eval_resp.package_type
    decl.exemption_applied = eval_resp.exemption_rule if eval_resp.is_exempt else None
    decl.exemption_rationale = eval_resp.rationale
    decl.multi_piece_count = request.multi_piece_count
    decl.combination_items = request.combination_items

    await db.commit()
    await db.refresh(decl)

    # Re-evaluate rules with exemption applied
    await evaluate_inspection(db=db, inspection=insp, declaration=decl)

    return eval_resp
