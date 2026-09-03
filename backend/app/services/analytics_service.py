from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import case, distinct, func, select, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import CheckResult, ComplianceResult, ViolationSeverity
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.legal_rule import LegalRule
from app.models.product import Product
from app.models.violation import Violation
from app.schemas.analytics import (
    AnalyticsFailingRulesResponse,
    AnalyticsHeatmapsResponse,
    AnalyticsOverviewResponse,
    AnalyticsRepeatOffendersResponse,
    AnalyticsTrendsResponse,
    FailingRuleMetric,
    HeatmapClusterPoint,
    RecurringNonComplianceEntity,
    TrendDataPoint,
)


async def get_overview_kpis(db: AsyncSession) -> AnalyticsOverviewResponse:
    """
    Computes deterministic high-level enforcement KPI aggregates.
    """
    # 1. Inspection Metrics
    insp_stmt = select(
        func.count(Inspection.id).label("total_inspections"),
        func.coalesce(
            func.sum(case((Inspection.overall_result == ComplianceResult.COMPLIANT, 1), else_=0)), 0
        ).label("compliant_count"),
        func.coalesce(
            func.sum(case((Inspection.overall_result == ComplianceResult.NON_COMPLIANT, 1), else_=0)), 0
        ).label("non_compliant_count"),
        func.coalesce(
            func.sum(case((Inspection.overall_result == ComplianceResult.NEEDS_REVIEW, 1), else_=0)), 0
        ).label("needs_review_count"),
        func.coalesce(
            func.sum(case((Inspection.overall_result == ComplianceResult.PENDING, 1), else_=0)), 0
        ).label("pending_count"),
        func.count(distinct(Inspection.inspector_id)).label("active_inspectors"),
    )
    insp_row = (await db.execute(insp_stmt)).one()

    total_inspections = int(insp_row.total_inspections or 0)
    compliant_count = int(insp_row.compliant_count or 0)
    non_compliant_count = int(insp_row.non_compliant_count or 0)
    needs_review_count = int(insp_row.needs_review_count or 0)
    pending_count = int(insp_row.pending_count or 0)
    active_inspectors = int(insp_row.active_inspectors or 0)

    compliance_rate = (
        round((compliant_count / total_inspections) * 100.0, 2)
        if total_inspections > 0
        else 0.0
    )

    # 2. Violation Metrics
    viol_stmt = select(
        func.count(Violation.id).label("total_violations"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Violation.severity.in_(
                            [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("high_critical_violations"),
    )
    viol_row = (await db.execute(viol_stmt)).one()

    total_violations = int(viol_row.total_violations or 0)
    high_critical_violations = int(viol_row.high_critical_violations or 0)

    return AnalyticsOverviewResponse(
        total_inspections=total_inspections,
        compliant_inspections=compliant_count,
        non_compliant_inspections=non_compliant_count,
        needs_review_inspections=needs_review_count,
        pending_inspections=pending_count,
        compliance_rate_percent=compliance_rate,
        total_violations=total_violations,
        high_or_critical_violations=high_critical_violations,
        active_inspecting_officers=active_inspectors,
    )


async def get_compliance_trends(
    db: AsyncSession, period: str = "monthly"
) -> AnalyticsTrendsResponse:
    """
    Computes time-series compliance and violation trends using PostgreSQL date_trunc.
    """
    db_period = "month" if period == "monthly" else ("week" if period == "weekly" else "day")

    period_col = func.date_trunc(db_period, Inspection.created_at)

    # Group inspections by period
    insp_trend_stmt = (
        select(
            period_col.label("period_start"),
            func.count(Inspection.id).label("total_inspections"),
            func.coalesce(
                func.sum(case((Inspection.overall_result == ComplianceResult.COMPLIANT, 1), else_=0)), 0
            ).label("compliant_count"),
            func.coalesce(
                func.sum(case((Inspection.overall_result == ComplianceResult.NON_COMPLIANT, 1), else_=0)), 0
            ).label("non_compliant_count"),
            func.coalesce(
                func.sum(case((Inspection.overall_result == ComplianceResult.NEEDS_REVIEW, 1), else_=0)), 0
            ).label("needs_review_count"),
        )
        .group_by(period_col)
        .order_by(period_col.asc())
    )
    insp_rows = (await db.execute(insp_trend_stmt)).all()

    # Group violations by period
    viol_period_col = func.date_trunc(db_period, Violation.created_at)
    viol_trend_stmt = (
        select(
            viol_period_col.label("period_start"),
            func.count(Violation.id).label("violation_count"),
        )
        .group_by(viol_period_col)
    )
    viol_rows = (await db.execute(viol_trend_stmt)).all()
    viol_map = {row.period_start.isoformat() if row.period_start else "": int(row.violation_count) for row in viol_rows}

    data_points: List[TrendDataPoint] = []
    for row in insp_rows:
        p_str = row.period_start.strftime("%Y-%m-%d") if row.period_start else "N/A"
        full_iso = row.period_start.isoformat() if row.period_start else ""
        v_count = viol_map.get(full_iso, 0)

        data_points.append(
            TrendDataPoint(
                period_start=p_str,
                total_inspections=int(row.total_inspections or 0),
                compliant_count=int(row.compliant_count or 0),
                non_compliant_count=int(row.non_compliant_count or 0),
                needs_review_count=int(row.needs_review_count or 0),
                violation_count=v_count,
            )
        )

    return AnalyticsTrendsResponse(period=period, data_points=data_points)


async def get_geographic_heatmaps(
    db: AsyncSession, state_filter: Optional[str] = None
) -> AnalyticsHeatmapsResponse:
    """
    Groups inspections and violations geographically by state and district.
    """
    stmt = select(
        func.coalesce(Inspection.state, "Unspecified State").label("state"),
        func.coalesce(Inspection.district, "Unspecified District").label("district"),
        func.count(Inspection.id).label("inspection_count"),
        func.coalesce(
            func.sum(case((Inspection.overall_result == ComplianceResult.NON_COMPLIANT, 1), else_=0)), 0
        ).label("non_compliant_count"),
        func.avg(Inspection.gps_latitude).label("avg_lat"),
        func.avg(Inspection.gps_longitude).label("avg_lng"),
    ).group_by(Inspection.state, Inspection.district)

    if state_filter:
        stmt = stmt.where(func.lower(Inspection.state) == state_filter.strip().lower())

    stmt = stmt.order_by(func.coalesce(Inspection.state, "Unspecified State").asc(), func.coalesce(Inspection.district, "Unspecified District").asc())
    rows = (await db.execute(stmt)).all()

    # Get violation count per state/district
    viol_geo_stmt = (
        select(
            func.coalesce(Inspection.state, "Unspecified State").label("state"),
            func.coalesce(Inspection.district, "Unspecified District").label("district"),
            func.count(Violation.id).label("violation_count"),
        )
        .join(Inspection, Violation.inspection_id == Inspection.id)
        .group_by(Inspection.state, Inspection.district)
    )
    if state_filter:
        viol_geo_stmt = viol_geo_stmt.where(func.lower(Inspection.state) == state_filter.strip().lower())

    viol_geo_rows = (await db.execute(viol_geo_stmt)).all()
    viol_geo_map = {(r.state, r.district): int(r.violation_count) for r in viol_geo_rows}

    clusters: List[HeatmapClusterPoint] = []
    for r in rows:
        insp_cnt = int(r.inspection_count or 0)
        non_comp_cnt = int(r.non_compliant_count or 0)
        v_cnt = viol_geo_map.get((r.state, r.district), 0)

        rate = (
            round((non_comp_cnt / insp_cnt) * 100.0, 2)
            if insp_cnt > 0
            else 0.0
        )

        avg_lat = float(r.avg_lat) if r.avg_lat is not None else None
        avg_lng = float(r.avg_lng) if r.avg_lng is not None else None
        has_gps = avg_lat is not None and avg_lng is not None

        clusters.append(
            HeatmapClusterPoint(
                state=r.state,
                district=r.district,
                inspection_count=insp_cnt,
                violation_count=v_cnt,
                non_compliant_count=non_comp_cnt,
                non_compliance_rate_percent=rate,
                latitude=avg_lat,
                longitude=avg_lng,
                has_gps_coordinates=has_gps,
            )
        )

    return AnalyticsHeatmapsResponse(total_regions=len(clusters), clusters=clusters)


async def get_recurring_non_compliance(
    db: AsyncSession, limit: int = 10
) -> AnalyticsRepeatOffendersResponse:
    """
    Identifies manufacturers/brands with repeat non-compliance and violation patterns.
    """
    stmt = (
        select(
            func.coalesce(
                Declaration.manufacturer_name,
                Declaration.packer_name,
                Declaration.importer_name,
                Product.manufacturer_name,
                Product.brand_name,
                "Unspecified Entity",
            ).label("entity_name"),
            func.count(distinct(Inspection.id)).label("inspection_count"),
            func.coalesce(
                func.count(
                    distinct(
                        case((Inspection.overall_result == ComplianceResult.NON_COMPLIANT, Inspection.id), else_=None)
                    )
                ),
                0,
            ).label("non_compliant_inspection_count"),
            func.count(Violation.id).label("violation_count"),
        )
        .select_from(Inspection)
        .outerjoin(Declaration, Inspection.id == Declaration.inspection_id)
        .outerjoin(Product, Inspection.product_id == Product.id)
        .outerjoin(Violation, Inspection.id == Violation.inspection_id)
        .group_by(
            Declaration.manufacturer_name,
            Declaration.packer_name,
            Declaration.importer_name,
            Product.manufacturer_name,
            Product.brand_name,
        )
        .having(func.count(distinct(Inspection.id)) > 0)
        .order_by(
            func.count(Violation.id).desc(),
            func.count(
                distinct(
                    case((Inspection.overall_result == ComplianceResult.NON_COMPLIANT, Inspection.id), else_=None)
                )
            ).desc(),
            func.count(distinct(Inspection.id)).desc(),
        )
        .limit(limit)
    )

    rows = (await db.execute(stmt)).all()

    entities: List[RecurringNonComplianceEntity] = []
    for r in rows:
        name = str(r.entity_name)
        insp_cnt = int(r.inspection_count or 0)
        non_comp_cnt = int(r.non_compliant_inspection_count or 0)
        viol_cnt = int(r.violation_count or 0)

        rate = (
            round((non_comp_cnt / insp_cnt) * 100.0, 2)
            if insp_cnt > 0
            else 0.0
        )

        # Get top failed rule codes for this entity
        entity_match = func.coalesce(
            Declaration.manufacturer_name,
            Declaration.packer_name,
            Declaration.importer_name,
            Product.manufacturer_name,
            Product.brand_name,
            "Unspecified Entity",
        )
        failed_rules_stmt = (
            select(
                LegalRule.rule_code,
                func.count(ComplianceCheck.id).label("fails"),
            )
            .select_from(ComplianceCheck)
            .join(Inspection, ComplianceCheck.inspection_id == Inspection.id)
            .outerjoin(Declaration, Inspection.id == Declaration.inspection_id)
            .outerjoin(Product, Inspection.product_id == Product.id)
            .join(LegalRule, ComplianceCheck.legal_rule_id == LegalRule.id)
            .where(
                ComplianceCheck.result == CheckResult.FAIL,
                entity_match == name,
            )
            .group_by(LegalRule.rule_code)
            .order_by(func.count(ComplianceCheck.id).desc())
            .limit(5)
        )
        rule_rows = (await db.execute(failed_rules_stmt)).all()
        top_rule_codes = [str(rr.rule_code) for rr in rule_rows]

        entities.append(
            RecurringNonComplianceEntity(
                entity_name=name,
                entity_type="MANUFACTURER",
                inspection_count=insp_cnt,
                violation_count=viol_cnt,
                non_compliant_inspection_count=non_comp_cnt,
                recurrence_rate_percent=rate,
                common_failed_rule_codes=top_rule_codes,
            )
        )

    return AnalyticsRepeatOffendersResponse(
        total_entities_tracked=len(entities), entities=entities
    )


async def get_failing_rules_breakdown(
    db: AsyncSession, limit: int = 20
) -> AnalyticsFailingRulesResponse:
    """
    Computes failure distribution across statutory LMPC rules.
    """
    # 1. Total failed checks count
    total_fails_stmt = select(func.count(ComplianceCheck.id)).where(
        ComplianceCheck.result == CheckResult.FAIL
    )
    total_failed_checks = int((await db.execute(total_fails_stmt)).scalar_one() or 0)

    # 2. Group by legal rule
    stmt = (
        select(
            LegalRule.rule_code,
            LegalRule.title,
            LegalRule.source_reference,
            LegalRule.rule_type,
            func.count(ComplianceCheck.id).label("failure_count"),
        )
        .join(LegalRule, ComplianceCheck.legal_rule_id == LegalRule.id)
        .where(ComplianceCheck.result == CheckResult.FAIL)
        .group_by(
            LegalRule.rule_code,
            LegalRule.title,
            LegalRule.source_reference,
            LegalRule.rule_type,
        )
        .order_by(func.count(ComplianceCheck.id).desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    failing_rules: List[FailingRuleMetric] = []
    for r in rows:
        f_count = int(r.failure_count or 0)
        f_pct = (
            round((f_count / total_failed_checks) * 100.0, 2)
            if total_failed_checks > 0
            else 0.0
        )
        failing_rules.append(
            FailingRuleMetric(
                rule_code=r.rule_code,
                title=r.title,
                statutory_reference=r.source_reference,
                rule_type=r.rule_type.value if hasattr(r.rule_type, "value") else str(r.rule_type),
                failure_count=f_count,
                failure_percentage=f_pct,
            )
        )

    return AnalyticsFailingRulesResponse(
        total_failed_checks=total_failed_checks,
        failing_rules=failing_rules,
    )

