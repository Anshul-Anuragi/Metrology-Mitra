import hashlib
import io
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enforcement_notice import EnforcementNotice
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.enforcement import CompoundingCalculationResponse


def calculate_statutory_compounding_fee(
    offence_count: int,
    is_repeat_within_three_years: bool = False,
    violation_rule_codes: Optional[List[str]] = None,
    reference_date_str: Optional[str] = None,
) -> CompoundingCalculationResponse:
    """
    Statutory compounding assessment under Section 48 of Legal Metrology Act, 2009
    for violations of Section 36(1) (Manufacture, pack, import, or sale of non-standard packages).

    Hardened Guardrails:
    - Distinguishes statutory penalty ceiling vs discretionary officer compounding.
    - Does NOT hardcode unsupported/arbitrary per-rule fee increments.
    - If statutory basis is insufficient or out of temporal validity range -> returns NEEDS_REVIEW / NOT_DETERMINABLE.
    - Explicitly tags source legislation, version, and effective dates.
    """
    # 1. Temporal Validity Verification
    effective_start = date(2011, 4, 1)  # Legal Metrology Act 2009 entered into force on 1 April 2011
    eval_date = date.today()
    if reference_date_str:
        try:
            eval_date = datetime.strptime(reference_date_str[:10], "%Y-%m-%d").date()
        except Exception:
            eval_date = date.today()

    if eval_date < effective_start:
        return CompoundingCalculationResponse(
            offence_count=offence_count,
            assessment_status="NOT_DETERMINABLE",
            statutory_section="Standards of Weights and Measures Act, 1976 (Historical / Pre-2011)",
            compounding_amount_reference=None,
            base_compounding_fee=None,
            max_statutory_penalty=None,
            is_compoundable=None,
            amount_determinable=False,
            statutory_citations=["Standards of Weights and Measures Act, 1976"],
            source_legislation="Standards of Weights and Measures Act, 1976 (Repealed)",
            source_version="Historical Pre-2011",
            effective_from="1976-04-08",
            effective_to="2011-03-31",
            legal_rationale="The reference date precedes 01-04-2011 (entry into force of Legal Metrology Act, 2009). Historical compounding provisions require manual legal archival review.",
        )

    # 2. Statutory Assessment by Offence Tier
    count = offence_count

    if count == 1:
        # First statutory offence under Section 36(1): Fine up to ₹25,000
        # Under Section 48(1), compoundable by authorized officer up to statutory penalty ceiling.
        return CompoundingCalculationResponse(
            offence_count=1,
            assessment_status="COMPOUNDABLE",
            statutory_section="Section 36(1) read with Section 48(1), Legal Metrology Act, 2009",
            compounding_amount_reference=25000.0,
            base_compounding_fee=25000.0,
            max_statutory_penalty=25000.0,
            is_compoundable=True,
            amount_determinable=True,
            statutory_citations=["Section 36(1)", "Section 48(1)", "LMPC Rules, 2011"],
            source_legislation="Legal Metrology Act, 2009",
            source_version="Act No. 1 of 2010",
            effective_from="2011-04-01",
            effective_to=None,
            legal_rationale="First statutory offence under Section 36(1). Fully compoundable at the discretion of the authorized Legal Metrology Officer under Section 48(1) up to the statutory ceiling of ₹25,000.",
        )

    elif count == 2:
        # Second statutory offence under Section 36(1): Fine up to ₹50,000
        if is_repeat_within_three_years:
            # Under Section 48(2), no compounding if committed within 3 years of first compounding of same offence
            return CompoundingCalculationResponse(
                offence_count=2,
                assessment_status="NON_COMPOUNDABLE",
                statutory_section="Section 36(1) read with Section 48(2), Legal Metrology Act, 2009",
                compounding_amount_reference=None,
                base_compounding_fee=None,
                max_statutory_penalty=50000.0,
                is_compoundable=False,
                amount_determinable=False,
                statutory_citations=["Section 36(1)", "Section 48(2)"],
                source_legislation="Legal Metrology Act, 2009",
                source_version="Act No. 1 of 2010",
                effective_from="2011-04-01",
                effective_to=None,
                legal_rationale="Second offence committed within 3 years of earlier compounding. Non-compoundable under statutory bar of Section 48(2); prosecution mandatory before Judicial Magistrate.",
            )
        else:
            return CompoundingCalculationResponse(
                offence_count=2,
                assessment_status="COMPOUNDABLE",
                statutory_section="Section 36(1) read with Section 48(1), Legal Metrology Act, 2009",
                compounding_amount_reference=50000.0,
                base_compounding_fee=50000.0,
                max_statutory_penalty=50000.0,
                is_compoundable=True,
                amount_determinable=True,
                statutory_citations=["Section 36(1)", "Section 48(1)"],
                source_legislation="Legal Metrology Act, 2009",
                source_version="Act No. 1 of 2010",
                effective_from="2011-04-01",
                effective_to=None,
                legal_rationale="Second statutory offence beyond 3-year bar. Compoundable at the discretion of the authorized Legal Metrology Officer under Section 48(1) up to statutory ceiling of ₹50,000.",
            )

    elif count >= 3:
        # Third or subsequent offence: Imprisonment up to 1 year or fine up to ₹1,00,000 or both
        return CompoundingCalculationResponse(
            offence_count=count,
            assessment_status="NON_COMPOUNDABLE",
            statutory_section="Section 36(1) / Section 36(2) read with Section 48(2), Legal Metrology Act, 2009",
            compounding_amount_reference=None,
            base_compounding_fee=None,
            max_statutory_penalty=100000.0,
            is_compoundable=False,
            amount_determinable=False,
            statutory_citations=["Section 36(1)", "Section 48(2)", "Section 36(2)"],
            source_legislation="Legal Metrology Act, 2009",
            source_version="Act No. 1 of 2010",
            effective_from="2011-04-01",
            effective_to=None,
            legal_rationale="Subsequent recurring offence attracts penal imprisonment (up to 1 year or fine up to ₹1,00,000 or both). Non-compoundable under Section 48(2); requires formal prosecution in court of law.",
        )

    else:
        return CompoundingCalculationResponse(
            offence_count=count,
            assessment_status="NEEDS_REVIEW",
            statutory_section="Legal Metrology Act, 2009",
            compounding_amount_reference=None,
            base_compounding_fee=None,
            max_statutory_penalty=None,
            is_compoundable=None,
            amount_determinable=False,
            statutory_citations=["Legal Metrology Act, 2009"],
            source_legislation="Legal Metrology Act, 2009",
            source_version="Act No. 1 of 2010",
            effective_from="2011-04-01",
            effective_to=None,
            legal_rationale="Offence count or statutory provisions are unspecified or indeterminate. Case requires direct review by authorized Legal Metrology Officer.",
        )


