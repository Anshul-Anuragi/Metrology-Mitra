"""
Phase 4.1 — Synthetic Validation Fixtures
=========================================
All fixtures in this module are strictly synthetic and designated for testing and validation.
MARKER: SYNTHETIC_VALIDATION_FIXTURE
No real government registration numbers, fake official documents, fake certificates,
or simulated live government integrations are used.
"""

from typing import Any, Dict, List

FIXTURE_MARKER = "SYNTHETIC_VALIDATION_FIXTURE"

# -------------------------------------------------------------------------
# 1. SYNTHETIC PRODUCT DECLARATION FIXTURES
# -------------------------------------------------------------------------

SYNTHETIC_COMPLIANT_DECLARATION: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "commodity_name": "Refined Sunflower Oil",
    "manufacturer_name": "Sun Agro Foods India Private Limited",
    "address": "Plot No. 42, Sector 8, Industrial Estate, Gandhinagar, Gujarat - 382028",
    "net_quantity": "1 l",
    "mrp": "Rs. 165.00 (inclusive of all taxes)",
    "unit_sale_price": "Rs. 165.00 per l",
    "manufacturing_date": "04/2026",
    "expiry_date": "04/2027",
    "consumer_care": "care@sunagrofoods.synthetic, Toll Free: 1800-000-4242",
    "country_of_origin": "India",
    "raw_extractions": {
        "pdp_area_sq_cm": 150.0,
        "numeral_height_mm": 4.5,
        "is_calibrated": True,
        "language_detected": "ENG",
    },
}

SYNTHETIC_MISSING_DECLARATIONS: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "commodity_name": "Premium Roasted Peanuts",
    "manufacturer_name": "Synthetic Snackers LLP",
    "address": "Warehouse 12, Industrial Area, Indore, Madhya Pradesh",
    "net_quantity": "200 Gms",  # Disallowed non-SI unit symbol under Rule 13 -> FAIL
    "mrp": "Rs. 95.00",  # Omits mandatory 'incl. of all taxes' statement under Rule 6(1)(e) -> FAIL
    "unit_sale_price": None,
    "manufacturing_date": "03/2026",
    "expiry_date": "09/2026",
    "consumer_care": "",  # Missing mandatory declaration under Rule 6(1)(f) -> REVIEW
    "country_of_origin": "India",
}

SYNTHETIC_MULTILINGUAL_DECLARATION: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "commodity_name": "शुद्ध बासमती चावल (Pure Basmati Rice)",
    "manufacturer_name": "भारत एग्रो फूड्स (Bharat Agro Foods)",
    "address": "ग्राम व डाकघर तरावड़ी, करनाल, हरियाणा - 132116",
    "net_quantity": "५ kg (5 kg)",
    "mrp": "रु ४५०.०० (Rs 450.00) सभी कर सहित (incl. of all taxes)",
    "unit_sale_price": "रु ९०.०० प्रति किग्रा (Rs 90.00 / kg)",
    "manufacturing_date": "०२/२०२६ (02/2026)",
    "consumer_care": "care@bharatagro.synthetic, दूरभाष: १८००-०००-५५५५",
    "country_of_origin": "भारत (India)",
    "raw_extractions": {
        "language_detected": "MIXED",
        "devanagari_numeral_translation": {
            "५ kg": "5 kg",
            "४५०.००": "450.00",
            "९०.००": "90.00",
            "०२/२०२६": "02/2026",
        },
    },
}

SYNTHETIC_NON_STANDARD_UNIT_DECLARATION: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "commodity_name": "Whole Wheat Flour",
    "manufacturer_name": "Organic Mills India",
    "address": "Village Kheda, District Pune, Maharashtra - 410501",
    "net_quantity": "5 KGS",  # Disallowed abbreviation under Rule 13 (must be 'kg')
    "mrp": "Rs. 220.00 incl. of all taxes",
    "unit_sale_price": "Rs. 44.00 / kg",
    "manufacturing_date": "05/2026",
    "consumer_care": "contact@organicmills.synthetic",
    "country_of_origin": "India",
}

# -------------------------------------------------------------------------
# 2. SYNTHETIC PHYSICAL METROLOGY & GRAVIMETRIC SCALE FIXTURES
# -------------------------------------------------------------------------

SYNTHETIC_GRAVIMETRIC_PASSED_LOT: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "nominal_quantity": 500.0,
    "unit": "g",
    "default_tare": 12.0,
    "lot_size": 1000,
    "sample_weights": [
        {"gross_weight": 515.0, "tare_weight": 12.0},  # Net = 503.0g
        {"gross_weight": 514.0, "tare_weight": 12.0},  # Net = 502.0g
        {"gross_weight": 513.5, "tare_weight": 12.0},  # Net = 501.5g
        {"gross_weight": 512.0, "tare_weight": 12.0},  # Net = 500.0g
        {"gross_weight": 516.0, "tare_weight": 12.0},  # Net = 504.0g
    ],
}

