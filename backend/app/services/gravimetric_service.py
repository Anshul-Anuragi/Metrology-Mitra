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


def get_statutory_mpe(nominal_value: float, unit: str) -> Tuple[float, str]:
    """
    Computes statutory Maximum Permissible Error (MPE) on net quantity
    under Legal Metrology (Packaged Commodities) Rules, 2011 — Schedule IV (Table 2).

    Returns:
    - mpe_in_nominal_units: Absolute MPE in the same unit as nominal_value.
    - mpe_rule_description: Statutory citation string.
    """
    u = unit.strip().lower()
    norm_val = nominal_value
    # Convert kg to g or L to ml for Table 2 lookup
    if u == "kg":
        norm_val = nominal_value * 1000.0
    elif u in ("l", "ltr", "litre", "liter"):
        norm_val = nominal_value * 1000.0

    # Schedule IV Table 2 tiers (values in g or ml)
    if norm_val <= 50.0:
        # 9% of nominal quantity
        mpe_val_g = norm_val * 0.09
        desc = "9% of nominal quantity (Schedule IV Table 2, Qn <= 50g/ml)"
    elif norm_val <= 100.0:
        # 4.5 g or ml
        mpe_val_g = 4.5
        desc = "4.5 g/ml fixed (Schedule IV Table 2, 50 < Qn <= 100g/ml)"
    elif norm_val <= 200.0:
        # 4.5% of nominal quantity
        mpe_val_g = norm_val * 0.045
        desc = "4.5% of nominal quantity (Schedule IV Table 2, 100 < Qn <= 200g/ml)"
    elif norm_val <= 300.0:
        # 9 g or ml
        mpe_val_g = 9.0
        desc = "9.0 g/ml fixed (Schedule IV Table 2, 200 < Qn <= 300g/ml)"
    elif norm_val <= 500.0:
        # 3% of nominal quantity
        mpe_val_g = norm_val * 0.03
        desc = "3.0% of nominal quantity (Schedule IV Table 2, 300 < Qn <= 500g/ml)"
    elif norm_val <= 1000.0:
        # 15 g or ml
        mpe_val_g = 15.0
        desc = "15.0 g/ml fixed (Schedule IV Table 2, 500 < Qn <= 1000g/ml)"
    elif norm_val <= 10000.0:
        # 1.5% of nominal quantity
        mpe_val_g = norm_val * 0.015
        desc = "1.5% of nominal quantity (Schedule IV Table 2, 1kg < Qn <= 10kg/L)"
    elif norm_val <= 15000.0:
        # 150 g or ml
        mpe_val_g = 150.0
        desc = "150.0 g/ml fixed (Schedule IV Table 2, 10kg < Qn <= 15kg/L)"
    else:
        # 1.0% of nominal quantity
        mpe_val_g = norm_val * 0.01
        desc = "1.0% of nominal quantity (Schedule IV Table 2, Qn > 15kg/L)"

    # Convert MPE back to original unit if kg or L
    if u == "kg":
        mpe_final = mpe_val_g / 1000.0
    elif u in ("l", "ltr", "litre", "liter"):
        mpe_final = mpe_val_g / 1000.0
    else:
        mpe_final = mpe_val_g

    return round(mpe_final, 4), desc