def build_compounding_challan_pdf(
    notice: EnforcementNotice,
    inspection: Inspection,
    inspector: User,
) -> bytes:
    """
    Renders a draft Section 48 Compounding Assessment & Section 36 Memorandum in PDF.
    Explicitly branded as DRAFT / REFERENCE ONLY — SUBJECT TO AUTHORIZED OFFICER REVIEW.
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
    text_dark = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#EDF2F7")
    disclaimer_bg = colors.HexColor("#FEF3C7")

    title_style = ParagraphStyle(
        "NoticeTitle",
        parent=styles["Heading1"],
        fontSize=12,
        leading=15,
        textColor=primary_color,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    sub_title = ParagraphStyle(
        "NoticeSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=danger_color,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "NoticeBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica",
    )
    body_bold = ParagraphStyle(
        "NoticeBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=text_dark,
        fontName="Helvetica-Bold",
    )

    story = []

    # 1. Draft Notice Disclaimer Header
    story.append(Paragraph("METROLOGYMITRA — STATUTORY DECISION SUPPORT RECORD", title_style))
    story.append(Paragraph("DRAFT SECTION 48 COMPOUNDING ASSESSMENT & SHOW-CAUSE MEMO", sub_title))
    story.append(Paragraph(
        "<b>[DRAFT / REFERENCE ONLY — SUBJECT TO FORMAL AUTHORIZED OFFICER REVIEW & EXECUTION]</b>",
        ParagraphStyle("DraftWarn", parent=body_style, alignment=1, textColor=danger_color, fontName="Helvetica-Bold"),
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8))

    # 2. Case Details Grid
    meta_rows = [
        [
            Paragraph("<b>Draft Notice ID:</b>", body_style),
            Paragraph(notice.notice_number, body_bold),
            Paragraph("<b>Assessment Date:</b>", body_style),
            Paragraph(notice.created_at.strftime("%Y-%m-%d %H:%M UTC") if notice.created_at else "N/A", body_style),
        ],
        [
            Paragraph("<b>Inspection ID:</b>", body_style),
            Paragraph(str(inspection.id)[:18] + "...", body_style),
            Paragraph("<b>Document Type:</b>", body_style),
            Paragraph(f"<b>{notice.notice_type} (DRAFT)</b>", body_bold),
        ],
        [
            Paragraph("<b>Establishment / Store:</b>", body_style),
            Paragraph(inspection.store_name or "N/A", body_style),
            Paragraph("<b>Jurisdiction:</b>", body_style),
            Paragraph(f"{inspection.district or 'N/A'}, {inspection.state or 'N/A'}", body_style),
        ],
        [
            Paragraph("<b>Reviewing Officer:</b>", body_style),
            Paragraph(f"{inspector.name} ({inspector.role.value})", body_style),
            Paragraph("<b>Offence Number:</b>", body_style),
            Paragraph(f"Offence #{notice.offence_count} (Section 36(1))", body_bold),
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

    # 3. Statutory Compounding Assessment
    story.append(Paragraph("1. STATUTORY PROVISIONS & COMPOUNDING ASSESSMENT REFERENCE", ParagraphStyle("H2", parent=title_style, alignment=0, fontSize=9, textColor=primary_color)))
    fee_display = f"₹ {notice.compounding_amount:,.2f} (Statutory Ceiling)" if notice.compounding_amount else "Discretionary / To be assessed by Officer"
    sections_display = ", ".join(notice.statutory_sections) if isinstance(notice.statutory_sections, list) else "Section 36(1), LMPC Rules 2011"

    calc_rows = [
        [Paragraph("<b>Statutory Offence Basis:</b>", body_bold), Paragraph(sections_display, body_style)],
        [Paragraph("<b>Regulatory Version / Source:</b>", body_bold), Paragraph("Legal Metrology Act, 2009 (Act No. 1 of 2010), Effective 01-04-2011", body_style)],
        [Paragraph("<b>Assessment Status:</b>", body_bold), Paragraph(f"<b>{notice.status} (ASSESSMENT REFERENCE)</b>", body_style)],
        [Paragraph("<b>Statutory Compounding Ceiling (Sec 48):</b>", body_bold), Paragraph(f"<font color='{danger_color.hexval()}'><b>{fee_display}</b></font>", body_bold)],
        [Paragraph("<b>Draft Challan Reference / Notes:</b>", body_bold), Paragraph(notice.challan_reference or "Pending Officer Determination", body_style)],
        [Paragraph("<b>Officer Observations:</b>", body_bold), Paragraph(notice.officer_remarks or "Non-compliance observed during field label inspection.", body_style)],
    ]

    t_calc = Table(calc_rows, colWidths=[2.6 * inch, 4.6 * inch])
    t_calc.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, light_bg]),
    ]))
    story.append(t_calc)
    story.append(Spacer(1, 10))

    # 4. Mandatory Statutory Disclaimer Table
    disc_data = [
        [
            Paragraph(
                "<b>MANDATORY STATUTORY DISCLAIMER & NON-ISSUANCE NOTICE:</b><br/>"
                "This document is an automated decision-support draft generated by MetrologyMitra for the assisting "
                "Legal Metrology Officer. It does NOT constitute an authoritative judicial order, final challan receipt, "
                "or executed compounding approval until formally evaluated, determined, signed, and issued by an "
                "authorized Legal Metrology Officer under Section 48 of the Legal Metrology Act, 2009.",
                ParagraphStyle("DiscBold", parent=body_style, fontSize=7, leading=10, textColor=colors.HexColor("#744210")),
            )
        ]
    ]
    t_disc = Table(disc_data, colWidths=[7.2 * inch])
    t_disc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), disclaimer_bg),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#D97706")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_disc)
    story.append(Spacer(1, 8))

    # 5. Fingerprint
    checksum = hashlib.sha256(f"{notice.id}:{notice.notice_number}:{notice.compounding_amount}".encode()).hexdigest()
    foot_data = [
        [
            Paragraph("<b>Digital Record Integrity Hash (SHA-256):</b>", body_style),
            Paragraph(f"<font name='Courier'>{checksum}</font>", body_style),
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
