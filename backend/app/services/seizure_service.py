import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.seizure import SeizureItem, SeizureRecord
from app.models.user import User


def generate_seizure_memo_number() -> str:
    """Generates unique statutory seizure memo number."""
    now = datetime.now(timezone.utc)
    return f"SZ-LMA15-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"


def compute_seizure_seal_hash(
    memo_number: str,
    premises_name: str,
    officer_id: str,
    timestamp: str,
    item_count: int,
) -> str:
    """Calculates cryptographic SHA-256 seal for the seizure panchnama."""
    raw = f"{memo_number}|{premises_name}|{officer_id}|{timestamp}|{item_count}|SEC15_LMA2009"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_panchnama_pdf(seizure: SeizureRecord, officer: User) -> bytes:
    """
    Renders an official Statutory Seizure Memo / Panchnama PDF under Section 15 of Legal Metrology Act, 2009.
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
    primary_color = colors.HexColor("#742A2A")  # Reddish brown for formal seizure notice
    text_dark = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#FFF5F5")

    title_style = ParagraphStyle(
        "PanchnamaTitle",
        parent=styles["Heading1"],
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=primary_color,
        fontName="Helvetica-Bold",
    )
    sub_title = ParagraphStyle(
        "PanchnamaSub",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
        fontName="Helvetica",
    )
    body_style = ParagraphStyle(
        "PanchnamaBody",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica",
    )
    bold_body = ParagraphStyle(
        "PanchnamaBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    meta_label = ParagraphStyle(
        "PanchnamaMetaLabel",
        parent=body_style,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#718096"),
        fontName="Helvetica-Bold",
    )
    meta_val = ParagraphStyle(
        "PanchnamaMetaVal",
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=text_dark,
        fontName="Helvetica",
    )

    elements = []

    # 1. Header & Statutory Watermark
    elements.append(Paragraph("GOVERNMENT OF INDIA • DEPARTMENT OF CONSUMER AFFAIRS", sub_title))
    elements.append(Paragraph("DIRECTORATE / CONTROLLER OF LEGAL METROLOGY", sub_title))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("FORM VI — SEIZURE MEMORANDUM & PANCHNAMA", title_style))
    elements.append(Paragraph("[Under Section 15 of Legal Metrology Act, 2009 & Rule 29 of LMPC Rules, 2011]", sub_title))
    elements.append(Spacer(1, 6))

    # Watermark Banner
    watermark_table = Table(
        [[Paragraph("<b>[DRAFT / REFERENCE ONLY — STATUTORY RECORD OF SEARCH & SEIZURE]</b>", ParagraphStyle("W", parent=sub_title, textColor=colors.HexColor("#9B2C2C")))]],
        colWidths=[522],
    )
    watermark_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FEB2B2")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(watermark_table)
    elements.append(Spacer(1, 10))

    # 2. Seizure Metadata Grid
    meta_data = [
        [
            Paragraph("SEIZURE MEMO NO:", meta_label),
            Paragraph(f"<b>{seizure.seizure_memo_number}</b>", meta_val),
            Paragraph("SEIZURE DATE / TIME:", meta_label),
            Paragraph(seizure.seizure_date.strftime("%d %b %Y, %H:%M UTC") if seizure.seizure_date else "N/A", meta_val),
        ],
        [
            Paragraph("INSPECTION PREMISES:", meta_label),
            Paragraph(f"<b>{seizure.premises_name}</b>", meta_val),
            Paragraph("CUSTODY STATUS:", meta_label),
            Paragraph(f"<b>{seizure.status}</b>", meta_val),
        ],
        [
            Paragraph("PREMISES ADDRESS:", meta_label),
            Paragraph(seizure.premises_address, meta_val),
            Paragraph("CUSTODY LOCATION:", meta_label),
            Paragraph(seizure.custody_location, meta_val),
        ],
        [
            Paragraph("INSPECTING OFFICER:", meta_label),
            Paragraph(f"{officer.name} ({officer.role})", meta_val),
            Paragraph("SHA-256 EVIDENCE SEAL:", meta_label),
            Paragraph(f"<font name='Courier' size='6'>{seizure.sha256_seal_hash[:24]}...</font>" if seizure.sha256_seal_hash else "N/A", meta_val),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[110, 160, 110, 142])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    # 3. Statutory Grounds for Seizure
    elements.append(Paragraph("<b>1. STATUTORY GROUNDS OF SEIZURE (SECTION 15)</b>", bold_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        f"The undersigned Legal Metrology Officer, having reasonable cause to believe that the packaged commodities "
        f"detailed hereunder are in violation of the Legal Metrology Act, 2009 and LMPC Rules, 2011, hereby seizes the same: "
        f"<br/><i>Grounds: {seizure.statutory_grounds}</i>",
        body_style,
    ))
    elements.append(Spacer(1, 8))

    # 4. Itemized Seizure Inventory Table
    elements.append(Paragraph("<b>2. INVENTORY OF SEIZED PACKAGED COMMODITIES & TEST SAMPLES DRAWN</b>", bold_body))
    elements.append(Spacer(1, 4))

    item_headers = ["Item", "Commodity Description", "Batch/Lot", "Net Qty", "MRP", "Total Seized", "Samples Drawn", "Seal Tag"]
    item_rows = [[Paragraph(f"<b>{h}</b>", meta_label) for h in item_headers]]

    for idx, item in enumerate(seizure.items):
        item_rows.append([
            Paragraph(str(idx + 1), meta_val),
            Paragraph(f"<b>{item.commodity_name}</b>" + (f"<br/><font size='6.5' color='#4A5568'>{item.brand_name}</font>" if item.brand_name else ""), meta_val),
            Paragraph(item.batch_lot_number or "N/A", meta_val),
            Paragraph(item.declared_net_quantity or "N/A", meta_val),
            Paragraph(item.mrp or "N/A", meta_val),
            Paragraph(f"<b>{item.total_packages_seized} pkgs</b>", meta_val),
            Paragraph(f"{item.sample_packages_taken} pkgs", meta_val),
            Paragraph(f"<font name='Courier' size='6'>{item.sample_seal_tag_number or 'N/A'}</font>", meta_val),
        ])

    t_items = Table(item_rows, colWidths=[24, 130, 60, 50, 60, 64, 64, 70])
    t_items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 10))

    # 5. Independent Pancha / Witnesses Section
    elements.append(Paragraph("<b>3. INDEPENDENT WITNESSES (PANCHAS) ATTESTATION</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "We, the undersigned independent witnesses, hereby declare that the search and seizure of above mentioned commodities "
        "was executed in our presence at the stated premises without any coercion or damage to other goods.",
        body_style,
    ))
    elements.append(Spacer(1, 6))

    witness_data = [
        [
            Paragraph("<b>WITNESS 1 (PANCHA 1)</b>", meta_label),
            Paragraph("<b>WITNESS 2 (PANCHA 2)</b>", meta_label),
        ],
        [
            Paragraph(f"Name: <b>{seizure.witness_1_name}</b><br/>Address: {seizure.witness_1_address}<br/>Phone: {seizure.witness_1_phone or 'N/A'}<br/><br/>Signature: _______________________", meta_val),
            Paragraph(f"Name: <b>{seizure.witness_2_name}</b><br/>Address: {seizure.witness_2_address}<br/>Phone: {seizure.witness_2_phone or 'N/A'}<br/><br/>Signature: _______________________", meta_val),
        ],
    ]
    t_witness = Table(witness_data, colWidths=[261, 261])
    t_witness.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_witness)
    elements.append(Spacer(1, 12))

    # 6. Signatures Block
    sig_data = [
        [
            Paragraph("<b>OCCUPIER / PERSON IN CHARGE</b><br/><br/><br/>Name: ______________________<br/>Date: ______________________", meta_val),
            Paragraph("<b>SEIZING LEGAL METROLOGY OFFICER</b><br/><br/><br/>Name: " + officer.name + "<br/>Designation: " + officer.role, meta_val),
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

