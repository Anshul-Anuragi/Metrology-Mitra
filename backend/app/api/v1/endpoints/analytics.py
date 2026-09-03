from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import require_supervisor
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsFailingRulesResponse,
    AnalyticsHeatmapsResponse,
    AnalyticsOverviewResponse,
    AnalyticsRepeatOffendersResponse,
    AnalyticsTrendsResponse,
)
from app.services.analytics_service import (
    get_compliance_trends,
    get_failing_rules_breakdown,
    get_geographic_heatmaps,
    get_overview_kpis,
    get_recurring_non_compliance,
)

router = APIRouter()


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get high-level compliance and enforcement KPIs",
    tags=["Supervisor Analytics"],
)
async def get_analytics_overview(
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes overall inspection volume, compliance rate, active violations, and inspector counts.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    return await get_overview_kpis(db)


@router.get(
    "/trends",
    response_model=AnalyticsTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get temporal compliance and violation trends",
    tags=["Supervisor Analytics"],
)
async def get_analytics_trends(
    period: str = Query(
        "monthly",
        pattern="^(monthly|weekly|daily)$",
        description="Aggregation time interval ('monthly', 'weekly', 'daily')",
    ),
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes time-series inspection compliance and violation metrics.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    return await get_compliance_trends(db, period=period)


@router.get(
    "/heatmaps",
    response_model=AnalyticsHeatmapsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get geographic state and district violation heatmaps",
    tags=["Supervisor Analytics"],
)
async def get_analytics_heatmaps(
    state: Optional[str] = Query(None, description="Optional state filter (e.g. DL, MH, KA)"),
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes regional violation densities, non-compliance rates, and cluster coordinates.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    return await get_geographic_heatmaps(db, state_filter=state)


@router.get(
    "/repeat-offenders",
    response_model=AnalyticsRepeatOffendersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recurring non-compliance and violation patterns by entity",
    tags=["Supervisor Analytics"],
)
async def get_analytics_repeat_offenders(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of entities to return (1-100)"),
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Ranks manufacturers/packers with recurring non-compliance and common failed rule codes.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    return await get_recurring_non_compliance(db, limit=limit)


@router.get(
    "/failing-rules",
    response_model=AnalyticsFailingRulesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get distribution and frequency of failed statutory rules",
    tags=["Supervisor Analytics"],
)
async def get_analytics_failing_rules(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of rules to return (1-50)"),
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes failure distribution across statutory LMPC rules.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    return await get_failing_rules_breakdown(db, limit=limit)

