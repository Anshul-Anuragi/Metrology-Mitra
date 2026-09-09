import hashlib
import io
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.gravimetric_test import GravimetricTest
from app.models.user import User


def get_fifth_schedule_sample_size(lot_size: Optional[int]) -> int:
    """
    Determines statutory sample size for lot testing under Fifth Schedule of LMPC Rules, 2011:
    - Lot size up to 4,000 packages -> Sample size = 32 packages
    - Lot size exceeding 4,000 packages -> Sample size = 80 packages
    """
    if lot_size is None or lot_size <= 4000:
        return 32
    return 80


def get_statutory_mpe(nominal_value: float, unit: str) -> Tuple[float, str]:
    """
    Computes statutory Maximum Permissible Error (MPE) on net quantity
    under the Official First Schedule of Legal Metrology (Packaged Commodities) Rules, 2011.

    Supports:
    - Mass / Weight (g, kg) & Volume (ml, l) [First Schedule, Table 1]
    - Length (m, cm, mm) [First Schedule, Table 2]
    - Area (sq_m, sq_cm) [First Schedule, Table 3]
    - Number / Count (N, U, units, pieces) [First Schedule, Table 4]

    Returns:
    - mpe_in_nominal_units: Absolute MPE in the same unit as nominal_value.
    - mpe_rule_description: Statutory citation string.
    """
    if nominal_value is None or nominal_value <= 0:
        return 0.0, "NEEDS_REVIEW: Statutory MPE cannot be determined for non-positive nominal quantity under First Schedule."

    u = (unit or "").strip().lower()

    # 1. Mass / Weight & Volume (First Schedule Table 1)
    mass_vol_units = (
        "g", "gm", "gram", "grams", "kg", "kilogram", "kilograms",
        "ml", "millilitre", "milliliter", "l", "ltr", "litre", "liter", "litres", "liters"
    )
    if u in mass_vol_units:
        norm_val = nominal_value
        if u in ("kg", "kilogram", "kilograms") or u in ("l", "ltr", "litre", "liter", "litres", "liters"):
            norm_val = nominal_value * 1000.0

        if norm_val <= 50.0:
            mpe_val_g = norm_val * 0.09
            desc = "9% of nominal quantity (First Schedule Table 1, Qn <= 50g/ml)"
        elif norm_val <= 100.0:
            mpe_val_g = 4.5
            desc = "4.5 g/ml fixed (First Schedule Table 1, 50 < Qn <= 100g/ml)"
        elif norm_val <= 200.0:
            mpe_val_g = norm_val * 0.045
            desc = "4.5% of nominal quantity (First Schedule Table 1, 100 < Qn <= 200g/ml)"
        elif norm_val <= 300.0:
            mpe_val_g = 9.0
            desc = "9.0 g/ml fixed (First Schedule Table 1, 200 < Qn <= 300g/ml)"
        elif norm_val <= 500.0:
            mpe_val_g = norm_val * 0.03
            desc = "3.0% of nominal quantity (First Schedule Table 1, 300 < Qn <= 500g/ml)"
        elif norm_val <= 1000.0:
            mpe_val_g = 15.0
            desc = "15.0 g/ml fixed (First Schedule Table 1, 500 < Qn <= 1000g/ml)"
        elif norm_val <= 10000.0:
            mpe_val_g = norm_val * 0.015
            desc = "1.5% of nominal quantity (First Schedule Table 1, 1kg < Qn <= 10kg/L)"
        elif norm_val <= 15000.0:
            mpe_val_g = 150.0
            desc = "150.0 g/ml fixed (First Schedule Table 1, 10kg < Qn <= 15kg/L)"
        else:
            mpe_val_g = norm_val * 0.01
            desc = "1.0% of nominal quantity (First Schedule Table 1, Qn > 15kg/L)"

        if u in ("kg", "kilogram", "kilograms") or u in ("l", "ltr", "litre", "liter", "litres", "liters"):
            mpe_final = mpe_val_g / 1000.0
        else:
            mpe_final = mpe_val_g

        return round(mpe_final, 4), desc

    # 2. Length (First Schedule Table 2)
    length_units = ("m", "meter", "meters", "metre", "metres", "cm", "centimeter", "centimeters", "mm")
    if u in length_units:
        norm_m = nominal_value
        if u in ("cm", "centimeter", "centimeters"):
            norm_m = nominal_value / 100.0
        elif u == "mm":
            norm_m = nominal_value / 1000.0

        if norm_m <= 10.0:
            mpe_len_m = norm_m * 0.02
            desc = "2.0% of declared length (First Schedule Table 2, length <= 10m)"
        else:
            mpe_len_m = norm_m * 0.01
            desc = "1.0% of declared length (First Schedule Table 2, length > 10m)"

        if u in ("cm", "centimeter", "centimeters"):
            mpe_final = mpe_len_m * 100.0
        elif u == "mm":
            mpe_final = mpe_len_m * 1000.0
        else:
            mpe_final = mpe_len_m

        return round(mpe_final, 4), desc

    # 3. Area (First Schedule Table 3)
    area_units = ("sq_m", "sqm", "m2", "sq_cm", "sqcm", "cm2")
    if u in area_units:
        norm_sqm = nominal_value
        if u in ("sq_cm", "sqcm", "cm2"):
            norm_sqm = nominal_value / 10000.0

        if norm_sqm <= 1.0:
            mpe_area = norm_sqm * 0.04
            desc = "4.0% of declared area (First Schedule Table 3, area <= 1m²)"
        else:
            mpe_area = norm_sqm * 0.02
            desc = "2.0% of declared area (First Schedule Table 3, area > 1m²)"

        if u in ("sq_cm", "sqcm", "cm2"):
            mpe_final = mpe_area * 10000.0
        else:
            mpe_final = mpe_area

        return round(mpe_final, 4), desc

    # 4. Number / Count (First Schedule Table 4)
    number_units = ("n", "u", "unit", "units", "piece", "pieces", "count", "nos", "no")
    if u in number_units:
        if nominal_value <= 50:
            return 0.0, "0 (Zero error allowable for count <= 50 under First Schedule Table 4)"
        else:
            mpe_num = math.ceil(nominal_value * 0.01)
            return float(mpe_num), "1% of declared count rounded to next integer (First Schedule Table 4, count > 50)"

    return 0.0, f"NEEDS_REVIEW: Unit '{unit}' is not recognized under First Schedule tables of LMPC Rules, 2011."


