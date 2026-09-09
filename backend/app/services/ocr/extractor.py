import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.ocr.normalizer import (
    normalize_price_string,
    normalize_quantity_string,
    parse_and_normalize_date,
)
from app.services.ocr.spatial_layout import (
    SpatialBlock,
    SpatialLayoutResult,
    SpatialLine,
    build_spatial_layout,
)
from app.services.ocr.vocabulary import VOCABULARY_DEFINITIONS


DEVANAGARI_DIGITS_MAP = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def translate_devanagari_numerals(text: str) -> str:
    """
    Translates Indic Devanagari numeral characters (०-९) to standard Arabic digits (0-9).
    """
    if not text:
        return text
    result = []
    for ch in text:
        result.append(DEVANAGARI_DIGITS_MAP.get(ch, ch))
    return "".join(result)


def detect_script_language(text: str) -> str:
    """
    Determines whether text is predominantly English, Hindi (Devanagari), or Mixed bilingual.
    """
    if not text:
        return "ENG"
    devanagari_count = len(re.findall(r"[\u0900-\u097F]", text))
    latin_count = len(re.findall(r"[A-Za-z]", text))

    if devanagari_count > 0 and latin_count > 0:
        return "MIXED"
    elif devanagari_count > 0:
        return "HIN"
    else:
        return "ENG"


