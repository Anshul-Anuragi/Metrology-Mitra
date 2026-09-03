from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_inspections: int = 0
    compliant_inspections: int = 0
    non_compliant_inspections: int = 0
    needs_review_inspections: int = 0
    pending_inspections: int = 0
    compliance_rate_percent: float = 0.0
    total_violations: int = 0
    high_or_critical_violations: int = 0
    active_inspecting_officers: int = 0


class TrendDataPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_start: str
    total_inspections: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    needs_review_count: int = 0
    violation_count: int = 0


class AnalyticsTrendsResponse(BaseModel):
    period: str
    data_points: List[TrendDataPoint] = []


class HeatmapClusterPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: str
    district: str
    inspection_count: int = 0
    violation_count: int = 0
    non_compliant_count: int = 0
    non_compliance_rate_percent: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_gps_coordinates: bool = False


class AnalyticsHeatmapsResponse(BaseModel):
    total_regions: int = 0
    clusters: List[HeatmapClusterPoint] = []


class RecurringNonComplianceEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_name: str
    entity_type: str = "MANUFACTURER"
    inspection_count: int = 0
    violation_count: int = 0
    non_compliant_inspection_count: int = 0
    recurrence_rate_percent: float = 0.0
    common_failed_rule_codes: List[str] = []


class AnalyticsRepeatOffendersResponse(BaseModel):
    total_entities_tracked: int = 0
    entities: List[RecurringNonComplianceEntity] = []


class FailingRuleMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_code: str
    title: str
    statutory_reference: Optional[str] = None
    rule_type: Optional[str] = None
    failure_count: int = 0
    failure_percentage: float = 0.0


class AnalyticsFailingRulesResponse(BaseModel):
    total_failed_checks: int = 0
    failing_rules: List[FailingRuleMetric] = []

