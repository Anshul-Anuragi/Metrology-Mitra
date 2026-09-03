import datetime
from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import RuleType
from app.models.legal_rule import LegalRule

# 18 Encoded statutory compliance checks derived from selected provisions of
# the Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011 (as amended).
DEFAULT_LMPC_RULES = [
    {
        "rule_code": "LMPC-R6-COMMODITY-NAME",
        "title": "Mandatory Generic / Common Name of Commodity",
        "description": "Every package must distinctly declare the generic or common name of the commodity contained therein.",
        "field_name": "commodity_name",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "min_length": 2,
            "evidence_required": ["ocr_text", "bounding_box"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-MANUFACTURER",
        "title": "Mandatory Name and Address of Manufacturer / Packer / Importer",
        "description": "Every package must distinctly bear the name and complete physical address of the manufacturer, packer (if packer is not manufacturer), or importer.",
        "field_name": "manufacturer_name",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "require_address": True,
            "evidence_required": ["entity_name", "postal_address"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-NET-QUANTITY",
        "title": "Mandatory Net Quantity in Standard SI Units",
        "description": "Every package must declare the net quantity in terms of standard unit of weight, measure or number (g, kg, ml, l, N). Symbols must strictly use standard SI notation.",
        "field_name": "net_quantity",
        "rule_type": RuleType.UNIT_CHECK,
        "parameters": {
            "valid_units": ["g", "kg", "ml", "l", "n", "u", "cm", "m"],
            "disallowed_units": ["gms", "kgs", "ltr", "gm", "ml."],
            "evidence_required": ["numeric_quantity", "si_unit_symbol"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(c) & Rule 13, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-MRP",
        "title": "Mandatory Retail Sale Price (MRP) Declaration",
        "description": "Every package must declare the Maximum Retail Price (MRP) inclusive of all taxes in the prescribed format 'MRP Rs. XX.XX incl. of all taxes' or 'MRP ₹ XX.XX (inclusive of all taxes)'.",
        "field_name": "mrp",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "required_phrases": ["incl", "taxes"],
            "currency_symbols": ["₹", "rs", "rs.", "inr"],
            "evidence_required": ["numeric_price", "tax_statement"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-DATE",
        "title": "Mandatory Month & Year of Manufacture / Packing / Import",
        "description": "Every package must declare the month and year in which the commodity is manufactured, pre-packed, or imported in a clear and legible format.",
        "field_name": "manufacturing_date",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "allowed_formats": ["MM/YYYY", "MM/YY", "Month YYYY", "YYYY-MM", "MM-YYYY"],
            "evidence_required": ["date_pattern"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-CONSUMER-CARE",
        "title": "Mandatory Consumer Complaint Grievance Redressal Contact",
        "description": "Every package must bear the name, address, telephone number, and email address of the person or office who can be contacted in case of consumer complaints.",
        "field_name": "consumer_care",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "require_phone": True,
            "require_email_or_address": True,
            "evidence_required": ["phone_number", "email_or_postal"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-ORIGIN",
        "title": "Mandatory Country of Origin for Imported Commodities",
        "description": "Every package containing imported commodities must distinctly declare the country of origin.",
        "field_name": "country_of_origin",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "conditional_on": "is_imported",
            "evidence_required": ["country_name"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(g), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-USP",
        "title": "Mandatory Unit Sale Price (USP) Declaration",
        "description": "Packages must declare Unit Sale Price (price per g/ml for commodities < 1kg/1l; price per kg/l for commodities > 1kg/1l; price per item for count-based packages).",
        "field_name": "unit_sale_price",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "effective_amendment": "2021",
            "evidence_required": ["unit_sale_price_text"],
        },
        "version": "2021.1",
        "source_version": "2021.1",
        "source_reference": "Rule 6(11), Legal Metrology (Packaged Commodities) (Amendment) Rules, 2021",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2022, 12, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-EXPIRY",
        "title": "Mandatory Best Before / Expiry Date on Perishable Commodities",
        "description": "Packages of commodities that may become unfit for human consumption after a period of time must bear the expiry date or best before date.",
        "field_name": "expiry_date",
        "rule_type": RuleType.EXPIRY_DATE_CHECK,
        "parameters": {
            "applicable_categories": ["FOOD_BEVERAGE", "COSMETIC_PERSONAL_CARE"],
            "evidence_required": ["expiry_or_best_before_date"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(d) proviso, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["FOOD_BEVERAGE", "COSMETIC_PERSONAL_CARE"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R7-FONT-HEIGHT",
        "title": "Minimum Height of Numerals & Letters in Declarations (Schedule II)",
        "description": "The minimum height of numerals in the net quantity declaration must comply with Schedule II Table 1 based on Principal Display Panel (PDP) area. When physical scale is uncalibrated, result is strictly REVIEW.",
        "field_name": "net_quantity",
        "rule_type": RuleType.NUMERAL_HEIGHT,
        "parameters": {
            "pdp_tiers_mm": [
                {"max_pdp_area_cm2": 50, "min_height_mm": 1.0, "blown_min_height_mm": 1.5},
                {"max_pdp_area_cm2": 100, "min_height_mm": 1.5, "blown_min_height_mm": 2.0},
                {"max_pdp_area_cm2": 500, "min_height_mm": 2.0, "blown_min_height_mm": 3.0},
                {"max_pdp_area_cm2": 2500, "min_height_mm": 4.0, "blown_min_height_mm": 6.0},
                {"max_pdp_area_cm2": 999999, "min_height_mm": 6.0, "blown_min_height_mm": 6.0},
            ],
            "evidence_required": ["pdp_area", "calibrated_scale", "numeral_pixel_height"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 7 & Schedule II, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "PHYSICAL_PACKAGE",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R8-PDP-PLACEMENT",
        "title": "Principal Display Panel (PDP) Placement Requirements",
        "description": "All mandatory declarations must appear on the Principal Display Panel (PDP) grouped together in a clear, conspicuous, and unobstructed manner.",
        "field_name": "pdp_area_sq_cm",
        "rule_type": RuleType.CUSTOM_LOGIC,
        "parameters": {
            "require_grouping": True,
            "evidence_required": ["pdp_bounding_boxes"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 8, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "PHYSICAL_PACKAGE",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R9-LEGIBILITY",
        "title": "Legibility, Readability & Prominent Contrast of Declarations",
        "description": "Every declaration must be prominent, clearly legible, and printed in distinct contrast with the background color of the package.",
        "field_name": "field_confidences",
        "rule_type": RuleType.FORMAT_CHECK,
        "parameters": {
            "min_optical_confidence": 0.85,
            "evidence_required": ["optical_confidence_scores"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 9, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "PHYSICAL_PACKAGE",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R18-DUAL-MRP",
        "title": "Prohibition of Sale at Price Higher than Declared MRP & Reference Catalog Verification",
        "description": "No person shall sell any commodity in packed form at a price higher than the price declared by the manufacturer. Discrepancy against reference catalog requires inspector verification.",
        "field_name": "mrp",
        "rule_type": RuleType.CUSTOM_LOGIC,
        "parameters": {
            "require_reference_match": True,
            "evidence_required": ["observed_mrp", "reference_catalog_mrp"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 18(2), Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R6-PACKER-DISTINCTION",
        "title": "Distinct Qualification of Manufacturer vs Packer / Marketer",
        "description": "Where the commodity is manufactured by one person and packed or marketed by another, declarations must distinctly qualify: 'Manufactured by...', 'Packed by...', or 'Marketed by...'.",
        "field_name": "packer_name",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "require_qualifier": True,
            "evidence_required": ["qualifier_prefix"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 6(1)(a) proviso, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R12-SYMBOL-PLACEMENT",
        "title": "Standard Representation of SI Symbols & Unit Casing",
        "description": "Symbols for units of measurement shall strictly follow standard SI conventions without trailing periods or plurals (e.g., 'kg' not 'Kg.', 'g' not 'Gms', 'ml' not 'ML').",
        "field_name": "net_quantity",
        "rule_type": RuleType.UNIT_CHECK,
        "parameters": {
            "disallowed_capitalizations": ["GMS", "Gms", "KGS", "Kgs", "LTR", "Ltr", "GM", "ML.", "Kg.", "gm.", "gms.", "kgs."],
            "evidence_required": ["unit_symbol_casing"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 12(2) & Rule 13, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R10-ECOM-DECLARATIONS",
        "title": "Mandatory E-Commerce Marketplace & Digital Product Declarations",
        "description": "An e-commerce entity shall ensure that the mandatory declarations under Rule 6(1) are displayed on the digital marketplace or pre-packed listing.",
        "field_name": "commodity_name",
        "rule_type": RuleType.CUSTOM_LOGIC,
        "parameters": {
            "require_digital_fields": ["commodity_name", "net_quantity", "mrp", "manufacturer_name"],
            "evidence_required": ["digital_listing_fields"],
        },
        "version": "2017.1",
        "source_version": "2017.1",
        "source_reference": "Rule 6(10), Legal Metrology (Packaged Commodities) (Amendment) Rules, 2017",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "ECOMMERCE",
        "effective_from": datetime.date(2018, 1, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R14-STANDARD-PACK",
        "title": "Standard Packaging Metric Denominations (Schedule II / Rule 14)",
        "description": "Specified commodities must be packed in standard metric weight or volume denominations as prescribed in the Second Schedule.",
        "field_name": "net_quantity",
        "rule_type": RuleType.UNIT_CHECK,
        "parameters": {
            "standard_denominations_check": True,
            "evidence_required": ["metric_denomination"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 5 & Second Schedule / Rule 14, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "PHYSICAL_PACKAGE",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
    {
        "rule_code": "LMPC-R27-REGISTRATION",
        "title": "Manufacturer / Packer Postal Address & Regulatory Registry Completeness",
        "description": "Every manufacturer, packer, or importer must declare complete physical address with postal jurisdiction. Without an official verification API, unverified registration produces REVIEW.",
        "field_name": "address",
        "rule_type": RuleType.REQUIRED_FIELD,
        "parameters": {
            "require_pin_or_complete_address": True,
            "evidence_required": ["postal_pin", "complete_address"],
        },
        "version": "2011.1",
        "source_version": "2011.1",
        "source_reference": "Rule 27, Legal Metrology (Packaged Commodities) Rules, 2011",
        "penalty_clause": "Section 36(1) of Legal Metrology Act, 2009",
        "category_applicability": ["ALL"],
        "channel": "BOTH",
        "effective_from": datetime.date(2011, 4, 1),
        "is_active": True,
    },
]

ACTIVE_RULE_CODES = [r["rule_code"] for r in DEFAULT_LMPC_RULES]


async def seed_legal_rules(session: AsyncSession) -> int:
    """
    Idempotently upserts the 18 statutory rules into the legal_rules table.
    Deactivates any legacy unmapped rule codes.
    """
    for rule_data in DEFAULT_LMPC_RULES:
        stmt = select(LegalRule).where(
            LegalRule.rule_code == rule_data["rule_code"],
            LegalRule.version == rule_data["version"],
        )
        result = await session.execute(stmt)
        existing_rule = result.scalar_one_or_none()

        if not existing_rule:
            rule = LegalRule(**rule_data)
            session.add(rule)
        else:
            for key, val in rule_data.items():
                setattr(existing_rule, key, val)

    # Deactivate legacy rules
    deact_stmt = (
        update(LegalRule)
        .where(LegalRule.rule_code.not_in(ACTIVE_RULE_CODES))
        .values(is_active=False)
    )
    await session.execute(deact_stmt)
    await session.commit()

    return len(DEFAULT_LMPC_RULES)
