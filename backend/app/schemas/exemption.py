from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExemptionEvaluationRequest(BaseModel):
    package_type: str = Field("STANDARD", description="STANDARD, SMALL_PACK, INSTITUTIONAL, AGRICULTURAL_BULK, FAST_FOOD, MULTI_PIECE, COMBINATION")
    declared_net_quantity_value: Optional[float] = Field(None, ge=0.0, description="Nominal net quantity numeric value")
    declared_net_quantity_unit: Optional[str] = Field(None, description="Nominal net quantity unit (g, kg, ml, l)")
    commodity_category: Optional[str] = Field(None, description="Category of commodity e.g. AGRICULTURAL_FARM_PRODUCE, FOOD, FMCG, TOBACCO, DRUG")
    is_agricultural_farm_produce: bool = Field(False, description="Verified as raw agricultural farm produce")
    is_institutional_consumer: bool = Field(False, description="Whether package is for direct institutional consumption under contract")
    has_institutional_marking: bool = Field(False, description="Whether package bears 'Not for retail sale' or institutional identification")
    is_fast_food_takeout: bool = Field(False, description="Food item packed by hotel/restaurant for immediate consumption")
    is_tobacco_product: bool = Field(False, description="Whether commodity is tobacco or tobacco product")
    multi_piece_count: Optional[int] = Field(None, ge=1, description="Number of individual pieces for Rule 21 multi-piece packages")
    combination_items: Optional[List[Dict[str, Any]]] = Field(None, description="Distinct commodities in combination pack for Rule 22")


class ExemptionEvaluationResponse(BaseModel):
    package_type: str
    is_exempt: bool
    assessment_status: str = Field(..., description="EXEMPTION_ELIGIBLE, NEEDS_REVIEW, NOT_EXEMPT, SPECIAL_PACKAGING_PROVISION")
    exemption_rule: Optional[str] = None
    exempt_mandatory_declarations: List[str] = Field(default_factory=list)
    applicable_special_rules: List[str] = Field(default_factory=list)
    statutory_citations: List[str]
    rationale: str
    missing_statutory_facts: List[str] = Field(default_factory=list)
    statutory_conditions: List[str] = Field(default_factory=list)
    source_legislation: str = "Legal Metrology (Packaged Commodities) Rules, 2011"
    source_version: str = "GSR 202(E) / LMPC 2011"
    effective_from: str = "2011-04-01"
    effective_to: Optional[str] = None
    disclaimer: str = (
        "Statutory exemption assessment under Rule 26 and special packaging provisions (Rules 21-22) of LMPC Rules, 2011. "
        "Package classification is an assessment input. Final exemption applicability requires authorized officer verification of commercial channel and statutory conditions."
    )
