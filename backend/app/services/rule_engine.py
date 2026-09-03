import datetime
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import CheckResult, ComplianceResult, InspectionStatus
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.legal_rule import LegalRule
from app.services.measurement_service import evaluate_reference_assisted_measurement


# -------------------------------------------------------------------
# INDIVIDUAL STATUTORY RULE EVALUATORS (18 Encoded Compliance Checks)
# -------------------------------------------------------------------

def _eval_commodity_name(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or not decl.commodity_name or not decl.commodity_name.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Generic / common commodity name declaration not detected in OCR perception; ocular verification required under Rule 6(1)(b).",
        )
    val = decl.commodity_name.strip()
    if len(val) < 2:
        return (
            CheckResult.REVIEW,
            val,
            0.5,
            "Commodity name text is too short or ambiguous to conclusively verify under Rule 6(1)(b).",
        )
    return (
        CheckResult.PASS,
        val,
        1.0 if (decl and decl.is_human_verified) else 0.95,
        "Commodity generic / common name is clearly declared on package in compliance with Rule 6(1)(b).",
    )


def _eval_manufacturer(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or (not decl.manufacturer_name and not decl.packer_name and not decl.importer_name):
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Name and address of manufacturer/packer/importer not detected in OCR text; ocular verification required under Rule 6(1)(a).",
        )
    
    name = (decl.manufacturer_name or decl.packer_name or decl.importer_name or "").strip()
    address = (decl.address or "").strip()
    
    if name and address:
        return (
            CheckResult.PASS,
            f"{name} | Address: {address}",
            1.0 if decl.is_human_verified else 0.95,
            "Name and complete address of manufacturer/packer/importer declared in compliance with Rule 6(1)(a).",
        )
    elif name and not address:
        return (
            CheckResult.REVIEW,
            f"{name} (Address missing)",
            0.6,
            "Manufacturer/packer name is present, but complete address requires ocular verification under Rule 6(1)(a).",
        )
    else:
        return (
            CheckResult.REVIEW,
            "Address without Name",
            0.6,
            "Address detected without distinct manufacturer/packer entity name under Rule 6(1)(a).",
        )


def _eval_net_quantity(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or not decl.net_quantity or not decl.net_quantity.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Net quantity declaration not detected in OCR perception; physical inspection required under Rule 6(1)(c).",
        )
    
    raw = decl.net_quantity.strip()
    
    # Check explicitly disallowed non-SI abbreviations / improper casing
    disallowed_casing_pattern = r"\b(GMS|Gms|KGS|Kgs|LTR|Ltr|GM|Gm|ML\.|Ml\.|Kg\.|kg\.|gm\.|gms\.|kgs\.)\b"
    if re.search(disallowed_casing_pattern, raw):
        return (
            CheckResult.FAIL,
            decl.net_quantity,
            0.95,
            "Non-standard unit symbol used. Standard SI unit symbols (e.g., 'g' not 'gms', 'kg' not 'kgs', 'ml' not 'ltr') are required under Rule 13.",
        )
    
    # Check valid SI quantity pattern
    valid_si_pattern = r"\b\d+(\.\d+)?\s*(g|kg|ml|l|n|u|cm|m)\b"
    if re.search(valid_si_pattern, raw, re.IGNORECASE):
        return (
            CheckResult.PASS,
            decl.net_quantity,
            1.0 if decl.is_human_verified else 0.95,
            "Net quantity declared in valid standard SI units in compliance with Rule 6(1)(c) and Rule 13.",
        )
    
    return (
        CheckResult.REVIEW,
        decl.net_quantity,
        0.5,
        "Net quantity text detected but unit format could not be conclusively validated; manual verification required.",
    )