SYNTHETIC_GRAVIMETRIC_DEFICIT_LOT: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "nominal_quantity": 500.0,
    "unit": "g",
    "default_tare": 12.0,
    "lot_size": 1000,
    "sample_weights": [
        {"gross_weight": 505.0, "tare_weight": 12.0},  # Net = 493.0g (defective: error -7g, within MPE 15g)
        {"gross_weight": 504.0, "tare_weight": 12.0},  # Net = 492.0g (defective: error -8g)
        {"gross_weight": 506.0, "tare_weight": 12.0},  # Net = 494.0g (defective: error -6g)
        # Mean net = 493.0g < 500.0g -> Fails sample mean deficit requirement under Rule 19 + Sixth Schedule
    ],
}

SYNTHETIC_GRAVIMETRIC_DOUBLE_MPE_LOT: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "nominal_quantity": 500.0,
    "unit": "g",
    "default_tare": 12.0,
    "lot_size": 1000,
    "sample_weights": [
        {"gross_weight": 515.0, "tare_weight": 12.0},  # Net = 503.0g
        {"gross_weight": 514.0, "tare_weight": 12.0},  # Net = 502.0g
        {"gross_weight": 475.0, "tare_weight": 12.0},  # Net = 463.0g (Deficit = -37.0g > 2 * 15g = 30g Double-MPE!)
    ],
}

# -------------------------------------------------------------------------
# 3. SYNTHETIC CORPORATE & REGISTRATION FIXTURES
# -------------------------------------------------------------------------

SYNTHETIC_COMPANY_RECORD: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "cin": "U15400GJ2024PTC999999",
    "company_name": "Synthetic Consumer Packaged Goods Ltd.",
    "registered_office": "100 Innovation Tower, SG Highway, Ahmedabad, Gujarat - 380054",
    "state": "Gujarat",
    "nominated_directors": [
        {
            "director_name": "Rohan J. Mehta",
            "din": "09999999",
            "designation": "Director (Operations & Compliance)",
            "form_i_reference": "FORM-I-NOTIF-2024-999",
            "is_active": True,
        }
    ],
}

SYNTHETIC_PACKER_REGISTRATION: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "registration_number": "SYNTH-REG-LM-2026-001",
    "entity_name": "Synthetic Consumer Packaged Goods Ltd.",
    "registered_address": "100 Innovation Tower, SG Highway, Ahmedabad, Gujarat - 380054",
    "jurisdiction_level": "STATE_CONTROLLER",
    "state": "Gujarat",
    "issuing_authority": "Controller of Legal Metrology, Gujarat",
    "registered_categories": ["Edible Oils", "Food Commodities"],
}

# -------------------------------------------------------------------------
# 4. SYNTHETIC SEIZURE & PANCHNAMA FIXTURES
# -------------------------------------------------------------------------

SYNTHETIC_SEIZURE_RECORD: Dict[str, Any] = {
    "fixture_type": FIXTURE_MARKER,
    "seizure_memo_number": "SYNTH-SEIZURE-2026-001",
    "premises_name": "Synthetic Retail Supermarket Outlet",
    "premises_address": "Shop 4, Commercial Complex, Sector 21, Gandhinagar, Gujarat",
    "statutory_grounds": "Seizure under Section 15 of Legal Metrology Act, 2009 for non-standard package declarations",
    "witness_1_name": "Amit Sharma (Independent Citizen)",
    "witness_1_address": "Flat 201, Green Meadows, Gandhinagar",
    "witness_1_phone": "9876543210",
    "witness_2_name": "Pooja Patel (Independent Citizen)",
    "witness_2_address": "Shop 6, Commercial Complex, Sector 21, Gandhinagar",
    "witness_2_phone": "9876543211",
    "custody_location": "Legal Metrology Department Safe Storage, Gandhinagar",
    "items": [
        {
            "commodity_name": "Refined Sunflower Oil 1L (Non-Standard Pack)",
            "brand_name": "Sun Agro",
            "batch_lot_number": "BATCH-2026-SYNTH-01",
            "declared_net_quantity": "1 l",
            "total_packages_seized": 40,
            "sample_packages_taken": 2,
            "sample_seal_tag_number": "SEAL-TAG-2026-001",
            "mrp": 165.0,
        }
    ],
}
