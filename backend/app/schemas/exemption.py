from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExemptionEvaluationRequest(BaseModel):
    package_type: str = Field("STANDARD", description="STANDARD, SMALL_PACK, INSTITUTIONAL, AGRICULTURAL_BULK, MULTI_PIECE, COMBINATION")
    declared_net_quantity_value: Optional[float] = Field(None, ge=0.0, description="Nominal net quantity numeric value")
    declared_net_quantity_unit: Optional[str] = Field(None, description="Nominal net quantity unit (g, kg, ml, l)")
    is_institutional_consumer: bool = Field(False, description="Whether package is for direct institutional consumption under contract")
    multi_piece_count: Optional[int] = Field(None, ge=1, description="Number of individual pieces for Rule 21 multi-piece packages")
    combination_items: Optional[List[Dict[str, Any]]] = Field(None, description="Distinct commodities in combination pack for Rule 22")


class ExemptionEvaluationResponse(BaseModel):
    package_type: str
    is_exempt: bool
    exemption_rule: Optional[str] = None
    exempt_mandatory_declarations: List[str] = Field(default_factory=list)
    applicable_special_rules: List[str] = Field(default_factory=list)
    statutory_citations: List[str]
    rationale: str
    source_legislation: str = "Legal Metrology (Packaged Commodities) Rules, 2011"
    source_version: str = "GSR 202(E) / LMPC 2011"
    effective_from: str = "2011-04-01"
    effective_to: Optional[str] = None
    disclaimer: str = (
        "Statutory exemption assessment under Rule 26 and Rules 21-22 of LMPC Rules, 2011. "
        "Exemption applicability requires field verification of commercial channel and packaging context."
    )