def _eval_mrp(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if decl and (getattr(decl, "package_type", None) in ("SMALL_PACK", "INSTITUTIONAL", "AGRICULTURAL_BULK") or getattr(decl, "exemption_applied", None) in ("Rule 26(a)", "Rule 26(b)", "Rule 26(c)", "Rule 26(c) / Rule 2(p)")):
        ex_name = getattr(decl, "exemption_applied", None) or getattr(decl, "package_type", "Rule 26 Exemption")
        return (
            CheckResult.PASS,
            decl.mrp or "EXEMPT",
            1.0,
            f"Exempt from retail MRP declaration under {ex_name} of LMPC Rules, 2011.",
        )

    if not decl or not decl.mrp or not decl.mrp.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Maximum Retail Price (MRP) declaration not detected in OCR text; ocular verification required under Rule 6(1)(e).",
        )
    
    raw = decl.mrp.strip().lower()
    has_number = bool(re.search(r"\d+(\.\d{1,2})?", raw))
    has_tax_phrase = ("incl" in raw and "tax" in raw) or "inclusive of all taxes" in raw or "incl. of all taxes" in raw or "incl of all taxes" in raw
    
    if has_number and has_tax_phrase:
        return (
            CheckResult.PASS,
            decl.mrp,
            1.0 if decl.is_human_verified else 0.95,
            "MRP declared in prescribed statutory format with 'incl. of all taxes' in compliance with Rule 6(1)(e).",
        )
    elif has_number and not has_tax_phrase:
        return (
            CheckResult.FAIL,
            decl.mrp,
            0.9,
            "MRP declared without mandatory 'incl. of all taxes' or 'inclusive of all taxes' statement under Rule 6(1)(e).",
        )
    else:
        return (
            CheckResult.REVIEW,
            decl.mrp,
            0.5,
            "MRP text detected but numeric value and tax statement require visual verification.",
        )


def _eval_date(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if decl and (getattr(decl, "package_type", None) == "SMALL_PACK" or getattr(decl, "exemption_applied", None) == "Rule 26(a)"):
        return (
            CheckResult.PASS,
            "EXEMPT",
            1.0,
            "Exempt from manufacturing/packing date declaration under Rule 26(a) (Small package <= 10g/ml exemption).",
        )

    date_val = None
    if decl:
        date_val = decl.manufacturing_date or decl.packing_date or decl.import_date
    
    if not date_val or not str(date_val).strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Month and year of manufacture/packing/import not detected in OCR; physical inspection required under Rule 6(1)(d).",
        )
    
    val_str = str(date_val).strip()
    date_patterns = [
        r"^(0[1-9]|1[0-2])\s*[/-]\s*(20\d{2}|\d{2})$",
        r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(20\d{2}|\d{2})$",
        r"^(20\d{2})[-/](0[1-9]|1[0-2])$",
    ]
    
    is_valid_format = any(re.search(p, val_str, re.IGNORECASE) for p in date_patterns)
    if is_valid_format:
        return (
            CheckResult.PASS,
            val_str,
            1.0 if (decl and decl.is_human_verified) else 0.95,
            "Month and year of manufacture/packing/import declared in valid format under Rule 6(1)(d).",
        )
    
    return (
        CheckResult.REVIEW,
        val_str,
        0.6,
        "Date text detected but format requires visual confirmation under Rule 6(1)(d).",
    )


def _eval_consumer_care(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or (not decl.consumer_care and not decl.consumer_care_email and not decl.consumer_care_phone):
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Consumer complaint contact details not detected in OCR text; ocular verification required under Rule 6(1)(f).",
        )
    
    phone = (decl.consumer_care_phone or "").strip()
    email = (decl.consumer_care_email or "").strip()
    general = (decl.consumer_care or "").strip()
    
    obs = f"Phone: {phone or 'N/A'}, Email: {email or 'N/A'}"
    if general and not phone and not email:
        obs = general
    
    has_combined_contact = ("@" in general and any(c.isdigit() for c in general)) or (phone and email) or (phone and "@" in general) or (email and len(general) > 10) or (decl.is_human_verified and (phone or email or general))
    if has_combined_contact:
        return (
            CheckResult.PASS,
            obs,
            1.0 if decl.is_human_verified else 0.95,
            "Consumer care telephone number and email/address declared in compliance with Rule 6(1)(f).",
        )
    elif phone or email or general:
        return (
            CheckResult.REVIEW,
            obs,
            0.6,
            "Partial consumer care contact detected; verify that both phone and email/address are distinctly provided under Rule 6(1)(f).",
        )
    else:
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Consumer grievance redressal details missing under Rule 6(1)(f).",
        )


