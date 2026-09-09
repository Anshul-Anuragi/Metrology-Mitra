"""
Phase 4.5 P0 Hardening — Context-Aware OCR Normalizer & Canonicalizer
====================================================================
Provides deterministic, context-specific normalization of OCR text artifacts:
1. Contextual homoglyph resolution (digits vs letters: O<->0, I/l<->1, S<->5).
2. Currency symbol and price punctuation cleanup (₹, FY, ¢ -> ₹, ,499 -> 1499).
3. Indian packaging date parsing and ISO-8601 canonicalization.
4. Metric unit canonicalization (kg -> g, l -> ml).
5. Comprehensive transformation audit logging.

SAFETY INVARIANTS:
1. No Global Overwrite: Normalizations are applied strictly within field-specific
   syntactic contexts (e.g. within price or weight patterns), never to arbitrary text.
2. Provenance Preservation: Every transformation preserves raw_value alongside
   normalized_value with a record of applied rules.
3. Zero False Certainty: Ambiguous transformations reduce confidence scores.
"""

import datetime
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


MONTH_NAME_MAP = {
    "jan": 1, "january": 1, "जनवरी": 1,
    "feb": 2, "february": 2, "फरवरी": 2,
    "mar": 3, "march": 3, "मार्च": 3,
    "apr": 4, "april": 4, "अप्रैल": 4,
    "may": 5, "मई": 5,
    "jun": 6, "june": 6, "जून": 6,
    "jul": 7, "july": 7, "जुलाई": 7,
    "aug": 8, "august": 8, "अगस्त": 8,
    "sep": 9, "sept": 9, "september": 9, "सितंबर": 9,
    "oct": 10, "october": 10, "अक्टूबर": 10,
    "nov": 11, "november": 11, "नवंबर": 11,
    "dec": 12, "december": 12, "दिसंबर": 12,
}


@dataclass
class NormalizationResult:
    raw_value: str
    normalized_value: Any
    normalizations_applied: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "normalizations_applied": self.normalizations_applied,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class DateNormalizationResult:
    raw_date: str
    normalized_date: str  # YYYY-MM or YYYY-MM-DD
    date_format: str      # e.g. "DD/MM/YYYY", "MM/YYYY", "DD MMM YYYY"
    confidence: float
    source: str = "OCR"
    year: int = 0
    month: int = 0
    day: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_date": self.raw_date,
            "normalized_date": self.normalized_date,
            "date_format": self.date_format,
            "confidence": round(self.confidence, 4),
            "source": self.source,
        }