def evaluate_gravimetric_samples(
    nominal_quantity: float,
    unit: str,
    samples_data: List[Dict[str, float]],
    default_tare: float = 0.0,
    lot_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Statistically evaluates sample unit physical weights against Schedule IV criteria:
    1. Sample mean net quantity (x̄) must be >= declared nominal quantity (Qn).
    2. Number of units with negative error > MPE must not exceed Schedule IV Table 1 allowable limits.
    3. Zero units may have negative error > 2 * MPE (double MPE is an immediate rejection).
    """
    mpe_val, mpe_desc = get_statutory_mpe(nominal_quantity, unit)
    double_mpe_val = mpe_val * 2.0

    processed_units: List[Dict[str, Any]] = []
    net_weights: List[float] = []
    defective_units_count = 0
    double_mpe_count = 0

    for idx, s in enumerate(samples_data):
        unit_num = s.get("unit_number", idx + 1)
        gross_w = float(s.get("gross_weight", 0.0))
        tare_w = float(s.get("tare_weight", default_tare) if s.get("tare_weight") is not None else default_tare)
        net_w = max(0.0, round(gross_w - tare_w, 4))
        error_val = round(net_w - nominal_quantity, 4)
        error_pct = round((error_val / nominal_quantity) * 100.0, 2) if nominal_quantity > 0 else 0.0

        is_neg = error_val < 0
        exceeds_mpe = (is_neg and abs(error_val) > mpe_val)
        exceeds_double_mpe = (is_neg and abs(error_val) > double_mpe_val)

        if exceeds_mpe:
            defective_units_count += 1
        if exceeds_double_mpe:
            double_mpe_count += 1

        net_weights.append(net_w)
        processed_units.append({
            "unit_number": unit_num,
            "gross_weight": gross_w,
            "tare_weight": tare_w,
            "net_weight": net_w,
            "error_value": error_val,
            "error_percent": error_pct,
            "is_negative_error": is_neg,
            "exceeds_mpe": exceeds_mpe,
            "exceeds_double_mpe": exceeds_double_mpe,
        })

    n = len(net_weights)
    if n == 0:
        return {
            "mpe_value": mpe_val,
            "mpe_description": mpe_desc,
            "sample_units_data": [],
            "sample_mean_net_quantity": 0.0,
            "sample_std_dev": 0.0,
            "defective_units_count": 0,
            "double_mpe_defective_count": 0,
            "lot_decision": "INCOMPLETE",
        }

    mean_net = sum(net_weights) / n
    variance = sum((x - mean_net) ** 2 for x in net_weights) / (n - 1) if n > 1 else 0.0
    std_dev = math.sqrt(variance)

    # Schedule IV Table 1 Acceptance Criteria:
    # For sample size <= 20: allowable defectives is typically 1 (for n=20) or 0 (for small sample n < 10)
    allowable_defectives = 1 if n >= 20 else (1 if n >= 10 else 0)

    # Lot Decision
    if double_mpe_count > 0:
        lot_decision = "FAILED_CRITICAL_DOUBLE_MPE"
    elif mean_net < nominal_quantity:
        lot_decision = "FAILED_MEAN_DEFICIT"
    elif defective_units_count > allowable_defectives:
        lot_decision = "FAILED_EXCESSIVE_DEFECTIVES"
    else:
        lot_decision = "PASSED_MPE"

    return {
        "nominal_quantity_value": nominal_quantity,
        "nominal_quantity_unit": unit,
        "declared_tare_weight": default_tare,
        "mpe_value": mpe_val,
        "mpe_description": mpe_desc,
        "sample_units_data": processed_units,
        "sample_mean_net_quantity": round(mean_net, 4),
        "sample_std_dev": round(std_dev, 4),
        "defective_units_count": defective_units_count,
        "double_mpe_defective_count": double_mpe_count,
        "allowable_defectives": allowable_defectives,
        "lot_decision": lot_decision,
        "statutory_standard": "Legal Metrology (Packaged Commodities) Rules, 2011 — Schedule IV & Rule 24",
        "disclaimer": (
            "Physical gravimetric testing records actual gross and tare weights on certified weighing equipment. "
            "Evaluation follows Schedule IV Table 2 MPE tolerances and sample mean criteria."
        ),
    }


def build_gravimetric_test_pdf(test: GravimetricTest, inspector: User) -> bytes:
    """
    Renders an official MetrologyMitra Gravimetric Net Quantity Verification Memo in PDF.
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
    danger_color = colors.HexColor("#C53030")
    success_color = colors.HexColor("#2F855A")
    text_dark = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#EDF2F7")

    title_style = ParagraphStyle(
        "MpeTitle",
        parent=styles["Heading1"],
        fontSize=12,
        leading=15,
        textColor=primary_color,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    sub_title = ParagraphStyle(
        "MpeSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=primary_color,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "MpeBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica",
    )
    body_bold = ParagraphStyle(
        "MpeBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica-Bold",
    )

    story = []

    # 1. Header
    story.append(Paragraph("METROLOGYMITRA — STATUTORY PHYSICAL METROLOGY RECORD", title_style))
    story.append(Paragraph("RULE 24 & SCHEDULE IV GRAVIMETRIC NET-QUANTITY TEST MEMORANDUM", sub_title))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8))

    # 2. Meta Table
    meta_rows = [
        [
            Paragraph("<b>Test ID:</b>", body_style),
            Paragraph(str(test.id)[:18] + "...", body_bold),
            Paragraph("<b>Test Date:</b>", body_style),
            Paragraph(test.created_at.strftime("%Y-%m-%d %H:%M UTC") if test.created_at else "N/A", body_style),
        ],
        [
            Paragraph("<b>Declared Nominal Qty:</b>", body_style),
            Paragraph(f"<b>{test.nominal_quantity_value} {test.nominal_quantity_unit}</b>", body_bold),
            Paragraph("<b>Statutory MPE (Table 2):</b>", body_style),
            Paragraph(f"± {test.mpe_value} {test.nominal_quantity_unit}", body_bold),
        ],
        [
            Paragraph("<b>Testing Officer:</b>", body_style),
            Paragraph(f"{inspector.name} ({inspector.role.value})", body_style),
            Paragraph("<b>Lot Verdict:</b>", body_style),
            Paragraph(f"<b>{test.lot_decision}</b>", ParagraphStyle("VD", parent=body_bold, textColor=success_color if test.lot_decision == "PASSED_MPE" else danger_color)),
        ],
    ]
    t_meta = Table(meta_rows, colWidths=[1.8 * inch, 2.0 * inch, 1.8 * inch, 1.6 * inch])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. Statistical Summary Table
    story.append(Paragraph("1. STATISTICAL NET CONTENT AGGREGATION (SCHEDULE IV CLAUSE 3)", ParagraphStyle("H2", parent=title_style, alignment=0, fontSize=9, textColor=primary_color)))
    samples = test.sample_units_data or []
    stat_rows = [
        [Paragraph("<b>Sample Units Tested:</b>", body_bold), Paragraph(str(len(samples)), body_style)],
        [Paragraph("<b>Sample Mean Net Content (x̄):</b>", body_bold), Paragraph(f"{test.sample_mean_net_quantity or 'N/A'} {test.nominal_quantity_unit}", body_bold)],
        [Paragraph("<b>Sample Standard Deviation (s):</b>", body_bold), Paragraph(f"{test.sample_std_dev or 'N/A'}", body_style)],
        [Paragraph("<b>Defective Units (> 1 MPE Negative):</b>", body_bold), Paragraph(f"{test.defective_units_count} unit(s)", body_style)],
    ]
    t_stat = Table(stat_rows, colWidths=[2.6 * inch, 4.6 * inch])
    t_stat.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, light_bg]),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 10))

    # 4. Individual Sample Breakdown Table (up to 15 samples)
    if samples:
        story.append(Paragraph("2. INDIVIDUAL SAMPLE WEIGHING LOG", ParagraphStyle("H3", parent=title_style, alignment=0, fontSize=9, textColor=primary_color)))
        unit_table_data = [[
            Paragraph("<b>Unit #</b>", body_bold),
            Paragraph("<b>Gross Wt</b>", body_bold),
            Paragraph("<b>Tare Wt</b>", body_bold),
            Paragraph("<b>Net Wt</b>", body_bold),
            Paragraph("<b>Error</b>", body_bold),
            Paragraph("<b>MPE Status</b>", body_bold),
        ]]
        for u in samples[:15]:
            status_txt = "PASS" if not u.get("exceeds_mpe") else ("DOUBLE MPE DEFECT" if u.get("exceeds_double_mpe") else "DEFICIENT (>1 MPE)")
            unit_table_data.append([
                Paragraph(str(u.get("unit_number", "-")), body_style),
                Paragraph(f"{u.get('gross_weight', 0):.2f}", body_style),
                Paragraph(f"{u.get('tare_weight', 0):.2f}", body_style),
                Paragraph(f"{u.get('net_weight', 0):.2f}", body_style),
                Paragraph(f"{u.get('error_value', 0):+.2f}", body_style),
                Paragraph(status_txt, ParagraphStyle("St", parent=body_style, textColor=danger_color if u.get("exceeds_mpe") else success_color)),
            ])
        t_units = Table(unit_table_data, colWidths=[1.0 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.4 * inch])
        t_units.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("BACKGROUND", (0, 0), (-1, 0), light_bg),
            ("PADDING", (0, 0), (-1, -1), 3.5),
        ]))
        story.append(t_units)
        story.append(Spacer(1, 10))

    # 5. Fingerprint & Legal Disclaimer
    checksum = hashlib.sha256(f"{test.id}:{test.nominal_quantity_value}:{test.sample_mean_net_quantity}".encode()).hexdigest()
    foot_data = [
        [
            Paragraph("<b>Digital Record Integrity Fingerprint (SHA-256):</b>", body_style),
            Paragraph(f"<font name='Courier'>{checksum}</font>", body_style),
        ],
        [
            Paragraph("<b>Physical Testing Standard:</b>", body_style),
            Paragraph(test.statutory_standard, body_style),
        ],
    ]
    t_foot = Table(foot_data, colWidths=[2.6 * inch, 4.6 * inch])
    t_foot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether(t_foot))

    doc.build(story)
    return buffer.getvalue()