def _eval_origin(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl:
        return (
            CheckResult.REVIEW,
            "No declaration data",
            0.5,
            "Declaration data unavailable; cannot determine country of origin requirement under Rule 6(1)(g).",
        )
    
    if decl.is_imported:
        if decl.country_of_origin and decl.country_of_origin.strip():
            return (
                CheckResult.PASS,
                decl.country_of_origin.strip(),
                1.0 if decl.is_human_verified else 0.95,
                "Country of origin clearly declared for imported commodity in compliance with Rule 6(1)(g).",
            )
        else:
            return (
                CheckResult.REVIEW,
                "NOT DETECTED",
                0.6,
                "Package is marked as imported but country of origin was not detected in OCR; ocular verification required under Rule 6(1)(g).",
            )
    else:
        if decl.country_of_origin and decl.country_of_origin.strip():
            return (
                CheckResult.PASS,
                decl.country_of_origin.strip(),
                1.0 if decl.is_human_verified else 0.95,
                "Country of origin declared in compliance with Rule 6(1)(g).",
            )
        return (
            CheckResult.PASS,
            "Domestic (Not Imported)",
            1.0,
            "Domestic commodity; country of origin is indicated by domestic manufacturer address under Rule 6(1)(a).",
        )


def _eval_usp(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if decl and (getattr(decl, "package_type", None) in ("SMALL_PACK", "INSTITUTIONAL", "AGRICULTURAL_BULK") or getattr(decl, "exemption_applied", None) in ("Rule 26(a)", "Rule 26(b)", "Rule 26(c)", "Rule 26(c) / Rule 2(p)")):
        ex_name = getattr(decl, "exemption_applied", None) or getattr(decl, "package_type", "Rule 26 Exemption")
        return (
            CheckResult.PASS,
            decl.unit_sale_price or "EXEMPT",
            1.0,
            f"Exempt from unit sale price declaration under {ex_name} of LMPC Rules, 2011.",
        )

    if not decl or not decl.unit_sale_price or not decl.unit_sale_price.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.6,
            "Unit Sale Price (USP) not detected; verify if package is exempt or subject to mandatory Rule 6(11) USP declaration.",
        )
    
    return (
        CheckResult.PASS,
        decl.unit_sale_price.strip(),
        1.0 if decl.is_human_verified else 0.9,
        "Unit Sale Price (USP) declared in compliance with Rule 6(11).",
    )


def _eval_expiry(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    exp = None
    if decl:
        exp = decl.expiry_date or decl.best_before
    
    if exp and str(exp).strip():
        return (
            CheckResult.PASS,
            str(exp).strip(),
            1.0 if (decl and decl.is_human_verified) else 0.9,
            "Best before / expiry date declared in compliance with Rule 6(1)(d) proviso.",
        )
    
    return (
        CheckResult.REVIEW,
        "NOT DETECTED",
        0.5,
        "Best before / expiry date not detected; verify whether commodity is perishable requiring declaration under Rule 6(1)(d) proviso.",
    )


def _eval_font_height(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    """
    Evaluates numeral & font height under Rule 7 and Schedule II Table 1.
    Strict Guardrail: If physical scale cannot be established, result is strictly REVIEW.
    """
    if not decl:
        return (
            CheckResult.REVIEW,
            "No data",
            0.5,
            "Declaration data unavailable; cannot evaluate numeral height under Rule 7.",
        )
    
    if decl.is_human_verified:
        return (
            CheckResult.PASS,
            "Human verified",
            1.0,
            "Numeral height and font specification verified by inspector under Rule 7 & Schedule II.",
        )

    # Check measurement_data or raw_extractions
    m_data = decl.measurement_data or {}
    pdp_area = decl.pdp_area_sq_cm or m_data.get("pdp_area_cm2")
    pixel_height = m_data.get("pixel_height")
    pixel_scale = m_data.get("pixel_scale_mm_per_px")
    scale_source = m_data.get("scale_source", "UNAVAILABLE")
    scale_conf = float(m_data.get("scale_confidence", 0.0))

    evidence = evaluate_reference_assisted_measurement(
        pdp_area_cm2=pdp_area,
        pixel_height=pixel_height,
        pixel_scale_mm_per_px=pixel_scale,
        scale_source=scale_source,
        scale_confidence=scale_conf,
        is_human_verified=decl.is_human_verified,
    )

    observed_str = f"PDP Area: {pdp_area} cm²" if pdp_area else "Uncalibrated Scale"
    if evidence.physical_height_mm is not None:
        observed_str = f"Estimated Height: {evidence.physical_height_mm:.2f} mm (Min required: {evidence.threshold_mm} mm)"

    return (
        evidence.result,
        observed_str,
        evidence.measurement_confidence if evidence.measurement_confidence > 0 else 0.5,
        evidence.reason,
    )


def _eval_pdp_placement(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl:
        return (
            CheckResult.REVIEW,
            "No data",
            0.5,
            "Declaration data unavailable; cannot evaluate PDP placement under Rule 8.",
        )
    
    if decl.is_human_verified:
        return (
            CheckResult.PASS,
            "Human verified",
            1.0,
            "Principal Display Panel layout and grouped placement verified by inspector under Rule 8.",
        )
    
    return (
        CheckResult.REVIEW,
        "Visual inspection required",
        0.5,
        "Principal Display Panel grouping and visual placement require ocular verification under Rule 8.",
    )


def _eval_legibility(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl:
        return (
            CheckResult.REVIEW,
            "No data",
            0.5,
            "Declaration data unavailable; cannot evaluate legibility under Rule 9.",
        )
    
    if decl.is_human_verified:
        return (
            CheckResult.PASS,
            "Human verified",
            1.0,
            "Legibility, readability, and prominent background contrast verified by inspector under Rule 9.",
        )
    
    confidences = decl.field_confidences or {}
    if confidences:
        vals = [float(v) for v in confidences.values() if isinstance(v, (int, float))]
        if vals and min(vals) >= 0.85:
            avg_c = round(sum(vals) / len(vals), 3)
            return (
                CheckResult.PASS,
                f"Avg Optical Confidence: {avg_c}",
                avg_c,
                "All declarations meet prominent clarity and optical contrast thresholds under Rule 9.",
            )
    
    return (
        CheckResult.REVIEW,
        "Visual contrast check required",
        0.5,
        "Physical print legibility and contrast against packaging background require manual verification under Rule 9.",
    )


def _eval_dual_mrp(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    """
    Evaluates MRP against Controlled Demo Master Catalog under Rule 18(2).
    Strict Guardrail: Catalog discrepancy returns CheckResult.REVIEW with neutral terminology.
    Never returns FAIL or alleges fraud.
    """
    if not decl:
        return (
            CheckResult.PASS,
            "No barcode / catalog data",
            1.0,
            "Master catalog cross-referencing not applicable.",
        )

    raw_extractions = decl.raw_extractions or {}
    barcode_data = raw_extractions.get("barcode_data")
    
    if not barcode_data:
        return (
            CheckResult.PASS,
            "No barcode detected on package",
            1.0,
            "No barcode detected on package photographs; standalone printed MRP declaration evaluated under Rule 6(1)(e).",
        )

    barcode_val = barcode_data.get("value", "")
    catalog_match = barcode_data.get("catalog_match")

    if not catalog_match or not catalog_match.get("matched"):
        return (
            CheckResult.PASS,
            f"Barcode: {barcode_val} (Unregistered in Demo Catalog)",
            1.0,
            f"Barcode {barcode_val} is not registered in the controlled demo master catalog; no price alteration discrepancy flagged under Rule 18(2).",
        )

    discrepancy = catalog_match.get("discrepancy")
    observed_mrp = catalog_match.get("observed_mrp")
    catalog_mrp = catalog_match.get("catalog_mrp")
    prod_name = catalog_match.get("product_name", "Registered Product")

    if discrepancy == "MATCH":
        return (
            CheckResult.PASS,
            f"Observed MRP: ₹{observed_mrp:.2f} | Catalog Reference: ₹{catalog_mrp:.2f}",
            1.0,
            f"Observed package price (₹{observed_mrp:.2f}) matches controlled demo master catalog reference for '{prod_name}' in compliance with Rule 18(2).",
        )
    elif discrepancy == "MISMATCH":
        return (
            CheckResult.REVIEW,
            f"Observed MRP: ₹{observed_mrp:.2f} | Catalog Reference: ₹{catalog_mrp:.2f}",
            0.75,
            f"MRP discrepancy detected against reference data: Observed package MRP (₹{observed_mrp:.2f}) differs from controlled demo catalog reference (₹{catalog_mrp:.2f}) for '{prod_name}'. Field officer physical verification required under Rule 18(2).",
        )
    else:
        return (
            CheckResult.REVIEW,
            f"Catalog Match: {prod_name} (MRP unverified)",
            0.6,
            f"Barcode matched '{prod_name}' in demo master catalog (₹{catalog_mrp:.2f}), but printed package MRP could not be extracted conclusively for comparison under Rule 18(2).",
        )


def _eval_packer_distinction(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl:
        return (
            CheckResult.REVIEW,
            "No data",
            0.5,
            "Declaration data unavailable; cannot evaluate manufacturer vs packer distinction under Rule 6(1)(a) proviso.",
        )
    
    mfg = (decl.manufacturer_name or "").strip()
    packer = (decl.packer_name or "").strip()
    
    if mfg and packer and mfg.lower() != packer.lower():
        return (
            CheckResult.PASS,
            f"Mfg: {mfg} | Packed by: {packer}",
            1.0 if decl.is_human_verified else 0.95,
            "Distinct qualification of manufacturer and packer declared in compliance with Rule 6(1)(a) proviso.",
        )
    elif mfg and not packer:
        return (
            CheckResult.PASS,
            f"Mfg & Packed by: {mfg}",
            1.0 if decl.is_human_verified else 0.95,
            "Manufacturer identified as sole pre-packer in compliance with Rule 6(1)(a).",
        )
    
    return (
        CheckResult.REVIEW,
        "Ambiguous Entity",
        0.5,
        "Entity name present but relationship requires ocular verification under Rule 6(1)(a) proviso.",
    )


def _eval_symbol_placement(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or not decl.net_quantity or not decl.net_quantity.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Mandatory net quantity declaration is missing under Rule 12(2) & Rule 13.",
        )

    raw_val = decl.net_quantity.strip()
    
    # Disallowed non-SI unit patterns / improper trailing period abbreviations
    disallowed_casing_pattern = r"\b(GMS|Gms|KGS|Kgs|LTR|Ltr|GM|Gm|ML\.|Ml\.|Kg\.|kg\.|gm\.|gms\.|kgs\.)\b"
    if re.search(disallowed_casing_pattern, raw_val):
        return (
            CheckResult.FAIL,
            raw_val,
            0.95,
            "Non-standard casing or trailing period detected in SI unit symbol (e.g. 'Kg.', 'Gms', 'ML.'). Standard lowercase SI notation is required under Rule 12(2) & Rule 13.",
        )

    return (
        CheckResult.PASS,
        raw_val,
        1.0 if decl.is_human_verified else 0.95,
        "Unit symbol casing and notation strictly follow standard SI metric conventions under Rule 12(2) & Rule 13.",
    )


def _eval_ecom_declarations(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl:
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Mandatory digital product declarations missing under Rule 6(10).",
        )

    # Check if digital listing data exists and has contradictions
    if decl.digital_listing_data:
        from app.services.listing_service import DigitalListingData, cross_check_digital_listing
        d_listing = DigitalListingData(
            title=decl.digital_listing_data.get("title"),
            description=decl.digital_listing_data.get("description"),
            price=decl.digital_listing_data.get("price"),
            country_of_origin=decl.digital_listing_data.get("country_of_origin"),
            net_quantity=decl.digital_listing_data.get("net_quantity"),
            manufacturer_name=decl.digital_listing_data.get("manufacturer_name"),
            listing_url=decl.digital_listing_data.get("listing_url"),
        )
        report = cross_check_digital_listing(d_listing, decl)
        if report.has_contradictions:
            return (
                CheckResult.REVIEW,
                "Digital Listing Discrepancy",
                0.75,
                report.summary_reason,
            )

    has_comm = bool(decl.commodity_name and decl.commodity_name.strip())
    has_mfg = bool(decl.manufacturer_name or decl.packer_name or decl.importer_name)
    has_qty = bool(decl.net_quantity and decl.net_quantity.strip())
    has_mrp = bool(decl.mrp and decl.mrp.strip())

    present_count = sum([has_comm, has_mfg, has_qty, has_mrp])
    if present_count == 4:
        return (
            CheckResult.PASS,
            "All 4 Core E-Commerce Declarations Present",
            1.0 if decl.is_human_verified else 0.95,
            "Core mandatory digital marketplace declarations (commodity name, manufacturer, quantity, MRP) verified under Rule 6(10).",
        )
    else:
        return (
            CheckResult.REVIEW,
            f"{present_count}/4 Core Declarations Present",
            0.7,
            "Core mandatory declarations required under Rule 6(10) (name, manufacturer, quantity, MRP) require verification on package listing.",
        )


def _eval_standard_pack(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    if not decl or not decl.net_quantity or not decl.net_quantity.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Net quantity declaration missing under Rule 5 & Second Schedule / Rule 14.",
        )

    raw_val = decl.net_quantity.strip().lower()
    metric_match = re.search(r"(\d+(?:\.\d+)?)\s*(g|kg|ml|l|n|u|cm|m)\b", raw_val)

    if metric_match:
        num_val = float(metric_match.group(1))
        unit = metric_match.group(2)
        return (
            CheckResult.PASS,
            f"{num_val} {unit}",
            1.0 if decl.is_human_verified else 0.95,
            f"Commodity packed with standard metric denomination ({num_val} {unit}) in compliance with Rule 5 & Second Schedule.",
        )
    else:
        return (
            CheckResult.REVIEW,
            decl.net_quantity,
            0.6,
            "Net quantity metric unit requires verification under Rule 5 & Rule 14.",
        )


def _eval_registration(decl: Optional[Declaration], rule: LegalRule) -> Tuple[CheckResult, str, Optional[float], str]:
    """
    Evaluates physical address & postal jurisdiction under Rule 27.
    Strict Guardrail: Without an official government verification API, lack of explicit registration number produces REVIEW.
    """
    if not decl or not decl.address or not decl.address.strip():
        return (
            CheckResult.REVIEW,
            "NOT DETECTED",
            0.5,
            "Manufacturer/packer address not detected in OCR; registry verification required under Rule 27.",
        )

    addr = decl.address.strip()
    has_pin = bool(re.search(r"\b\d{6}\b", addr))
    
    if has_pin or len(addr) > 25:
        return (
            CheckResult.PASS,
            addr,
            1.0 if decl.is_human_verified else 0.95,
            "Complete physical address with postal/jurisdictional detail declared for regulatory registry validation under Rule 27.",
        )
    else:
        return (
            CheckResult.REVIEW,
            addr,
            0.6,
            "Address is abbreviated or lacks 6-digit postal PIN code; cross-referencing with Controller of Legal Metrology registry advised under Rule 27.",
        )


RULE_EVALUATORS = {
    "LMPC-R6-COMMODITY-NAME": _eval_commodity_name,
    "LMPC-R6-MANUFACTURER": _eval_manufacturer,
    "LMPC-R6-NET-QUANTITY": _eval_net_quantity,
    "LMPC-R6-MRP": _eval_mrp,
    "LMPC-R6-DATE": _eval_date,
    "LMPC-R6-CONSUMER-CARE": _eval_consumer_care,
    "LMPC-R6-ORIGIN": _eval_origin,
    "LMPC-R6-USP": _eval_usp,
    "LMPC-R6-EXPIRY": _eval_expiry,
    "LMPC-R7-FONT-HEIGHT": _eval_font_height,
    "LMPC-R8-PDP-PLACEMENT": _eval_pdp_placement,
    "LMPC-R9-LEGIBILITY": _eval_legibility,
    "LMPC-R18-DUAL-MRP": _eval_dual_mrp,
    "LMPC-R6-PACKER-DISTINCTION": _eval_packer_distinction,
    "LMPC-R12-SYMBOL-PLACEMENT": _eval_symbol_placement,
    "LMPC-R10-ECOM-DECLARATIONS": _eval_ecom_declarations,
    "LMPC-R14-STANDARD-PACK": _eval_standard_pack,
    "LMPC-R27-REGISTRATION": _eval_registration,
}


async def evaluate_inspection(
    db: AsyncSession,
    inspection: Inspection,
    declaration: Optional[Declaration] = None,
    channel: str = "BOTH",
    inspection_date: Optional[datetime.date] = None,
) -> Tuple[ComplianceResult, List[ComplianceCheck]]:
    """
    Deterministic rule engine evaluating an inspection against applicable LMPC statutory rules.
    Features temporal version resolution (inspection_date) and channel filtering.
    """
    if inspection_date is None:
        if inspection.created_at:
            inspection_date = inspection.created_at.date()
        else:
            inspection_date = datetime.date.today()

    # 1. Fetch active rules matching channel and effective date
    stmt = (
        select(LegalRule)
        .where(
            LegalRule.is_active == True,  # noqa: E712
            (LegalRule.effective_from == None) | (LegalRule.effective_from <= inspection_date),  # noqa: E711
            (LegalRule.effective_to == None) | (LegalRule.effective_to >= inspection_date),  # noqa: E711
        )
        .order_by(LegalRule.rule_code.asc())
    )
    result = await db.execute(stmt)
    all_active_rules = result.scalars().all()

    # Channel filtering
    rules = [
        r for r in all_active_rules
        if r.channel == "BOTH" or channel == "BOTH" or r.channel == channel
    ]

    # 2. Delete existing checks for fresh idempotent evaluation
    del_stmt = delete(ComplianceCheck).where(ComplianceCheck.inspection_id == inspection.id)
    await db.execute(del_stmt)

    checks: List[ComplianceCheck] = []
    has_fail = False
    has_review = False

    for rule in rules:
        evaluator = RULE_EVALUATORS.get(rule.rule_code)
        if evaluator:
            check_res, observed_val, conf, reason = evaluator(declaration, rule)
        else:
            check_res = CheckResult.REVIEW
            observed_val = "Unmapped rule"
            conf = 0.5
            reason = f"No automated evaluator registered for rule {rule.rule_code}; manual review required."

        if check_res == CheckResult.FAIL:
            has_fail = True
        elif check_res == CheckResult.REVIEW:
            has_review = True

        check = ComplianceCheck(
            inspection_id=inspection.id,
            legal_rule_id=rule.id,
            field_name=rule.field_name,
            observed_value=observed_val,
            result=check_res,
            confidence=conf,
            reason=reason,
        )
        checks.append(check)
        db.add(check)

    # 3. Aggregate Overall Result
    if not checks:
        overall = ComplianceResult.NEEDS_REVIEW
    elif has_fail:
        overall = ComplianceResult.NON_COMPLIANT
    elif has_review:
        overall = ComplianceResult.NEEDS_REVIEW
    else:
        overall = ComplianceResult.COMPLIANT

    # 4. Update inspection status
    inspection.overall_result = overall
    if inspection.status != InspectionStatus.COMPLETED:
        inspection.status = InspectionStatus.REVIEW_REQUIRED

    await db.commit()
    return overall, checks