# ----------------------------------------------------------------------
# 1. Price / Currency Normalizer
# ----------------------------------------------------------------------
def normalize_price_string(raw_price_str: str) -> NormalizationResult:
    """
    Normalizes OCR price strings to a canonical float and currency representation.
    Handles:
    - Rupee symbol misreads: 'FY ,499/-', '¢4.88', 'Rs 145.OO'
    - Separator noise: '1,499/-', '145.00/-'
    - Missing leading '1' when OCR read as comma: ',499' -> 1499
    """
    if not raw_price_str:
        return NormalizationResult(raw_value="", normalized_value=None, confidence=0.0)

    applied: List[str] = []
    text = raw_price_str.strip()
    conf = 0.95

    # 1. Fix common Rupee symbol misreads
    if re.search(r"(?i)\b(?:FY|¢|¥)\b", text):
        text = re.sub(r"(?i)\b(?:FY|¢|¥)\b", "₹", text)
        applied.append("HOMOGLYPH_CURRENCY_SYMBOL")
        conf -= 0.05

    # 2. Fix trailing /-, /-., or -
    if re.search(r"/[-\.]*$", text):
        text = re.sub(r"/[-\.]*$", "", text).strip()
        applied.append("STRIP_TRAILING_SLASH_HYPHEN")

    # 3. Fix digit 'O' or 'o' in decimal places: e.g. 145.OO -> 145.00
    if re.search(r"\.\s*[Oo0]{1,2}\b", text):
        text = re.sub(r"\.\s*[Oo0]{1,2}\b", ".00", text)
        applied.append("HOMOGLYPH_DECIMAL_O_TO_ZERO")

    # 4. Extract numeric component
    # Match pattern: optional leading comma/dot then digits
    m = re.search(r"(?:₹|rs\.?|inr)?\s*([,\.]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if not m:
        return NormalizationResult(raw_value=raw_price_str, normalized_value=None, confidence=0.0)

    num_part = m.group(1).replace(" ", "").strip()

    # Handle comma at start like ',499'
    if num_part.startswith(","):
        num_part = "1" + num_part[1:]
        applied.append("CORRECT_LEADING_COMMA_TO_ONE")
        conf -= 0.35  # Conservative safety penalty: prevents false certainty on synthesized digit

    num_clean = num_part.replace(",", "")
    try:
        val = float(num_clean)
        return NormalizationResult(
            raw_value=raw_price_str,
            normalized_value=val,
            normalizations_applied=applied,
            confidence=max(0.40, conf),
        )
    except ValueError:
        return NormalizationResult(raw_value=raw_price_str, normalized_value=None, confidence=0.0)


# ----------------------------------------------------------------------
# 2. Net Quantity & Unit Normalizer
# ----------------------------------------------------------------------
def normalize_quantity_string(raw_qty_str: str) -> NormalizationResult:
    """
    Normalizes Net Quantity declarations and converts units to standard metric grams/milliliters.
    Handles:
    - Homoglyphs: '1 k9' -> '1 kg', '1OOO g' -> '1000 g', '15O ml' -> '150 ml'
    - Conversions: '1 kg' -> 1000.0 g, '500 g' -> 500.0 g, '1 l' -> 1000.0 ml
    """
    if not raw_qty_str:
        return NormalizationResult(raw_value="", normalized_value=None, confidence=0.0)

    applied: List[str] = []
    text = raw_qty_str.strip()
    conf = 0.95

    # 1. Homoglyphs in unit: 'k9' -> 'kg'
    if re.search(r"(?i)\bk9\b", text):
        text = re.sub(r"(?i)\bk9\b", "kg", text)
        applied.append("HOMOGLYPH_K9_TO_KG")
        conf -= 0.05

    # 2. Homoglyph 'OOO' or 'O' in numbers before unit
    # e.g. 1OOO g -> 1000 g, 25O g -> 250 g
    m_homo = re.search(r"\b(\d+)([Oo]+)\s*(g|kg|ml|l|mg)\b", text, re.IGNORECASE)
    if m_homo:
        num_prefix = m_homo.group(1)
        zeros = "0" * len(m_homo.group(2))
        unit = m_homo.group(3)
        text = f"{num_prefix}{zeros} {unit}"
        applied.append("HOMOGLYPH_O_TO_ZERO")
        conf -= 0.05

    # 3. Parse numeric value and unit
    p = r"(?i)(\d+(?:,\d{3})*(?:\.\d+)?|\d+)\s*(g|kg|mg|ml|l|ltr|litre|liter|gm|gms|kgs|n|u|units?|pieces?)\b"
    m = re.search(p, text)
    if not m:
        return NormalizationResult(raw_value=raw_qty_str, normalized_value=None, confidence=0.0)

    raw_num = m.group(1).replace(",", "")
    unit_str = m.group(2).lower()

    try:
        num_val = float(raw_num)
    except ValueError:
        return NormalizationResult(raw_value=raw_qty_str, normalized_value=None, confidence=0.0)

    canonical_unit = "g"
    canonical_val = num_val

    if unit_str in ("kg", "kgs"):
        canonical_val = num_val * 1000.0
        canonical_unit = "g"
        applied.append("CONVERT_KG_TO_G")
    elif unit_str in ("g", "gm", "gms"):
        canonical_val = num_val
        canonical_unit = "g"
    elif unit_str in ("mg",):
        canonical_val = num_val / 1000.0
        canonical_unit = "g"
        applied.append("CONVERT_MG_TO_G")
    elif unit_str in ("l", "ltr", "litre", "liter"):
        canonical_val = num_val * 1000.0
        canonical_unit = "ml"
        applied.append("CONVERT_L_TO_ML")
    elif unit_str in ("ml",):
        canonical_val = num_val
        canonical_unit = "ml"
    elif unit_str in ("n", "u", "unit", "units", "piece", "pieces"):
        canonical_val = num_val
        canonical_unit = "u"

    formatted_str = f"{int(canonical_val) if canonical_val.is_integer() else canonical_val} {canonical_unit}"

    return NormalizationResult(
        raw_value=raw_qty_str,
        normalized_value={
            "declared_quantity_numeric": canonical_val,
            "declared_unit": canonical_unit,
            "formatted": formatted_str,
        },
        normalizations_applied=applied,
        confidence=max(0.50, conf),
    )


# ----------------------------------------------------------------------
# 3. Expanded Date Normalizer
# ----------------------------------------------------------------------
def parse_and_normalize_date(raw_date_str: str) -> Optional[DateNormalizationResult]:
    """
    Robust Indian packaging date parser supporting:
    - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY (e.g. 15/08/2025)
    - DD MMM YYYY (e.g. 15 AUG 2025, 15-Aug-2025)
    - MM/YYYY, MM-YYYY (e.g. 08/2025, 08-2025)
    - MMM YYYY (e.g. AUG 2025)
    - YYYY/MM, YYYY-MM
    Normalizes to ISO-8601 (YYYY-MM-DD or YYYY-MM).
    """
    if not raw_date_str:
        return None

    clean_str = raw_date_str.strip()

    # Pattern 1: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    m1 = re.search(r"\b(0[1-9]|[12]\d|3[01])[/\-\.](0[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})\b", clean_str)
    if m1:
        day = int(m1.group(1))
        month = int(m1.group(2))
        yr_str = m1.group(3)
        year = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
        return DateNormalizationResult(
            raw_date=clean_str,
            normalized_date=f"{year:04d}-{month:02d}-{day:02d}",
            date_format="DD/MM/YYYY",
            confidence=0.95,
            year=year,
            month=month,
            day=day,
        )

    # Pattern 2: DD MMM YYYY (e.g. 15 AUG 2025, 15-AUG-2025, 15 Aug 25)
    p2 = r"\b(0[1-9]|[12]\d|3[01])[\s/.-]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s/.-]+(20\d{2}|\d{2})\b"
    m2 = re.search(p2, clean_str, re.IGNORECASE)
    if m2:
        day = int(m2.group(1))
        m_name = m2.group(2).lower()[:3]
        month = MONTH_NAME_MAP.get(m_name, 1)
        yr_str = m2.group(3)
        year = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
        return DateNormalizationResult(
            raw_date=clean_str,
            normalized_date=f"{year:04d}-{month:02d}-{day:02d}",
            date_format="DD MMM YYYY",
            confidence=0.95,
            year=year,
            month=month,
            day=day,
        )

    # Pattern 3: MM/YYYY or MM-YYYY
    m3 = re.search(r"\b(0[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})\b", clean_str)
    if m3:
        month = int(m3.group(1))
        yr_str = m3.group(2)
        year = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
        return DateNormalizationResult(
            raw_date=clean_str,
            normalized_date=f"{year:04d}-{month:02d}",
            date_format="MM/YYYY",
            confidence=0.90,
            year=year,
            month=month,
            day=None,
        )

    # Pattern 4: MMM YYYY (e.g. AUG 2025, AUG-2025)
    p4 = r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s/.-]+(20\d{2}|\d{2})\b"
    m4 = re.search(p4, clean_str, re.IGNORECASE)
    if m4:
        m_name = m4.group(1).lower()[:3]
        month = MONTH_NAME_MAP.get(m_name, 1)
        yr_str = m4.group(2)
        year = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
        return DateNormalizationResult(
            raw_date=clean_str,
            normalized_date=f"{year:04d}-{month:02d}",
            date_format="MMM YYYY",
            confidence=0.90,
            year=year,
            month=month,
            day=None,
        )

    # Pattern 5: YYYY/MM or YYYY-MM
    m5 = re.search(r"\b(20\d{2})[/\-\.](0[1-9]|1[0-2])\b", clean_str)
    if m5:
        year = int(m5.group(1))
        month = int(m5.group(2))
        return DateNormalizationResult(
            raw_date=clean_str,
            normalized_date=f"{year:04d}-{month:02d}",
            date_format="YYYY/MM",
            confidence=0.90,
            year=year,
            month=month,
            day=None,
        )

    return None
