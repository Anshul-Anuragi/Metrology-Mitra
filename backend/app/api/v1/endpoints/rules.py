import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.legal_rule import LegalRule
from app.schemas.pipeline import BenchmarkReportResponse
from app.schemas.rule import LegalRuleCreate, LegalRuleResponse
from app.services.benchmarking import run_benchmark_suite
from app.services.rule_seeder import seed_legal_rules

router = APIRouter()


@router.get("/benchmark", response_model=BenchmarkReportResponse, tags=["Legal Rules & Benchmarking"])
async def get_accuracy_benchmark():
    """
    Executes benchmark accuracy evaluation on validation dataset.
    Returns honest, non-fabricated metrics for precision, recall, F1, and compliance accuracy.
    """
    report = run_benchmark_suite()
    return BenchmarkReportResponse(
        total_samples=report.total_samples,
        field_precision=report.field_precision,
        field_recall=report.field_recall,
        field_f1=report.field_f1,
        compliance_accuracy=report.compliance_accuracy,
        per_field_metrics=report.per_field_metrics,
        detailed_results=report.detailed_results,
    )


@router.get("/", response_model=List[LegalRuleResponse], tags=["Legal Rules"])
async def list_rules(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LegalRule)
    if active_only:
        stmt = stmt.where(LegalRule.is_active == True)  # noqa: E712
    stmt = stmt.order_by(LegalRule.rule_code.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{rule_id}", response_model=LegalRuleResponse, tags=["Legal Rules"])
async def get_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rule = await db.get(LegalRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal rule not found",
        )
    return rule


@router.post("/seed", tags=["Legal Rules"])
async def trigger_rule_seed(db: AsyncSession = Depends(get_db)):
    seeded_count = await seed_legal_rules(db)
    return {
        "success": True,
        "message": f"Successfully processed seed rules. {seeded_count} new rule(s) inserted.",
    }
