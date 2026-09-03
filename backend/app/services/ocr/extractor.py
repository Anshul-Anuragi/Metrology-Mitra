import re
from typing import Any, Dict, List, Optional, Tuple


def extract_mrp(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Maximum Retail Price and tax phrasing.
    Matches e.g.:
    - MRP Rs. 40.00 incl. of all taxes
    - MRP ₹ 185.00 (inclusive of all taxes)
    - MRP: 50.00 INCL OF ALL TAXES
    """
    p1 = r"(?i)\b(?:MRP|M\.R\.P\.?|Maximum\s*Retail\s*Price)\s*[:.-]?\s*(?:Rs\.?|₹|INR)?\s*(\d+(?:\.\d{1,2})?)\s*(.*?(?:(?:incl|inclusive)\s*(?:of)?\s*all\s*taxes|incl\.?\s*of\s*all\s*taxes|\(incl.*?taxes\)))"
    m1 = re.search(p1, text)
    if m1:
        val = m1.group(1).strip()
        tax_part = m1.group(2).strip()
        return f"MRP Rs. {val} {tax_part}".strip(), 0.95

    p2 = r"(?i)\b(?:MRP|M\.R\.P\.?|Maximum\s*Retail\s*Price)\s*[:.-]?\s*(?:Rs\.?|₹|INR)?\s*(\d+(?:\.\d{1,2})?)"
    m2 = re.search(p2, text)
    if m2:
        val = m2.group(1).strip()
        if re.search(r"(?i)(?:incl|inclusive)\s*(?:of)?\s*all\s*taxes", text):
            return f"MRP Rs. {val} incl. of all taxes", 0.90
        return f"MRP Rs. {val}", 0.85

    return None, None


def extract_net_quantity(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Net Quantity.
    """
    p1 = r"(?i)\b(?:Net\s*(?:Qty|Quantity|Wt|Weight|Volume|Content|Contents)?)\s*[:.-]?\s*(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|n|u|cm|m|gms|kgs|ltr|gm|ml\.))\b"
    m1 = re.search(p1, text)
    if m1:
        return m1.group(1).strip(), 0.92

    p2 = r"\b(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gms|kgs|ltr))\b"
    m2 = re.search(p2, text, re.IGNORECASE)
    if m2:
        return m2.group(1).strip(), 0.75

    return None, None


def extract_dates(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts Manufacturing Date, Packing Date, Expiry Date, and Best Before.
    """
    mfg_date = None
    pkd_date = None
    exp_date = None
    best_before = None
    conf = None

    date_regex = r"(\b(?:0[1-9]|1[0-2])[/-](?:20\d{2}|\d{2})\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(?:20\d{2}|\d{2})\b|\b(?:20\d{2})[/-](?:0[1-9]|1[0-2])\b)"

    mfg_m = re.search(r"(?i)\b(?:Mfd|Mfg|Manufactured|Mfg\s*Date|Mfd\s*Date)\s*[:.-]?\s*" + date_regex, text)
    if mfg_m:
        mfg_date = mfg_m.group(1).strip()
        conf = 0.90

    pkd_m = re.search(r"(?i)\b(?:PKD|Packed|Pack|Pkg|Packed\s*on)\s*[:.-]?\s*" + date_regex, text)
    if pkd_m:
        pkd_date = pkd_m.group(1).strip()
        if not mfg_date:
            mfg_date = pkd_date
        conf = 0.90

    exp_m = re.search(r"(?i)\b(?:Use\s*by|Expiry|Exp\s*Date|Exp)\s*[:.-]?\s*" + date_regex, text)
    if exp_m:
        exp_date = exp_m.group(1).strip()
        conf = 0.90

    bb_m = re.search(r"(?i)\b(?:Best\s*Before)\s*[:.-]?\s*([^\n,]+)", text)
    if bb_m:
        best_before = bb_m.group(1).strip()
        conf = 0.85

    return mfg_date, pkd_date, exp_date, best_before, conf


def extract_consumer_care(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts consumer grievance phone, email, and care block.
    """
    phone = None
    email = None
    care_block = None
    conf = None

    phone_m = re.search(r"\b(1800[-\s]?\d{3}[-\s]?\d{3,4}|\+?91[-\s]?\d{10}|\b\d{3,5}[-\s]\d{6,8})\b", text)
    if phone_m:
        phone = phone_m.group(1).strip()
        conf = 0.92

    email_m = re.search(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", text)
    if email_m:
        email = email_m.group(1).strip()
        conf = 0.95

    care_m = re.search(r"(?i)(?:Consumer\s*Care|Customer\s*Care|Helpline|Grievance\s*Cell)\s*[:.-]?\s*([^\n]+(?:\n[^\n]+)?)", text)
    if care_m:
        care_block = care_m.group(0).strip()
        conf = 0.88
    elif phone or email:
        care_block = f"Phone: {phone or 'N/A'}, Email: {email or 'N/A'}"

    return phone, email, care_block, conf


def extract_manufacturer_and_address(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float]]:
    """
    Extracts manufacturer, packer, importer name, and address.
    """
    mfg_name = None
    packer_name = None
    importer_name = None
    address = None
    conf = None

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if re.search(r"(?i)\b(?:Mfg\s*by|Manufactured\s*by|Mfd\s*by)\b", line):
            mfg_name = re.sub(r"(?i)\b(?:Mfg\s*by|Manufactured\s*by|Mfd\s*by)\s*[:.-]?", "", line).strip()
            if not mfg_name and i + 1 < len(lines):
                mfg_name = lines[i + 1]
            conf = 0.88

        elif re.search(r"(?i)\b(?:Packed\s*by|Pkd\s*by)\b", line):
            packer_name = re.sub(r"(?i)\b(?:Packed\s*by|Pkd\s*by)\s*[:.-]?", "", line).strip()
            if not packer_name and i + 1 < len(lines):
                packer_name = lines[i + 1]
            conf = 0.88

        elif re.search(r"(?i)\b(?:Imported\s*by|Imp\s*by)\b", line):
            importer_name = re.sub(r"(?i)\b(?:Imported\s*by|Imp\s*by)\s*[:.-]?", "", line).strip()
            if not importer_name and i + 1 < len(lines):
                importer_name = lines[i + 1]
            conf = 0.88

        if re.search(r"(?i)\b(?:Plot|Street|Road|Estate|Phase|Sector|Industrial\s*Area|Pin\s*Code|Pincode|\b\d{6}\b)\b", line):
            if not address:
                address = line
            else:
                address += f", {line}"
            conf = 0.85

    return mfg_name, packer_name, importer_name, address, conf


def extract_unit_sale_price(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts Unit Sale Price (USP).
    """
    p = r"(?i)\b(?:USP|Unit\s*Sale\s*Price)\s*[:.-]?\s*(?:Rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?\s*(?:/|per)\s*(?:g|kg|ml|l|item|piece|N|u))\b"
    m = re.search(p, text)
    if m:
        return f"Rs. {m.group(1).strip()}", 0.90
    return None, None


def extract_origin(text: str) -> Tuple[Optional[str], bool, Optional[float]]:
    """
    Extracts Country of Origin and is_imported boolean.
    """
    p = r"(?i)\b(?:Country\s*of\s*Origin|Made\s*in|Origin)\s*[:.-]?\s*([A-Za-z ]+)"
    m = re.search(p, text)
    if m:
        country = m.group(1).strip()
        is_imported = country.lower() not in ("india", "bharat", "domestic")
        return country, is_imported, 0.92

    if re.search(r"(?i)\b(?:Imported\s*by|Importer)\b", text):
        return None, True, 0.80

    return None, False, None


def extract_commodity_name(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Extracts commodity name (Product/Item line or first prominent header).
    """
    p = r"(?i)\b(?:Product|Item|Commodity)\s*[:.-]?\s*([^\n]+)"
    m = re.search(p, text)
    if m:
        return m.group(1).strip(), 0.90

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:3]:
        if not re.search(r"(?i)^(?:MRP|Net|Mfd|Exp|Batch|Pkg|Use|Toll)", line) and len(line) > 3:
            return line, 0.70

    return None, None


def extract_declaration_from_ocr(
    raw_text: str, tokens_data: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Deterministic extraction pipeline converting raw OCR text into structured LMPC 2011 declarations.
    """
    extracted_fields: Dict[str, Any] = {}
    field_confidences: Dict[str, float] = {}

    if not raw_text or not raw_text.strip():
        return extracted_fields, field_confidences

    # 1. Commodity Name
    comm_name, comm_conf = extract_commodity_name(raw_text)
    if comm_name:
        extracted_fields["commodity_name"] = comm_name
        if comm_conf is not None:
            field_confidences["commodity_name"] = comm_conf

    # 2. Manufacturer, Packer, Importer, Address
    mfg_name, pkr_name, imp_name, addr, mfg_conf = extract_manufacturer_and_address(raw_text)
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

    # 3. Net Quantity
    net_qty, qty_conf = extract_net_quantity(raw_text)
    if net_qty:
        extracted_fields["net_quantity"] = net_qty
        if qty_conf is not None:
            field_confidences["net_quantity"] = qty_conf

    # 4. MRP
    mrp, mrp_conf = extract_mrp(raw_text)
    if mrp:
        extracted_fields["mrp"] = mrp
        if mrp_conf is not None:
            field_confidences["mrp"] = mrp_conf

    # 5. Dates
    mfg_dt, pkd_dt, exp_dt, bb, dt_conf = extract_dates(raw_text)
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
    phone, email, care_block, care_conf = extract_consumer_care(raw_text)
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
    usp, usp_conf = extract_unit_sale_price(raw_text)
    if usp:
        extracted_fields["unit_sale_price"] = usp
        if usp_conf is not None:
            field_confidences["unit_sale_price"] = usp_conf

    # 8. Origin
    origin, is_imp, orig_conf = extract_origin(raw_text)
    if origin:
        extracted_fields["country_of_origin"] = origin
        if orig_conf:
            field_confidences["country_of_origin"] = orig_conf
    extracted_fields["is_imported"] = is_imp

    return extracted_fields, field_confidences

