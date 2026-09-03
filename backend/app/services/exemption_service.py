from typing import Any, Dict, List, Optional
from app.schemas.exemption import ExemptionEvaluationResponse


def evaluate_statutory_exemption(
    package_type: str = "STANDARD",
    net_quantity_value: Optional[float] = None,
    net_quantity_unit: Optional[str] = None,
    is_institutional_consumer: bool = False,
    multi_piece_count: Optional[int] = None,
    combination_items: Optional[List[Dict[str, Any]]] = None,
) -> ExemptionEvaluationResponse:
    """
    Evaluates statutory exemptions under Rule 26 and special packaging rules (Rules 21, 22)
    of the Legal Metrology (Packaged Commodities) Rules, 2011.
    """
    pkg_t = (package_type or "STANDARD").strip().upper()
    u = (net_quantity_unit or "g").strip().lower()

    # Normalize to grams/ml
    val_in_base = net_quantity_value
    if val_in_base is not None:
        if u == "kg" or u in ("l", "ltr", "litre", "liter"):
            val_in_base = val_in_base * 1000.0

    # 1. Rule 26(a): Small Package Exemption (<= 10g or <= 10ml)
    if pkg_t == "SMALL_PACK" or (val_in_base is not None and val_in_base <= 10.0 and val_in_base > 0):
        return ExemptionEvaluationResponse(
            package_type="SMALL_PACK",
            is_exempt=True,
            exemption_rule="Rule 26(a)",
            exempt_mandatory_declarations=["mrp", "unit_sale_price", "manufacturing_date", "packing_date"],
            applicable_special_rules=["Rule 26(a) Small Package Provisions"],
            statutory_citations=["Rule 26(a), LMPC Rules, 2011"],
            rationale=(
                "Under Rule 26(a), packages containing net weight or measure of 10g or 10ml or less "
                "are exempt from mandatory retail MRP, unit sale price, and manufacturing/packing date declarations."
            ),
        )

    # 2. Rule 26(b): Bulk Agricultural Produce Exemption (> 50kg)
    if pkg_t == "AGRICULTURAL_BULK" or (val_in_base is not None and val_in_base > 50000.0):
        return ExemptionEvaluationResponse(
            package_type="AGRICULTURAL_BULK",
            is_exempt=True,
            exemption_rule="Rule 26(b)",
            exempt_mandatory_declarations=["mrp", "unit_sale_price", "consumer_care"],
            applicable_special_rules=["Rule 26(b) Agricultural Bulk Provisions"],
            statutory_citations=["Rule 26(b), LMPC Rules, 2011"],
            rationale="Under Rule 26(b), packages containing agricultural produce exceeding 50 kg are exempt from standard retail packaging rules.",
        )

    # 3. Rule 26(c) read with Rule 2(p): Institutional / Industrial Consumer Exemption
    if pkg_t == "INSTITUTIONAL" or is_institutional_consumer:
        return ExemptionEvaluationResponse(
            package_type="INSTITUTIONAL",
            is_exempt=True,
            exemption_rule="Rule 26(c) / Rule 2(p)",
            exempt_mandatory_declarations=["mrp", "unit_sale_price"],
            applicable_special_rules=["Rule 2(p) Institutional Consumer Definition", "Rule 26(c)"],
            statutory_citations=["Rule 26(c)", "Rule 2(p), LMPC Rules, 2011"],
            rationale=(
                "Under Rule 26(c) read with Rule 2(p), packages intended for direct institutional consumers "
                "(service institutions like railways, hotels, hospitals for direct use and not for retail sale) "
                "are exempt from Chapter II retail declarations."
            ),
        )

    # 4. Rule 21: Multi-Piece Packages
    if pkg_t == "MULTI_PIECE" or (multi_piece_count is not None and multi_piece_count > 1):
        return ExemptionEvaluationResponse(
            package_type="MULTI_PIECE",
            is_exempt=False,
            exemption_rule=None,
            exempt_mandatory_declarations=[],
            applicable_special_rules=["Rule 21 (Multi-Piece Packages)"],
            statutory_citations=["Rule 21, LMPC Rules, 2011"],
            rationale=(
                f"Multi-piece package containing {multi_piece_count or 'multiple'} individual pieces. "
                "Rule 21 requires declaration of the number of individual pieces and individual net quantities on the outer package."
            ),
        )

    # 5. Rule 22: Combination Packages
    if pkg_t == "COMBINATION" or (combination_items and len(combination_items) > 1):
        return ExemptionEvaluationResponse(
            package_type="COMBINATION",
            is_exempt=False,
            exemption_rule=None,
            exempt_mandatory_declarations=[],
            applicable_special_rules=["Rule 22 (Combination Packages)"],
            statutory_citations=["Rule 22, LMPC Rules, 2011"],
            rationale="Combination package containing distinct commodities. Rule 22 requires name and quantity of each distinct commodity on outer package.",
        )

    # Standard Retail Package
    return ExemptionEvaluationResponse(
        package_type="STANDARD",
        is_exempt=False,
        exemption_rule=None,
        exempt_mandatory_declarations=[],
        applicable_special_rules=["Chapter II (General Provisions)"],
        statutory_citations=["LMPC Rules, 2011 (Chapter II)"],
        rationale="Standard retail package subject to all 18 mandatory Chapter II statutory declarations.",
    )