def extract_mrp(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Maximum Retail Price and tax phrasing in English and Hindi.
    Handles multiline formatting, intervening tax phrasing, and OCR corruption.
    Matches e.g.:
    - MRP Rs. 40.00 incl. of all taxes
    - MRP ₹ 185.00 (inclusive of all taxes)
    - MAXIMUM RETAIL PRICE \n (INCL. OF ALL TAXES) \n Rs. 145.00
    - MAP FY ,499/-
    - अधिकतम खुदरा मूल्य ₹ 50.00 (सभी करों सहित)
    - अ.खु.मू. ₹ ५०.०० (सभी कर सहित)
    """
    if not text:
        return None, None
    norm_text = translate_devanagari_numerals(text)

    # Scoped separator for multiline labels: supports optional colon, optional parenthesized tax header on same or next line
    sep = r"(?:\s*[:.-]?\s*|\s*\([^)\n]+\)\s*|\s*\n\s*\([^)\n]+\)\s*\n\s*|\s+)"

    # 1. Hindi with tax phrasing
    hin_p1 = r"(?i)\b(?:अधिकतम\s*खुदरा\s*मूल्य|अ\.?खु\.?मू\.?|अ०खु०मू०|खुदरा\s*मूल्य|एम\.?आर\.?पी\.?)\b" + sep + r"(?:Rs\.?|₹|INR|रु\.?|रुपये)?\s*([,\.]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)(?!\s*(?:/|per|प्रति)\s*(?:g|ml|kg|l|n|u))\s*([^\n]{0,60}?(?:सभी\s*करों?\s*सहित|कर\s*सहित))"
    m_hin1 = re.search(hin_p1, norm_text)
    if m_hin1:
        p_res = normalize_price_string(m_hin1.group(1))
        val_str = f"{p_res.normalized_value:.2f}" if (p_res.normalized_value is not None and isinstance(p_res.normalized_value, float)) else (str(p_res.normalized_value) if p_res.normalized_value is not None else m_hin1.group(1).replace(",", "").strip())
        return f"MRP Rs. {val_str} incl. of all taxes (अधिकतम खुदरा मूल्य सभी कर सहित)", 0.95

    # 2. English with tax phrasing (multiline resilient)
    p1 = r"(?i)\b(?:MRP|M\.R\.P\.?|M\s*R\s*P|Maximum\s*Retail\s*Price|Max\.?\s*Retail\s*Price|Retail\s*Price)\b" + sep + r"(?:Rs\.?|₹|INR|FY|¢)?\s*([,\.]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)(?!\s*(?:/|per|प्रति)\s*(?:g|ml|kg|l|n|u))\s*([^\n]{0,60}?(?:(?:incl|inclusive)\s*(?:of)?\s*all\s*taxes|incl\.?\s*of\s*all\s*taxes|\(incl.*?taxes\)))"
    m1 = re.search(p1, norm_text)
    if m1:
        p_res = normalize_price_string(m1.group(1))
        val_str = f"{p_res.normalized_value:.2f}" if (p_res.normalized_value is not None and isinstance(p_res.normalized_value, float)) else (str(p_res.normalized_value) if p_res.normalized_value is not None else m1.group(1).replace(",", "").strip())
        tax_part = m1.group(2).strip()
        tax_clean = re.sub(r"\s+", " ", tax_part)
        return f"MRP Rs. {val_str} {tax_clean}".strip(), 0.95

    # 3. Dedicated OCR misread pattern for 'MAP' on packaging
    p_map = r"(?i)\bMAP\s*[:.-]?\s*(?:Rs\.?|₹|INR|FY|¢|¥|\d)?\s*([,\.]?\s*\d{1,3}(?:[\s,]\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)\s*(?:/-)?"
    m_map = re.search(p_map, norm_text)
    if m_map:
        raw_val = m_map.group(1).replace(" ", ",")
        p_res = normalize_price_string(raw_val)
        if p_res.normalized_value and p_res.normalized_value >= 1.0:
            val_str = f"{p_res.normalized_value:.2f}" if isinstance(p_res.normalized_value, float) else str(p_res.normalized_value)
            return f"MRP Rs. {val_str}", 0.85

    # 4. Hindi without tax phrasing
    hin_p2 = r"(?i)\b(?:अधिकतम\s*खुदरा\s*मूल्य|अ\.?खु\.?मू\.?|अ०खु०मू०|खुदरा\s*मूल्य|एम\.?आर\.?पी\.?)\b" + sep + r"(?:Rs\.?|₹|INR|रु\.?|रुपये)?\s*([,\.]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)(?!\s*(?:/|per|प्रति)\s*(?:g|ml|kg|l|n|u))"
    m_hin2 = re.search(hin_p2, norm_text)
    if m_hin2:
        p_res = normalize_price_string(m_hin2.group(1))
        val_str = f"{p_res.normalized_value:.2f}" if (p_res.normalized_value is not None and isinstance(p_res.normalized_value, float)) else (str(p_res.normalized_value) if p_res.normalized_value is not None else m_hin2.group(1).replace(",", "").strip())
        if re.search(r"(?i)(?:सभी\s*करों?\s*सहित|कर\s*सहित|(?:incl|inclusive)\s*(?:of)?\s*all\s*taxes)", norm_text):
            return f"MRP Rs. {val_str} incl. of all taxes", 0.90
        return f"MRP Rs. {val_str}", 0.85

    # 5. English without tax phrasing (multiline resilient)
    p2 = r"(?i)\b(?:MRP|M\.R\.P\.?|M\s*R\s*P|Maximum\s*Retail\s*Price|Max\.?\s*Retail\s*Price|Retail\s*Price)\b" + sep + r"(?:Rs\.?|₹|INR|FY|¢)?\s*([,\.]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|[,\.]?\s*\d+(?:\.\d{1,2})?)(?!\s*(?:/|per|प्रति)\s*(?:g|ml|kg|l|n|u))"
    m2 = re.search(p2, norm_text)
    if m2:
        p_res = normalize_price_string(m2.group(1))
        val_str = f"{p_res.normalized_value:.2f}" if (p_res.normalized_value is not None and isinstance(p_res.normalized_value, float)) else (str(p_res.normalized_value) if p_res.normalized_value is not None else m2.group(1).replace(",", "").strip())
        if re.search(r"(?i)(?:incl|inclusive)\s*(?:of)?\s*all\s*taxes|सभी\s*करों?\s*सहित", norm_text):
            return f"MRP Rs. {val_str} incl. of all taxes", 0.90
        return f"MRP Rs. {val_str}", 0.85

    return None, None


def _clean_quantity_val(val: str) -> str:
    """Helper to clean OCR homoglyphs and translate Hindi unit names while preserving raw unit."""
    val = val.strip()
    val = re.sub(r"ग्राम", "g", val)
    val = re.sub(r"किग्रा", "kg", val)
    val = re.sub(r"मिली", "ml", val)
    val = re.sub(r"लीटर", "l", val)
    val = re.sub(r"(?<=[0-9])[Oo]+(?=[Oo0-9]*\s*(?:g|kg|ml|l|mg|n|u))", lambda m: "0" * len(m.group(0)), val)
    val = re.sub(r"(?i)\bk9\b", "kg", val)
    val = re.sub(r"(?i)\bgms\b", "g", val)
    val = re.sub(r"(?i)\bgm\b", "g", val)
    val = re.sub(r"(?i)\bkgs\b", "kg", val)
    val = re.sub(r"(?i)\bltr\b", "l", val)
    val = re.sub(r",", "", val)
    return val


def extract_net_quantity(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Net Quantity in English and Hindi units.
    Handles multiline formatting, OCR homoglyphs ('1 k9', '1OOO g'), and
    disambiguates from nutritional serving sizes (e.g. 'per 30g', 'serving size: 32g').
    """
    if not text:
        return None, None
    norm_text = translate_devanagari_numerals(text)

    # 1. Hindi Net Quantity with explicit label
    hin_p1 = r"(?i)(?:शुद्ध\s*मात्रा|नेट\s*मात्रा|मात्रा|शुद्ध\s*वजन|नेट\s*वजन)\s*[:.-]?\s*([Oo0-9,\.]+\s*(?:g|kg|ml|l|mg|n|u|ग्राम|किग्रा|मिली|लीटर))(?:\b|\s|$)"
    m_hin1 = re.search(hin_p1, norm_text)
    if m_hin1:
        val = _clean_quantity_val(m_hin1.group(1))
        return val, 0.92

    # 2. English Net Quantity with explicit label (multiline resilient)
    p1 = r"(?i)\b(?:Net\s*(?:Qty|Quantity|Wt|Weight|Volume|Content|Contents)?)\s*[:.-]?\s*([Oo0-9,\.]+\s*(?:g|kg|ml|l|mg|n|u|cm|m|gms|kgs|ltr|gm|ml\.|k9))\b"
    m1 = re.search(p1, norm_text, re.DOTALL)
    if m1:
        val = _clean_quantity_val(m1.group(1))
        return val, 0.92

    # 3. Fallback: isolated quantity pattern, strictly filtering out serving size context
    p2 = r"\b([Oo0-9,\.]+\s*(?:g|kg|ml|l|mg|gms|kgs|ltr|k9))\b"
    for match in re.finditer(p2, norm_text, re.IGNORECASE):
        start_idx = max(0, match.start() - 25)
        prefix = norm_text[start_idx:match.start()].lower()
        if any(ign in prefix for ign in ("per", "serving", "approx", "protein", "carb", "fat", "sugar", "energy")):
            continue
        val = _clean_quantity_val(match.group(1))
        return val, 0.75

    return None, None


def extract_dates(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts Manufacturing Date, Packing Date, Expiry Date, and Best Before in English and Hindi.
    Supports DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD MMM YYYY, MMM YYYY, MM/YYYY.
    """
    if not text:
        return None, None, None, None, None
    norm_text = translate_devanagari_numerals(text)
    mfg_date = None
    pkd_date = None
    exp_date = None
    best_before = None
    conf = None

    date_regex = (
        r"("
        r"\b(?:0[1-9]|[12]\d|3[01])[/\-\.](?:0[1-9]|1[0-2])[/\-\.](?:20\d{2}|\d{2})\b|"
        r"\b(?:0[1-9]|[12]\d|3[01])[\s/\-\.](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s/\-\.](?:20\d{2}|\d{2})\b|"
        r"\b(?:0[1-9]|1[0-2])[/\-\.](?:20\d{2}|\d{2})\b|"
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s/\-\.](?:20\d{2}|\d{2})\b|"
        r"\b(?:20\d{2})[/\-\.](?:0[1-9]|1[0-2])\b"
        r")"
    )

    # Manufacturing date
    mfg_m = re.search(r"(?i)\b(?:Mfd|Mfg|Manufactured|Mfg\s*Date|Mfd\s*Date|Date\s*of\s*Mfg|Date\s*of\s*Manufacture|निर्माण\s*तिथि|उत्पादन\s*तिथि)\s*[:.-]?\s*" + date_regex, norm_text)
    if mfg_m:
        raw_dt = mfg_m.group(1).strip()
        norm_dt = parse_and_normalize_date(raw_dt)
        mfg_date = norm_dt.raw_date if norm_dt else raw_dt
        conf = 0.90

    # Packing date
    pkd_m = re.search(r"(?i)\b(?:PKD|Packed|Pack|Pkg|Packed\s*on|Date\s*of\s*Packing|पैकिंग\s*तिथि|पैक\s*तिथि)\s*[:.-]?\s*" + date_regex, norm_text)
    if pkd_m:
        raw_dt = pkd_m.group(1).strip()
        norm_dt = parse_and_normalize_date(raw_dt)
        pkd_date = norm_dt.raw_date if norm_dt else raw_dt
        if not mfg_date:
            mfg_date = pkd_date
        conf = 0.90

    # Expiry date
    exp_m = re.search(r"(?i)\b(?:Use\s*by|Expiry|Exp\s*Date|Exp|अवसान\s*तिथि|समाप्ति\s*तिथि|उपयोग\s*की\s*अंतिम\s*तिथि)\s*[:.-]?\s*" + date_regex, norm_text)
    if exp_m:
        raw_dt = exp_m.group(1).strip()
        norm_dt = parse_and_normalize_date(raw_dt)
        exp_date = norm_dt.raw_date if norm_dt else raw_dt
        conf = 0.90

    # Best before
    bb_m = re.search(r"(?i)\b(?:Best\s*Before|Best\s*By|सर्वोत्तम\s*उपयोग)\s*[:.-]?\s*([^\n,]+)", norm_text)
    if bb_m:
        best_before = bb_m.group(1).strip()
        conf = 0.85

    return mfg_date, pkd_date, exp_date, best_before, conf


def extract_consumer_care(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts consumer grievance phone, email, and care block in English and Hindi.
    """
    if not text:
        return None, None, None, None
    norm_text = translate_devanagari_numerals(text)
    phone = None
    email = None
    care_block = None
    conf = None

    phone_m = re.search(r"\b(1800[-\s]?\d{3}[-\s]?\d{3,4}|\+?91[-\s]?\d{10}|\b\d{3,5}[-\s]\d{6,8})\b", norm_text)
    if phone_m:
        phone = phone_m.group(1).strip()
        conf = 0.92

    email_m = re.search(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", norm_text)
    if email_m:
        email = email_m.group(1).strip()
        conf = 0.95

    care_m = re.search(r"(?i)(?:Consumer\s*Care|Customer\s*Care|Helpline|Grievance\s*Cell|उपभोक्ता\s*सेवा|ग्राहक\s*सेवा|शिकायत\s*निवारण)\s*[:.-]?\s*([^\n]+(?:\n[^\n]+)?)", norm_text)
    if care_m:
        care_block = care_m.group(0).strip()
        conf = 0.88
    elif phone or email:
        care_block = f"Phone: {phone or 'N/A'}, Email: {email or 'N/A'}"

    return phone, email, care_block, conf


def extract_manufacturer_and_address(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts manufacturer, packer, importer name, and address in English and Hindi.
    Tolerates common OCR keyword variations.
    """
    if not text:
        return None, None, None, None, None
    norm_text = translate_devanagari_numerals(text)
    mfg_name = None
    packer_name = None
    importer_name = None
    address = None
    conf = None

    lines = [line.strip() for line in norm_text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if re.search(r"(?i)\b(?:Mfg(?:\.|\s*by)?|Manufactur[a-z]{0,4}\s*by|Mfd(?:\.|\s*by)?|द्वारा\s*निर्मित|निर्माता)\b", line):
            mfg_name = re.sub(r"(?i)\b(?:Mfg(?:\.|\s*by)?|Manufactur[a-z]{0,4}\s*by|Mfd(?:\.|\s*by)?|द्वारा\s*निर्मित|निर्माता)\s*[:.-]?", "", line).strip()
            if not mfg_name and i + 1 < len(lines):
                mfg_name = lines[i + 1]
            conf = 0.88

        elif re.search(r"(?i)\b(?:Packed\s*by|Pack[a-z]{0,3}\s*by|Pkd(?:\.|\s*by)?|द्वारा\s*पैक|पैकर)\b", line):
            packer_name = re.sub(r"(?i)\b(?:Packed\s*by|Pack[a-z]{0,3}\s*by|Pkd(?:\.|\s*by)?|द्वारा\s*पैक|पैकर)\s*[:.-]?", "", line).strip()
            if not packer_name and i + 1 < len(lines):
                packer_name = lines[i + 1]
            conf = 0.88

        elif re.search(r"(?i)\b(?:Imported\s*by|Import[a-z]{0,3}\s*by|Imp(?:\.|\s*by)?|आयातकर्ता)\b", line):
            importer_name = re.sub(r"(?i)\b(?:Imported\s*by|Import[a-z]{0,3}\s*by|Imp(?:\.|\s*by)?|आयातकर्ता)\s*[:.-]?", "", line).strip()
            if not importer_name and i + 1 < len(lines):
                importer_name = lines[i + 1]
            conf = 0.88

        if re.search(r"(?i)\b(?:Plot|Street|Road|Estate|Phase|Sector|Industrial\s*Area|Pin\s*Code|Pincode|पता|पिन\s*कोड|\b\d{6}\b)\b", line):
            if not address:
                address = line
            else:
                address += f", {line}"
            conf = 0.85

    return mfg_name, packer_name, importer_name, address, conf


def extract_unit_sale_price(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Unit Sale Price (USP) in English and Hindi.
    Handles OCR homoglyphs like '¢4.88/q' -> 'Rs. 4.88 / g'.
    """
    if not text:
        return None, None
    norm_text = translate_devanagari_numerals(text)
    norm_text = re.sub(r"[¢¥]", "Rs.", norm_text)
    norm_text = re.sub(r"(?i)\bFY\b", "Rs.", norm_text)

    p = r"(?i)\b(?:USP|U\.S\.P\.?|Unit\s*Sale\s*Price|प्रति\s*इकाई\s*मूल्य|इकाई\s*मूल्य)\s*[:.-]?\s*(?:Rs\.?|₹|रु\.?)?\s*(\d+(?:\.\d{1,2})?\s*(?:/|per|प्रति)\s*(?:g|kg|ml|l|q|9|item|piece|N|u|ग्राम|किग्रा|मिली|लीटर))\b"
    m = re.search(p, norm_text)
    if m:
        raw_val = m.group(1).strip()
        raw_val = re.sub(r"/\s*[q9]\b", "/g", raw_val)
        raw_val = re.sub(r"per\s*[q9]\b", "per g", raw_val)
        return f"Rs. {raw_val}", 0.90

    return None, None


extract_usp = extract_unit_sale_price


def extract_origin(text: str) -> Tuple[Optional[str], bool, Optional[float]]:
    """
    Extracts Country of Origin and is_imported boolean in English and Hindi.
    """
    if not text:
        return None, False, None
    norm_text = translate_devanagari_numerals(text)
    p = r"(?i)\b(?:Country\s*of\s*Origin|Made\s*in|Product\s*of|Origin|मूल\s*देश|उत्पत्ति\s*देश|उत्पादक\s*देश)\s*[:.-]?\s*([A-Za-z\u0900-\u097F ]+)"
    m = re.search(p, norm_text)
    if m:
        country = m.group(1).strip()
        is_imported = country.lower() not in ("india", "bharat", "domestic", "भारत", "स्वदेशी")
        return country, is_imported, 0.92

    if re.search(r"(?i)\b(?:Imported\s*by|Imp\s*by|Importer|आयातकर्ता)\b", norm_text):
        return None, True, 0.80

    return None, False, None


def extract_commodity_name(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts commodity name in English and Hindi safely.
    Eliminates unsafe arbitrary first-line fallback to prevent noise pollution.
    """
    if not text:
        return None, None
    norm_text = translate_devanagari_numerals(text)

    # 1. Explicit keyword match
    p = r"(?i)\b(?:Product(?:\s*Name)?|Item(?:\s*Name)?|Commodity(?:\s*Name)?|Generic\s*Name|उत्पाद(?:\s*का\s*नाम)?|सामग्री|वस्तु)\s*[:.-]?\s*([^\n\r]+)"
    m = re.search(p, norm_text)
    if m:
        candidate = m.group(1).strip()
        # Clean candidate: stop at subsequent keywords
        candidate = re.split(r"(?i)\b(?:mrp|net|mfd|exp|batch|lic|pkd)\b", candidate)[0].strip(" :-.,")
        if len(candidate) > 2:
            return candidate, 0.90

    # 2. Contextual check: Do NOT use first line if it looks like a header, address, care line, or company name
    return None, None


def extract_declaration_from_ocr(
    raw_text: str, tokens_data: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Deterministic extraction pipeline converting raw OCR text and tokens into
    structured LMPC 2011 declarations with 2D spatial layout resolution and
    bilingual English/Hindi Indic awareness.
    """
    extracted_fields: Dict[str, Any] = {}
    field_confidences: Dict[str, float] = {}

    # Build 2D spatial layout if tokens_data is provided
    spatial_layout = build_spatial_layout(tokens_data)

    if not raw_text or not raw_text.strip():
        if spatial_layout.full_text:
            raw_text = spatial_layout.full_text
        else:
            return extracted_fields, field_confidences

    # Language/Script detection
    script_lang = detect_script_language(raw_text)
    extracted_fields["_language_detected"] = script_lang

    block_texts = spatial_layout.get_blocks_text() if spatial_layout.blocks else []
    # Combined text corpus: raw_text plus structured spatial blocks
    corpus_to_search = [raw_text] + block_texts

    # 1. Commodity Name (safe extraction without arbitrary first-line fallback)
    comm_name = None
    comm_conf = None
    for corpus in corpus_to_search:
        comm_name, comm_conf = extract_commodity_name(corpus)
        if comm_name:
            break
    if comm_name:
        extracted_fields["commodity_name"] = comm_name
        if comm_conf is not None:
            field_confidences["commodity_name"] = comm_conf

    # 2. Manufacturer, Packer, Importer, Address
    mfg_name = None
    pkr_name = None
    imp_name = None
    addr = None
    mfg_conf = None
    for corpus in corpus_to_search:
        m, p, i, a, c = extract_manufacturer_and_address(corpus)
        if not mfg_name and m:
            mfg_name = m
            mfg_conf = c
        if not pkr_name and p:
            pkr_name = p
            mfg_conf = c
        if not imp_name and i:
            imp_name = i
            mfg_conf = c
        if not addr and a:
            addr = a
            mfg_conf = c

    if mfg_name:
        extracted_fields["manufacturer_name"] = mfg_name
        if mfg_conf:
            field_confidences["manufacturer_name"] = mfg_conf
    if pkr_name:
        extracted_fields["packer_name"] = pkr_name
        if mfg_conf:
            field_confidences["packer_name"] = mfg_conf
    if imp_name:
        extracted_fields["importer_name"] = imp_name
        if mfg_conf:
            field_confidences["importer_name"] = mfg_conf
    if addr:
        extracted_fields["address"] = addr
        if mfg_conf:
            field_confidences["address"] = mfg_conf

    # 3. Net Quantity (incorporating spatial block downward pairing)
    net_qty = None
    qty_conf = None
    for corpus in corpus_to_search:
        net_qty, qty_conf = extract_net_quantity(corpus)
        if net_qty:
            break

    # Spatial downward association for Net Quantity if not found
    if not net_qty and spatial_layout.blocks:
        for block in spatial_layout.blocks:
            for idx, line in enumerate(block.lines):
                if re.search(r"(?i)\b(?:Net\s*(?:Quantity|Qty|Wt|Weight)?|शुद्ध\s*मात्रा)\b", line.text):
                    if idx + 1 < len(block.lines):
                        cand_text = block.lines[idx + 1].text
                        q_cand, c_cand = extract_net_quantity(cand_text)
                        if q_cand:
                            net_qty = q_cand
                            qty_conf = 0.90
                            break
            if net_qty:
                break

    if net_qty:
        extracted_fields["net_quantity"] = net_qty
        if qty_conf is not None:
            field_confidences["net_quantity"] = qty_conf

    # 4. MRP (incorporating multiline regex and spatial downward association)
    mrp = None
    mrp_conf = None
    for corpus in corpus_to_search:
        mrp, mrp_conf = extract_mrp(corpus)
        if mrp:
            break

    # Spatial downward association for MRP if not found
    if not mrp and spatial_layout.blocks:
        for block in spatial_layout.blocks:
            for idx, line in enumerate(block.lines):
                if re.search(r"(?i)\b(?:MRP|M\.R\.P\.?|Maximum\s*Retail\s*Price|अधिकतम\s*खुदरा\s*मूल्य)\b", line.text):
                    for offset in (1, 2):
                        if idx + offset < len(block.lines):
                            cand_line = block.lines[idx + offset].text
                            combined = f"{line.text}\n{cand_line}"
                            m_cand, c_cand = extract_mrp(combined)
                            if m_cand:
                                mrp = m_cand
                                mrp_conf = 0.90
                                break
                    if mrp:
                        break
            if mrp:
                break

    if mrp:
        extracted_fields["mrp"] = mrp
        if mrp_conf is not None:
            field_confidences["mrp"] = mrp_conf

    # 5. Dates
    mfg_dt = None
    pkd_dt = None
    exp_dt = None
    bb = None
    dt_conf = None
    for corpus in corpus_to_search:
        m, p, e, b, c = extract_dates(corpus)
        if not mfg_dt and m:
            mfg_dt = m
            dt_conf = c
        if not pkd_dt and p:
            pkd_dt = p
            dt_conf = c
        if not exp_dt and e:
            exp_dt = e
            dt_conf = c
        if not bb and b:
            bb = b
            dt_conf = c

    if mfg_dt:
        extracted_fields["manufacturing_date"] = mfg_dt
        if dt_conf:
            field_confidences["manufacturing_date"] = dt_conf
    if pkd_dt:
        extracted_fields["packing_date"] = pkd_dt
        if dt_conf:
            field_confidences["packing_date"] = dt_conf
    if exp_dt:
        extracted_fields["expiry_date"] = exp_dt
        if dt_conf:
            field_confidences["expiry_date"] = dt_conf
    if bb:
        extracted_fields["best_before"] = bb
        if dt_conf:
            field_confidences["best_before"] = dt_conf

    # 6. Consumer Care
    phone = None
    email = None
    care_block = None
    care_conf = None
    for corpus in corpus_to_search:
        p, e, cb, c = extract_consumer_care(corpus)
        if not phone and p:
            phone = p
            care_conf = c
        if not email and e:
            email = e
            care_conf = c
        if not care_block and cb:
            care_block = cb
            care_conf = c

    if phone:
        extracted_fields["consumer_care_phone"] = phone
        if care_conf:
            field_confidences["consumer_care_phone"] = care_conf
    if email:
        extracted_fields["consumer_care_email"] = email
        if care_conf:
            field_confidences["consumer_care_email"] = care_conf
    if care_block:
        extracted_fields["consumer_care"] = care_block
        if care_conf:
            field_confidences["consumer_care"] = care_conf

    # 7. Unit Sale Price
    usp = None
    usp_conf = None
    for corpus in corpus_to_search:
        usp, usp_conf = extract_unit_sale_price(corpus)
        if usp:
            break
    if usp:
        extracted_fields["unit_sale_price"] = usp
        if usp_conf is not None:
            field_confidences["unit_sale_price"] = usp_conf

    # 8. Origin
    origin = None
    is_imp = False
    orig_conf = None
    for corpus in corpus_to_search:
        o, imp, c = extract_origin(corpus)
        if not origin and o:
            origin = o
            orig_conf = c
        if imp:
            is_imp = True
    if origin:
        extracted_fields["country_of_origin"] = origin
        if orig_conf:
            field_confidences["country_of_origin"] = orig_conf
    extracted_fields["is_imported"] = is_imp

    return extracted_fields, field_confidences