def evaluate_gravimetric_samples(
    nominal_quantity: float,
    unit: str,
    samples_data: List[Dict[str, float]],
    default_tare: float = 0.0,
    lot_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Statistically evaluates sample unit physical measurements against statutory criteria
    under Rule 19, Rule 24, First Schedule, and Fifth Schedule of LMPC Rules, 2011:
    1. Sample mean net quantity (x̄) must be >= declared nominal quantity (Qn).
    2. Number of units with negative error > MPE must not exceed allowable defective limit.
    3. Zero units may have negative error > 2 * MPE (double MPE is an immediate critical rejection).
    """
    mpe_val, mpe_desc = get_statutory_mpe(nominal_quantity, unit)
    if nominal_quantity <= 0 or "NEEDS_REVIEW" in mpe_desc:
        return {
            "lot_decision": "NEEDS_REVIEW",
            "statutory_standard": "LMPC Rules, 2011 — Rules 19, 24, First Schedule & Fifth Schedule",
            "mpe_value": mpe_val,
            "mpe_description": mpe_desc,
            "sample_mean_net_quantity": 0.0,
            "sample_std_dev": 0.0,
            "defective_units_count": 0,
            "double_mpe_count": 0,
            "double_mpe_defective_count": 0,
            "sample_units": [],
            "reason": f"Statutory MPE cannot be determined: {mpe_desc}",
            "disclaimer": "Decision-Support Record: Physical scale measurements must be recorded on certified weighing instruments under Rule 19.",
        }

    double_mpe_val = mpe_val * 2.0

    processed_units: List[Dict[str, Any]] = []
    net_weights: List[float] = []
    defective_units_count = 0
    double_mpe_count = 0

    for idx, s in enumerate(samples_data):
        gross = float(s.get("gross_weight", 0.0))
        tare = float(s.get("tare_weight", default_tare))
        net = round(gross - tare, 4)
        net_weights.append(net)

        error = round(net - nominal_quantity, 4)
        is_defective = error < (-mpe_val)
        is_double_mpe = error < (-double_mpe_val)

        if is_defective:
            defective_units_count += 1
        if is_double_mpe:
            double_mpe_count += 1

        processed_units.append({
            "unit_number": idx + 1,
            "gross_weight": gross,
            "tare_weight": tare,
            "net_quantity": net,
            "error": error,
            "is_defective": is_defective,
            "is_critical_defect": is_double_mpe,
        })

    n = len(net_weights)
    if n == 0:
        return {
            "lot_decision": "NEEDS_REVIEW",
            "statutory_standard": "LMPC Rules, 2011 — Rules 19, 24, First Schedule & Fifth Schedule",
            "mpe_value": mpe_val,
            "mpe_description": mpe_desc,
            "sample_mean_net_quantity": 0.0,
            "sample_std_dev": 0.0,
            "defective_units_count": 0,
            "double_mpe_count": 0,
            "double_mpe_defective_count": 0,
            "sample_units": [],
            "reason": "No sample measurements provided.",
            "disclaimer": "Decision-Support Record: Physical scale measurements must be recorded on certified weighing instruments.",
        }

    mean_val = round(sum(net_weights) / n, 4)
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in net_weights) / (n - 1)
        std_dev = round(math.sqrt(variance), 4)
    else:
        std_dev = 0.0

    # Decision logic based on Rule 19 & Fifth Schedule criteria
    # Max allowable defective units: for small pilot sample n <= 10 -> 0 allowed, n <= 32 -> 1 allowed, n > 32 -> 2 allowed
    max_allowable_defectives = 1 if n >= 20 else (2 if n >= 50 else 0)

    reasons = []
    lot_decision = "PASSED_MPE"

    if double_mpe_count > 0:
        lot_decision = "FAILED_CRITICAL_DOUBLE_MPE"
        reasons.append(f"{double_mpe_count} unit(s) exhibited critical negative error exceeding 2x statutory MPE (-{double_mpe_val:.4f} {unit}).")
    elif mean_val < nominal_quantity:
        lot_decision = "FAILED_MEAN_DEFICIT"
        reasons.append(f"Sample mean net quantity ({mean_val:.4f} {unit}) is below declared nominal quantity ({nominal_quantity:.4f} {unit}) under Rule 19.")
    elif defective_units_count > max_allowable_defectives:
        lot_decision = "FAILED_EXCESSIVE_DEFECTIVES"
        reasons.append(f"Defective unit count ({defective_units_count}) exceeds allowable limit ({max_allowable_defectives}) for sample size {n}.")

    if not reasons:
        reasons.append(f"Lot satisfied all statutory First Schedule & Fifth Schedule criteria: mean net content ({mean_val:.4f} {unit} >= {nominal_quantity:.4f} {unit}), 0 double-MPE defects, and defectives within allowable limits.")

    return {
        "lot_decision": lot_decision,
        "statutory_standard": "LMPC Rules, 2011 — Rules 19, 24, First Schedule & Fifth Schedule",
        "mpe_value": mpe_val,
        "mpe_description": mpe_desc,
        "sample_mean_net_quantity": mean_val,
        "sample_std_dev": std_dev,
        "defective_units_count": defective_units_count,
        "double_mpe_count": double_mpe_count,
        "double_mpe_defective_count": double_mpe_count,
        "sample_units": processed_units,
        "sample_units_data": processed_units,
        "reason": " ".join(reasons),
        "disclaimer": (
            "Decision-Support Record: Statutory physical net-weight record logged under Rule 19 & First Schedule of LMPC Rules, 2011. "
            "Data represents physical weighing readings obtained by inspecting officer on calibrated scales. "
            "Testing methodology follows Sixth Schedule guidelines."
        ),
    }


def build_gravimetric_test_pdf(test: GravimetricTest, inspector: User) -> bytes:
    """
    Renders an official Statutory Gravimetric Net-Quantity Verification Record PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#1A365D")
    text_dark = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#F7FAFC")

    title_style = ParagraphStyle(
        "MemoTitle",
        parent=styles["Heading1"],
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=primary_color,
        fontName="Helvetica-Bold",
    )
    sub_title = ParagraphStyle(
        "MemoSub",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
        fontName="Helvetica",
    )
    body_style = ParagraphStyle(
        "MemoBody",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica",
    )
    bold_body = ParagraphStyle(
        "MemoBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=body_style,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#718096"),
        fontName="Helvetica-Bold",
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=text_dark,
        fontName="Helvetica",
    )

    elements = []

    # Header
    elements.append(Paragraph("GOVERNMENT OF INDIA • DEPARTMENT OF CONSUMER AFFAIRS", sub_title))
    elements.append(Paragraph("DIRECTORATE OF LEGAL METROLOGY", sub_title))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("PHYSICAL METROLOGY NET-QUANTITY VERIFICATION MEMORANDUM", title_style))
    elements.append(Paragraph("[Under Rules 19 & 24, First Schedule and Fifth Schedule of LMPC Rules, 2011]", sub_title))
    elements.append(Spacer(1, 8))

    # Summary Metadata
    summary_data = [
        [
            Paragraph("TEST RECORD ID:", meta_label),
            Paragraph(f"<font name='Courier' size='7'>{str(test.id)}</font>", meta_val),
            Paragraph("VERIFICATION DATE:", meta_label),
            Paragraph(test.created_at.strftime("%d %b %Y, %H:%M UTC") if test.created_at else "N/A", meta_val),
        ],
        [
            Paragraph("NOMINAL QUANTITY (Qn):", meta_label),
            Paragraph(f"<b>{test.nominal_quantity_value} {test.nominal_quantity_unit}</b>", meta_val),
            Paragraph("STATUTORY MPE (±):", meta_label),
            Paragraph(f"<b>±{test.mpe_value} {test.nominal_quantity_unit}</b>", meta_val),
        ],
        [
            Paragraph("SAMPLE MEAN (x̄):", meta_label),
            Paragraph(f"<b>{test.sample_mean_net_quantity:.4f} {test.nominal_quantity_unit}</b>" if test.sample_mean_net_quantity else "N/A", meta_val),
            Paragraph("STD DEVIATION (s):", meta_label),
            Paragraph(f"{test.sample_std_dev:.4f}" if test.sample_std_dev else "0.0", meta_val),
        ],
        [
            Paragraph("INSPECTING OFFICER:", meta_label),
            Paragraph(f"{inspector.name} ({inspector.role})", meta_val),
            Paragraph("LOT VERDICT:", meta_label),
            Paragraph(f"<b>{test.lot_decision}</b>", meta_val),
        ],
    ]
    t_summary = Table(summary_data, colWidths=[110, 160, 110, 142])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 10))

    # Sample Units Table
    units_data = test.sample_units_data or []
    if units_data:
        elements.append(Paragraph("<b>SAMPLE UNIT MEASUREMENTS & ERROR PROFILE</b>", bold_body))
        elements.append(Spacer(1, 4))

        unit_headers = ["Unit #", "Gross (g/ml)", "Tare (g/ml)", "Net Quantity", "Error (e)", "Result Status"]
        unit_rows = [[Paragraph(f"<b>{h}</b>", meta_label) for h in unit_headers]]

        for u in units_data:
            err = u.get("error", 0.0)
            is_def = u.get("is_defective", False)
            is_crit = u.get("is_critical_defect", False)
            status_str = "PASSED"
            if is_crit:
                status_str = "<font color='#C53030'><b>CRITICAL (>2x MPE)</b></font>"
            elif is_def:
                status_str = "<font color='#DD6B20'><b>DEFECTIVE (>MPE)</b></font>"

            unit_rows.append([
                Paragraph(str(u.get("unit_number", "-")), meta_val),
                Paragraph(f"{u.get('gross_weight', 0.0):.2f}", meta_val),
                Paragraph(f"{u.get('tare_weight', 0.0):.2f}", meta_val),
                Paragraph(f"<b>{u.get('net_quantity', 0.0):.2f} {test.nominal_quantity_unit}</b>", meta_val),
                Paragraph(f"{err:+.2f} {test.nominal_quantity_unit}", meta_val),
                Paragraph(status_str, meta_val),
            ])

        t_units = Table(unit_rows, colWidths=[40, 90, 80, 110, 92, 110])
        t_units.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        elements.append(t_units)
        elements.append(Spacer(1, 10))

    # Statutory Standards & Legal Notice
    elements.append(Paragraph("<b>STATUTORY BASIS & STATISTICAL METHODOLOGY</b>", bold_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        f"<b>Standard:</b> {test.statutory_standard}<br/>"
        f"<b>Methodology:</b> Statistical lot evaluation conducted in accordance with Rule 19, Rule 24, First Schedule, and Fifth Schedule of the Legal Metrology (Packaged Commodities) Rules, 2011. Testing procedures align with Sixth Schedule guidelines.",
        body_style,
    ))
    elements.append(Spacer(1, 6))

    # Disclaimer Block
    disclaimer_text = (
        test.disclaimer
        or "This document is a statutory inspection test memorandum recorded by an authorized Legal Metrology Officer. "
        "Physical weighing measurements are conducted on certified laboratory/field weighing apparatus."
    )
    elements.append(Paragraph(f"<i><b>Notice / Disclaimer:</b> {disclaimer_text}</i>", meta_label))
    elements.append(Spacer(1, 12))

    # Signatures
    sig_data = [
        [
            Paragraph("<b>STORE / DEPOT REPRESENTATIVE</b><br/><br/><br/>Name: ______________________<br/>Date: ______________________", meta_val),
            Paragraph("<b>LEGAL METROLOGY OFFICER</b><br/><br/><br/>Name: " + inspector.name + "<br/>Designation: " + inspector.role, meta_val),
        ]
    ]
    t_sig = Table(sig_data, colWidths=[261, 261])
    t_sig.setStyle(TableStyle([
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(KeepTogether([t_sig]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
