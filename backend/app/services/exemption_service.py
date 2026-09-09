from typing import Any, Dict, List, Optional
from app.schemas.exemption import ExemptionEvaluationResponse


def evaluate_statutory_exemption(
    package_type: str = "STANDARD",
    net_quantity_value: Optional[float] = None,
    net_quantity_unit: Optional[str] = None,
    commodity_category: Optional[str] = None,
    is_agricultural_farm_produce: bool = False,
    is_institutional_consumer: bool = False,
    has_institutional_marking: bool = False,
    is_fast_food_takeout: bool = False,
    is_dpco_formulation: bool = False,
    is_tobacco_product: bool = False,
    multi_piece_count: Optional[int] = None,
    combination_items: Optional[List[Dict[str, Any]]] = None,
) -> ExemptionEvaluationResponse:
    """
    Deterministic evaluation of statutory exemptions under Rule 26 and special packaging provisions
    (Rule 2(p), Rule 21, and Rule 22) of the Legal Metrology (Packaged Commodities) Rules, 2011.

    Legal Invariant: Exemption eligibility requires both statutory classification and sufficient
    supporting factual evidence. Ambiguous or unsupported claims yield NEEDS_REVIEW rather than automatic PASS.
    """
    pkg_t = (package_type or "STANDARD").strip().upper()
    u = (net_quantity_unit or "g").strip().lower()

    # Normalize net quantity to grams / ml
    val_in_base = net_quantity_value
    if val_in_base is not None:
        if u in ("kg", "kilogram", "kilograms") or u in ("l", "ltr", "litre", "liter", "litres", "liters"):
            val_in_base = val_in_base * 1000.0

    # -------------------------------------------------------------------------
    # 1. Rule 26(a): Small Package Exemption (<= 10g or <= 10ml)
    # -------------------------------------------------------------------------
    is_small_nominal = (val_in_base is not None and 0.0 < val_in_base <= 10.0)
    if pkg_t == "SMALL_PACK" or is_small_nominal:
        # Proviso 2: Tobacco and tobacco products are explicitly excluded from Rule 26(a)
        if is_tobacco_product or (commodity_category and commodity_category.upper() in ("TOBACCO", "CIGARETTE", "BIDI", "PAN_MASALA")):
            return ExemptionEvaluationResponse(
                package_type="SMALL_PACK",
                is_exempt=False,
                assessment_status="NOT_EXEMPT",
                exemption_rule="Rule 26(a) Proviso 2",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 26(a) Proviso (Tobacco Exclusion)"],
                statutory_citations=["Proviso 2 to Rule 26(a), LMPC Rules, 2011"],
                statutory_conditions=["Commodity must not be tobacco or tobacco product"],
                missing_statutory_facts=["Proviso to Rule 26(a) explicitly denies exemption to packages of tobacco or tobacco products."],
                rationale="Under the second proviso to Rule 26(a), small package exemptions do NOT apply to tobacco and tobacco products.",
            )

        return ExemptionEvaluationResponse(
            package_type="SMALL_PACK",
            is_exempt=True,
            assessment_status="EXEMPTION_ELIGIBLE",
            exemption_rule="Rule 26(a)",
            exempt_mandatory_declarations=["mrp", "unit_sale_price", "manufacturing_date", "packing_date"],
            applicable_special_rules=["Rule 26(a) Small Package Provisions"],
            statutory_citations=["Rule 26(a), LMPC Rules, 2011"],
            statutory_conditions=[
                "Net weight or measure is 10g or 10ml or less",
                "Sold by weight or measure",
                "Commodity is not tobacco or a tobacco product",
            ],
            missing_statutory_facts=[],
            rationale=(
                "Under Rule 26(a), packages containing net weight or measure of 10g or 10ml or less "
                "are exempt from mandatory retail MRP, unit sale price, and manufacturing/packing date declarations. "
                "Manufacturer identification and net quantity remain mandatory."
            ),
        )

    # -------------------------------------------------------------------------
    # 1B. Rule 26(a) Proviso 1: 10g-20g / 10ml-20ml Package Proviso
    # -------------------------------------------------------------------------
    is_medium_small_nominal = (val_in_base is not None and 10.0 < val_in_base <= 20.0)
    if is_medium_small_nominal:
        if is_tobacco_product or (commodity_category and commodity_category.upper() in ("TOBACCO", "CIGARETTE", "BIDI", "PAN_MASALA")):
            return ExemptionEvaluationResponse(
                package_type="STANDARD",
                is_exempt=False,
                assessment_status="NOT_EXEMPT",
                exemption_rule="Rule 26(a) Proviso 2",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 26(a) Proviso (Tobacco Exclusion)"],
                statutory_citations=["Proviso 2 to Rule 26(a), LMPC Rules, 2011"],
                statutory_conditions=["Commodity must not be tobacco or tobacco product"],
                missing_statutory_facts=["Tobacco products are barred from Rule 26(a) provisos."],
                rationale="Tobacco and tobacco products are excluded from small package provisos.",
            )

        return ExemptionEvaluationResponse(
            package_type="MEDIUM_SMALL_PROVISO",
            is_exempt=True,
            assessment_status="EXEMPTION_ELIGIBLE",
            exemption_rule="Rule 26(a) Proviso 1",
            exempt_mandatory_declarations=["mrp", "unit_sale_price", "manufacturing_date", "packing_date"],
            applicable_special_rules=["Rule 26(a) Proviso 1 (10g-20g Declaration Relaxation)"],
            statutory_citations=["First Proviso to Rule 26(a), LMPC Rules, 2011"],
            statutory_conditions=[
                "Net weight or measure is between 10g-20g or 10ml-20ml",
                "Sold by weight or measure",
                "Commodity is not tobacco",
            ],
            missing_statutory_facts=[],
            rationale=(
                "Under the first proviso to Rule 26(a), packages containing net quantity of 10g to 20g (or 10ml to 20ml) "
                "shall not require declarations of MRP, Unit Sale Price, and Date of manufacture/packing."
            ),
        )

    # -------------------------------------------------------------------------
    # 2. Rule 26(b): Fast Food Items Packed by Restaurant / Hotel
    # -------------------------------------------------------------------------
    if pkg_t == "FAST_FOOD" or is_fast_food_takeout:
        if is_fast_food_takeout:
            return ExemptionEvaluationResponse(
                package_type="FAST_FOOD",
                is_exempt=True,
                assessment_status="EXEMPTION_ELIGIBLE",
                exemption_rule="Rule 26(b)",
                exempt_mandatory_declarations=["mrp", "unit_sale_price", "manufacturing_date", "packing_date", "consumer_care"],
                applicable_special_rules=["Rule 26(b) Fast Food Restaurant Provisions"],
                statutory_citations=["Rule 26(b), LMPC Rules, 2011"],
                statutory_conditions=["Food items packed by hotel/restaurant for immediate consumption/takeout"],
                missing_statutory_facts=[],
                rationale="Under Rule 26(b), fast food items packed by hotels/restaurants for immediate takeout are exempt from Chapter II declarations.",
            )
        else:
            return ExemptionEvaluationResponse(
                package_type="FAST_FOOD",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule="Rule 26(b)",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 26(b) Restaurant Takeout Verification"],
                statutory_citations=["Rule 26(b), LMPC Rules, 2011"],
                statutory_conditions=["Food items packed by restaurant/hotel for immediate consumption"],
                missing_statutory_facts=["Verification that package is an immediate takeout item prepared by restaurant/hotel."],
                rationale="Fast food category selected but immediate takeout preparation by restaurant/hotel not verified under Rule 26(b).",
            )

    # -------------------------------------------------------------------------
    # 3. Rule 26(c): Formulations under Drugs (Prices Control) Order (DPCO), 2013
    # -------------------------------------------------------------------------
    if pkg_t == "DPCO_DRUG" or is_dpco_formulation:
        if is_dpco_formulation:
            return ExemptionEvaluationResponse(
                package_type="DPCO_DRUG",
                is_exempt=True,
                assessment_status="EXEMPTION_ELIGIBLE",
                exemption_rule="Rule 26(c)",
                exempt_mandatory_declarations=["mrp", "unit_sale_price"],
                applicable_special_rules=["Rule 26(c) DPCO 2013 Drug Formulation Provisions"],
                statutory_citations=["Rule 26(c), LMPC Rules, 2011", "DPCO, 2013", "Drugs and Cosmetics Act, 1940"],
                statutory_conditions=["Scheduled or non-scheduled formulations covered under Drugs (Prices Control) Order (DPCO), 2013"],
                missing_statutory_facts=[],
                rationale=(
                    "Under Rule 26(c), scheduled and non-scheduled formulations covered under DPCO 2013 "
                    "are governed by the Drugs and Cosmetics Act, 1940 and exempt from LMPC Chapter II retail MRP declarations."
                ),
            )
        else:
            return ExemptionEvaluationResponse(
                package_type="DPCO_DRUG",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule="Rule 26(c)",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 26(c) DPCO Formulation Verification"],
                statutory_citations=["Rule 26(c), LMPC Rules, 2011"],
                statutory_conditions=["Formulation covered under DPCO 2013"],
                missing_statutory_facts=["Verification of DPCO 2013 scheduled/non-scheduled formulation status."],
                rationale="Drug formulation selected but DPCO 2013 regulatory coverage not verified under Rule 26(c).",
            )

    # -------------------------------------------------------------------------
    # 4. Rule 26(d): Agricultural Farm Produce Exemption (> 50kg)
    # -------------------------------------------------------------------------
    is_bulk_nominal = (val_in_base is not None and val_in_base > 50000.0)
    if pkg_t == "AGRICULTURAL_BULK" or is_bulk_nominal:
        # Statutory condition: Must be raw agricultural farm produce (not generic industrial goods)
        is_farm_produce = is_agricultural_farm_produce or (
            commodity_category and commodity_category.upper() in ("AGRICULTURAL_FARM_PRODUCE", "GRAIN", "PULSES", "WHEAT", "RICE_FARM", "FARM_PRODUCE")
        )
        if is_farm_produce:
            return ExemptionEvaluationResponse(
                package_type="AGRICULTURAL_BULK",
                is_exempt=True,
                assessment_status="EXEMPTION_ELIGIBLE",
                exemption_rule="Rule 26(d)",
                exempt_mandatory_declarations=["mrp", "unit_sale_price", "consumer_care", "manufacturing_date", "packing_date"],
                applicable_special_rules=["Rule 26(d) Agricultural Bulk Farm Produce Provisions"],
                statutory_citations=["Rule 26(d), LMPC Rules, 2011"],
                statutory_conditions=[
                    "Package net quantity exceeds 50 kg",
                    "Commodity strictly constitutes agricultural farm produce",
                ],
                missing_statutory_facts=[],
                rationale=(
                    "Under Rule 26(d), packages containing agricultural farm produce exceeding 50 kg "
                    "are exempt from standard Chapter II retail declarations."
                ),
            )
        else:
            # Generic package >50kg without verified agricultural status is NOT automatically exempt
            return ExemptionEvaluationResponse(
                package_type=pkg_t if pkg_t == "AGRICULTURAL_BULK" else "STANDARD",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule="Rule 26(d)",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 26(d) Agricultural Verification Requirement"],
                statutory_citations=["Rule 26(d), LMPC Rules, 2011"],
                statutory_conditions=["Commodity must be proven to be raw agricultural farm produce"],
                missing_statutory_facts=[
                    "Verification required: Rule 26(d) exemption applies strictly to agricultural farm produce >50kg. "
                    "Generic industrial or commercial packages >50kg are not automatically exempt."
                ],
                rationale="Package exceeds 50 kg but commodity is not verified as agricultural farm produce under Rule 26(d).",
            )

    # -------------------------------------------------------------------------
    # 5. Rule 2(p) read with Rule 3: Institutional Consumer Package (Separate Provision)
    # -------------------------------------------------------------------------
    if pkg_t == "INSTITUTIONAL" or is_institutional_consumer:
        if is_institutional_consumer and has_institutional_marking:
            return ExemptionEvaluationResponse(
                package_type="INSTITUTIONAL",
                is_exempt=True,
                assessment_status="EXEMPTION_ELIGIBLE",
                exemption_rule="Rule 2(p) / Rule 3",
                exempt_mandatory_declarations=["mrp", "unit_sale_price"],
                applicable_special_rules=["Rule 2(p) Institutional Consumer Definition", "Rule 3 Chapter II Proviso"],
                statutory_citations=["Rule 2(p)", "Rule 3, LMPC Rules, 2011"],
                statutory_conditions=[
                    "Direct supply agreement/contract with institutional consumer under Rule 2(p)",
                    "Package bears mandatory declaration 'Not for retail sale' or institutional identification",
                ],
                missing_statutory_facts=[],
                rationale=(
                    "Under Rule 2(p) read with Rule 3 proviso, packages intended for direct institutional consumers "
                    "(service institutions like railways, hotels, hospitals, canteens for direct use and not for retail sale) "
                    "are exempt from retail MRP and unit sale price declarations."
                ),
            )
        else:
            return ExemptionEvaluationResponse(
                package_type="INSTITUTIONAL",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule="Rule 2(p) / Rule 3",
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 2(p) Institutional Consumer Verification", "Rule 3"],
                statutory_citations=["Rule 2(p)", "Rule 3, LMPC Rules, 2011"],
                statutory_conditions=[
                    "Direct contractual supply to institutional consumer",
                    "Label marking 'Not for retail sale' or institutional identification",
                ],
                missing_statutory_facts=[
                    "Missing evidence: Direct supply contract with institutional consumer under Rule 2(p) not verified.",
                    "Missing label verification: 'Not for retail sale' or institutional marking not established.",
                ],
                rationale=(
                    "Institutional package classification claimed, but required statutory facts under Rule 2(p) "
                    "and Rule 3 are incomplete or unverified. Manual officer review required."
                ),
            )

    # -------------------------------------------------------------------------
    # 6. Rule 21: Multi-Piece Packages (Special Packaging Provision)
    # -------------------------------------------------------------------------
    if pkg_t == "MULTI_PIECE" or (multi_piece_count is not None and multi_piece_count > 1):
        has_valid_count = (multi_piece_count is not None and multi_piece_count > 1)
        if has_valid_count:
            return ExemptionEvaluationResponse(
                package_type="MULTI_PIECE",
                is_exempt=False,
                assessment_status="SPECIAL_PACKAGING_PROVISION",
                exemption_rule=None,
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 21 (Multi-Piece Packages)"],
                statutory_citations=["Rule 21, LMPC Rules, 2011"],
                statutory_conditions=[
                    "Outer package must declare total quantity and number of individual pieces",
                    "Individual pieces must bear mandatory declarations unless individually exempt",
                ],
                missing_statutory_facts=[],
                rationale=(
                    f"Multi-piece package containing {multi_piece_count} individual pieces. "
                    "Rule 21 requires declaration of the number of individual pieces and total net quantity on the outer package. "
                    "This is a special packaging regulation, NOT a blanket exemption."
                ),
            )
        else:
            return ExemptionEvaluationResponse(
                package_type="MULTI_PIECE",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule=None,
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 21 (Multi-Piece Packages)"],
                statutory_citations=["Rule 21, LMPC Rules, 2011"],
                statutory_conditions=["Individual piece count specified"],
                missing_statutory_facts=["Number of individual pieces not specified under Rule 21."],
                rationale="Multi-piece packaging selected but individual piece count is missing.",
            )

    # -------------------------------------------------------------------------
    # 7. Rule 22: Combination Packages (Special Packaging Provision)
    # -------------------------------------------------------------------------
    if pkg_t == "COMBINATION" or (combination_items and len(combination_items) > 1):
        has_valid_items = (combination_items is not None and len(combination_items) > 1)
        if has_valid_items:
            return ExemptionEvaluationResponse(
                package_type="COMBINATION",
                is_exempt=False,
                assessment_status="SPECIAL_PACKAGING_PROVISION",
                exemption_rule=None,
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 22 (Combination Packages)"],
                statutory_citations=["Rule 22, LMPC Rules, 2011"],
                statutory_conditions=[
                    "Outer package must declare name and net quantity of each distinct commodity",
                    "Single comprehensive MRP for the combined package",
                ],
                missing_statutory_facts=[],
                rationale=(
                    f"Combination package containing {len(combination_items)} distinct commodities. "
                    "Rule 22 requires name and quantity of each distinct commodity and single total MRP on outer package. "
                    "This is a special packaging regulation, NOT a blanket exemption."
                ),
            )
        else:
            return ExemptionEvaluationResponse(
                package_type="COMBINATION",
                is_exempt=False,
                assessment_status="NEEDS_REVIEW",
                exemption_rule=None,
                exempt_mandatory_declarations=[],
                applicable_special_rules=["Rule 22 (Combination Packages)"],
                statutory_citations=["Rule 22, LMPC Rules, 2011"],
                statutory_conditions=["Distinct commodity item details specified"],
                missing_statutory_facts=["Individual commodity items in combination pack not specified under Rule 22."],
                rationale="Combination package selected but distinct commodity item breakdown is missing.",
            )

    # -------------------------------------------------------------------------
    # 8. Standard Retail Package (Default)
    # -------------------------------------------------------------------------
    return ExemptionEvaluationResponse(
        package_type="STANDARD",
        is_exempt=False,
        assessment_status="NOT_EXEMPT",
        exemption_rule=None,
        exempt_mandatory_declarations=[],
        applicable_special_rules=["Chapter II General Retail Packaging Provisions"],
        statutory_citations=["Rule 6, LMPC Rules, 2011"],
        statutory_conditions=["Subject to all standard mandatory retail declarations"],
        missing_statutory_facts=[],
        rationale="Standard retail package. All Chapter II mandatory declarations (Rule 6) apply fully.",
    )
