import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
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
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import CheckResult, ComplianceResult, ReportType, UserRole, ViolationSeverity
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.report import Report
from app.models.user import User
from app.models.violation import Violation
from app.schemas.report import JSONExportBundle
from app.services.storage import storage_service


async def generate_report_number(db: AsyncSession, state_code: Optional[str] = None) -> str:
    """
    Generates a unique, database-backed report number in format LMPC/YYYY/STATE/SEQ.
    """
    current_year = datetime.now(timezone.utc).year
    state = (state_code or "DL").strip().upper()[:2]
    if len(state) < 2:
        state = "DL"

    prefix = f"LMPC/{current_year}/{state}/"

    stmt = select(func.count(Report.id)).where(Report.report_number.like(f"{prefix}%"))
    count_res = await db.execute(stmt)
    seq = (count_res.scalar_one() or 0) + 1

    # Format sequence as 4 digits
    report_num = f"{prefix}{seq:04d}"

    # Verify uniqueness in case of race condition
    while True:
        check_stmt = select(Report).where(Report.report_number == report_num)
        exists = (await db.execute(check_stmt)).scalar_one_or_none()
        if not exists:
            break
        seq += 1
        report_num = f"{prefix}{seq:04d}"

    return report_num


def compute_sha256_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_pdf_report(
    inspection: Inspection,
    inspector: User,
    declaration: Optional[Declaration],
    checks: List[ComplianceCheck],
    violations: List[Violation],
    evidence_items: List[Evidence],
    report_number: str,
    report_type: ReportType,
) -> bytes:
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
    secondary_color = colors.HexColor("#2B6CB0")
    text_dark = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#EDF2F7")
    danger_color = colors.HexColor("#C53030")
    success_color = colors.HexColor("#22543D")
    warning_color = colors.HexColor("#B7791F")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=14,
        leading=17,
        textColor=primary_color,
        alignment=1,  # Center
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        fontName="Helvetica-Oblique",
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=primary_color,
        fontName="Helvetica-Bold",
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=text_dark,
        fontName="Helvetica",
    )
    body_bold = ParagraphStyle(
        "BodyBoldCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=text_dark,
        fontName="Helvetica-Bold",
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#718096"),
        alignment=1,
        fontName="Helvetica-Oblique",
    )

    story = []

    # 1. Header & Document Title
    is_sec36_notice = report_type == ReportType.NOTICE_SEC36
    if is_sec36_notice:
        story.append(Paragraph("LEGAL METROLOGY ACT, 2009 — SECTION 36", title_style))
        story.append(Paragraph("DRAFT NOTICE OF NON-COMPLIANCE FOR INSPECTOR REVIEW", ParagraphStyle("RedSub", parent=title_style, textColor=danger_color, fontSize=12, leading=15)))
        story.append(Paragraph("MetrologyMitra — Computer-Assisted Decision Support (Requires Authorized Inspector Verification)", subtitle_style))
    else:
        story.append(Paragraph("LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", title_style))
        story.append(Paragraph("DRAFT INSPECTION COMPLIANCE MEMO & RECORD", ParagraphStyle("SubTitle2", parent=title_style, textColor=secondary_color, fontSize=12, leading=15)))
        story.append(Paragraph("MetrologyMitra — For Authorized Inspector Review Only (Decision-Support Prototype)", subtitle_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8))

    # 2. Metadata Grid Table
    overall_color = danger_color if inspection.overall_result == ComplianceResult.NON_COMPLIANT else (success_color if inspection.overall_result == ComplianceResult.COMPLIANT else warning_color)
    created_dt = inspection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if inspection.created_at else "N/A"

    meta_data = [
        [
            Paragraph("<b>Report Number:</b>", body_style),
            Paragraph(report_number, body_bold),
            Paragraph("<b>Inspection Date:</b>", body_style),
            Paragraph(created_dt, body_style),
        ],
        [
            Paragraph("<b>Inspection ID:</b>", body_style),
            Paragraph(str(inspection.id)[:18] + "...", body_style),
            Paragraph("<b>Overall Result:</b>", body_style),
            Paragraph(f"<font color='{overall_color.hexval()}'><b>{inspection.overall_result.value}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Store Name:</b>", body_style),
            Paragraph(inspection.store_name or "N/A", body_style),
            Paragraph("<b>Inspector:</b>", body_style),
            Paragraph(f"{inspector.name} ({inspector.role.value})", body_style),
        ],
        [
            Paragraph("<b>Location / District:</b>", body_style),
            Paragraph(f"{inspection.district or 'N/A'}, {inspection.state or 'N/A'}", body_style),
            Paragraph("<b>GPS Coordinates:</b>", body_style),
            Paragraph(f"{inspection.gps_latitude or 'N/A'}, {inspection.gps_longitude or 'N/A'}", body_style),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[1.3 * inch, 2.3 * inch, 1.3 * inch, 2.3 * inch])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. Product & Declarations Summary
    story.append(Paragraph("1. STATUTORY DECLARATION SUMMARY (LMPC RULE 6)", section_heading))
    decl_rows = [
        [
            Paragraph("<b>Statutory Declaration Field</b>", body_bold),
            Paragraph("<b>Observed / Extracted Value</b>", body_bold),
            Paragraph("<b>Verification Status</b>", body_bold),
        ]
    ]

    human_verified_badge = "Human Verified" if (declaration and declaration.is_human_verified) else "OCR Extracted (Pending Review)"
    decl_fields = [
        ("Commodity Name (Rule 6(1)(b))", getattr(declaration, "commodity_name", None)),
        ("Manufacturer / Packer (Rule 6(1)(a))", getattr(declaration, "manufacturer_name", None) or getattr(declaration, "packer_name", None)),
        ("Address (Rule 6(1)(a))", getattr(declaration, "address", None)),
        ("Net Quantity (Rule 6(1)(c) & Rule 12)", getattr(declaration, "net_quantity", None)),
        ("Maximum Retail Price (Rule 6(1)(e))", getattr(declaration, "mrp", None)),
        ("Unit Sale Price (Rule 6(11))", getattr(declaration, "unit_sale_price", None)),
        ("Month & Year of Mfg/Packing (Rule 6(1)(d))", getattr(declaration, "manufacturing_date", None) or getattr(declaration, "packing_date", None)),
        ("Best Before / Expiry (Rule 6(1)(d) proviso)", getattr(declaration, "expiry_date", None) or getattr(declaration, "best_before", None)),
        ("Country of Origin (Rule 6(1)(g))", getattr(declaration, "country_of_origin", None)),
        ("Consumer Care Helpline / Email (Rule 6(1)(n))", getattr(declaration, "consumer_care", None) or getattr(declaration, "consumer_care_phone", None)),
    ]

    for label, val in decl_fields:
        val_text = val if val else "<font color='#A0AEC0'><i>NOT DECLARED</i></font>"
        decl_rows.append([
            Paragraph(label, body_style),
            Paragraph(val_text, body_style),
            Paragraph(human_verified_badge, body_style),
        ])

    t_decl = Table(decl_rows, colWidths=[2.6 * inch, 3.2 * inch, 1.4 * inch])
    t_decl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 3.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
    ]))
    story.append(t_decl)
    story.append(Spacer(1, 10))

    # 4. Compliance Rule Matrix
    story.append(Paragraph("2. STATUTORY COMPLIANCE EVALUATION MATRIX", section_heading))
    story.append(Paragraph("<i>18 encoded compliance checks based on selected provisions of the Legal Metrology (Packaged Commodities) Rules, 2011 and applicable amendments.</i>", ParagraphStyle("MatrixSub", parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#4A5568"))))
    story.append(Spacer(1, 4))
    check_rows = [
        [
            Paragraph("<b>Rule Code</b>", body_bold),
            Paragraph("<b>Statutory Reference</b>", body_bold),
            Paragraph("<b>Rule Description</b>", body_bold),
            Paragraph("<b>Observed</b>", body_bold),
            Paragraph("<b>Result</b>", body_bold),
        ]
    ]

    for c in checks:
        r_code = c.legal_rule.rule_code if c.legal_rule else "LMPC-RULE"
        r_ref = c.legal_rule.source_reference if c.legal_rule else "LMPC Rules, 2011"
        r_title = c.legal_rule.title if c.legal_rule else (c.field_name or "Declaration Check")
        res_color = success_color if c.result == CheckResult.PASS else (danger_color if c.result == CheckResult.FAIL else warning_color)

        check_rows.append([
            Paragraph(r_code, body_style),
            Paragraph(r_ref, body_style),
            Paragraph(r_title, body_style),
            Paragraph(c.observed_value or "NOT DECLARED", body_style),
            Paragraph(f"<font color='{res_color.hexval()}'><b>{c.result.value}</b></font>", body_style),
        ])

    t_checks = Table(check_rows, colWidths=[1.2 * inch, 1.6 * inch, 2.2 * inch, 1.3 * inch, 0.9 * inch])
    t_checks.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 3.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
    ]))
    story.append(t_checks)
    story.append(Spacer(1, 10))

    # 5. Detected Violations & Statutory Citations
    if violations:
        story.append(Paragraph("3. DETECTED STATUTORY VIOLATIONS & LEGAL PROVISIONS", section_heading))
        viol_rows = [
            [
                Paragraph("<b>Severity</b>", body_bold),
                Paragraph("<b>Violation Finding</b>", body_bold),
                Paragraph("<b>Statutory Citation</b>", body_bold),
                Paragraph("<b>Legal Penalty Provision</b>", body_bold),
            ]
        ]
        for v in violations:
            sev_color = danger_color if v.severity in (ViolationSeverity.HIGH, ViolationSeverity.CRITICAL) else (warning_color if v.severity == ViolationSeverity.MEDIUM else primary_color)
            viol_rows.append([
                Paragraph(f"<font color='{sev_color.hexval()}'><b>{v.severity.value}</b></font>", body_style),
                Paragraph(f"<b>{v.title}</b><br/>{v.description}", body_style),
                Paragraph(v.rule_citation or "LMPC Rules, 2011", body_style),
                Paragraph("Section 36(1), Legal Metrology Act, 2009<br/><i>(Applicable penalty to be determined upon inspector review)</i>", body_style),
            ])

        t_viols = Table(viol_rows, colWidths=[0.9 * inch, 2.7 * inch, 1.8 * inch, 1.8 * inch])
        t_viols.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), danger_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
        ]))
        story.append(t_viols)
        story.append(Spacer(1, 10))

    # 6. Visual Evidence References
    story.append(Paragraph("4. VISUAL EVIDENCE REFERENCES", section_heading))
    if evidence_items:
        ev_rows = [
            [
                Paragraph("<b>Evidence Type</b>", body_bold),
                Paragraph("<b>Description</b>", body_bold),
                Paragraph("<b>Spatial Bounding Box [x, y, w, h]</b>", body_bold),
            ]
        ]
        for ev in evidence_items[:8]:  # Limit top 8 evidence items for clean single/double page fit
            bbox_str = f"x={ev.bounding_box.get('x')}, y={ev.bounding_box.get('y')}, w={ev.bounding_box.get('width')}, h={ev.bounding_box.get('height')}" if ev.bounding_box else "N/A (Textual proof)"
            ev_rows.append([
                Paragraph(ev.evidence_type.value, body_style),
                Paragraph(ev.description or "Evidence record", body_style),
                Paragraph(bbox_str, body_style),
            ])

        t_ev = Table(ev_rows, colWidths=[1.5 * inch, 3.7 * inch, 2.0 * inch])
        t_ev.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("PADDING", (0, 0), (-1, -1), 3.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
        ]))
        story.append(t_ev)
    else:
        story.append(Paragraph("<i>No visual evidence records attached to this inspection.</i>", body_style))

    story.append(Spacer(1, 12))

    # 7. Verification / Checksum Box & Legal Disclaimer
    checksum_val = hashlib.sha256(f"{inspection.id}:{report_number}:{created_dt}".encode()).hexdigest()
    footer_data = [
        [
            Paragraph("<b>Digital Verification Fingerprint (SHA-256):</b>", body_style),
            Paragraph(f"<font name='Courier'>{checksum_val}</font>", body_style),
        ],
        [
            Paragraph("<b>Generated By:</b>", body_style),
            Paragraph(f"{inspector.name} ({inspector.email}) — Role: {inspector.role.value}", body_style),
        ],
        [
            Paragraph("<b>Legal Notice Disclaimer:</b>", body_style),
            Paragraph(
                "This document is a computer-assisted draft inspection memo generated from optical text extractions and "
                "deterministic legal metrology rule evaluations. It does NOT constitute an autonomous government sanction or "
                "final adjudication. All findings and observed values require physical verification by an authorized Legal Metrology Officer.",
                disclaimer_style,
            ),
        ],
    ]
    t_foot = Table(footer_data, colWidths=[2.2 * inch, 5.0 * inch])
    t_foot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(KeepTogether(t_foot))

    doc.build(story)
    return buffer.getvalue()


def _build_json_export(
    inspection: Inspection,
    inspector: User,
    declaration: Optional[Declaration],
    checks: List[ComplianceCheck],
    violations: List[Violation],
    evidence_items: List[Evidence],
    ocr_results: List[OCRResult],
    report_number: str,
    report_type: ReportType,
) -> JSONExportBundle:
    inspection_dict = {
        "id": str(inspection.id),
        "status": inspection.status.value,
        "overall_result": inspection.overall_result.value,
        "store_name": inspection.store_name,
        "store_address": inspection.store_address,
        "district": inspection.district,
        "state": inspection.state,
        "gps_latitude": inspection.gps_latitude,
        "gps_longitude": inspection.gps_longitude,
        "started_at": inspection.started_at.isoformat() if inspection.started_at else None,
        "completed_at": inspection.completed_at.isoformat() if inspection.completed_at else None,
        "created_at": inspection.created_at.isoformat() if inspection.created_at else None,
    }
    inspector_dict = {
        "id": str(inspector.id),
        "name": inspector.name,
        "email": inspector.email,
        "role": inspector.role.value,
    }
    decl_dict = None
    if declaration:
        decl_dict = {
            "id": str(declaration.id),
            "commodity_name": declaration.commodity_name,
            "manufacturer_name": declaration.manufacturer_name,
            "packer_name": declaration.packer_name,
            "importer_name": declaration.importer_name,
            "address": declaration.address,
            "net_quantity": declaration.net_quantity,
            "mrp": declaration.mrp,
            "unit_sale_price": declaration.unit_sale_price,
            "manufacturing_date": declaration.manufacturing_date,
            "packing_date": declaration.packing_date,
            "expiry_date": declaration.expiry_date,
            "best_before": declaration.best_before,
            "country_of_origin": declaration.country_of_origin,
            "is_imported": declaration.is_imported,
            "consumer_care": declaration.consumer_care,
            "is_human_verified": declaration.is_human_verified,
            "field_confidences": declaration.field_confidences,
        }

    checks_list = [
        {
            "id": str(c.id),
            "rule_code": c.legal_rule.rule_code if c.legal_rule else None,
            "rule_title": c.legal_rule.title if c.legal_rule else None,
            "statutory_reference": c.legal_rule.source_reference if c.legal_rule else None,
            "field_name": c.field_name,
            "observed_value": c.observed_value,
            "result": c.result.value,
            "confidence": c.confidence,
            "reason": c.reason,
            "checked_at": c.checked_at.isoformat() if c.checked_at else None,
        }
        for c in checks
    ]

    violations_list = [
        {
            "id": str(v.id),
            "compliance_check_id": str(v.compliance_check_id),
            "severity": v.severity.value,
            "title": v.title,
            "description": v.description,
            "rule_citation": v.rule_citation,
            "status": v.status.value,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in violations
    ]

    evidence_list = [
        {
            "id": str(e.id),
            "compliance_check_id": str(e.compliance_check_id) if e.compliance_check_id else None,
            "violation_id": str(e.violation_id) if e.violation_id else None,
            "image_id": str(e.image_id) if e.image_id else None,
            "evidence_type": e.evidence_type.value,
            "description": e.description,
            "bounding_box": e.bounding_box,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evidence_items
    ]

    ocr_list = [
        {
            "id": str(o.id),
            "image_id": str(o.image_id),
            "raw_text": o.raw_text,
            "confidence": o.confidence,
            "engine": o.engine,
            "processing_time_ms": o.processing_time_ms,
        }
        for o in ocr_results
    ]

    payload_str = json.dumps({
        "inspection_id": str(inspection.id),
        "report_number": report_number,
        "created_at": inspection_dict["created_at"],
    }, sort_keys=True)
    checksum = compute_sha256_checksum(payload_str.encode())

    return JSONExportBundle(
        export_version="1.0.0",
        document_type="LEGAL_METROLOGY_INSPECTION_RECORD_DRAFT",
        generated_at=datetime.now(timezone.utc),
        checksum_sha256=checksum,
        report_number=report_number,
        report_type=report_type,
        inspection=inspection_dict,
        inspector=inspector_dict,
        declaration=decl_dict,
        compliance_checks=checks_list,
        violations=violations_list,
        evidence_items=evidence_list,
        ocr_results=ocr_list,
    )


async def create_inspection_report(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    report_type: ReportType,
    current_user: User,
) -> Tuple[Report, bytes, str]:
    """
    Builds, renders, persists, and logs an inspection report entirely from persisted DB data.
    """
    # 1. Fetch Inspection with all related entities
    stmt = (
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            selectinload(Inspection.inspector),
            selectinload(Inspection.declaration),
            selectinload(Inspection.images),
        )
    )
    res = await db.execute(stmt)
    inspection = res.scalar_one_or_none()

    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found.",
        )

    # 2. RBAC Ownership Verification
    if current_user.role == UserRole.INSPECTOR and inspection.inspector_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: You can only generate reports for your own inspections.",
        )

    # 3. Load Compliance Checks with Legal Rules
    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.inspection_id == inspection_id)
        .options(selectinload(ComplianceCheck.legal_rule))
        .order_by(ComplianceCheck.checked_at.asc())
    )
    checks = (await db.execute(checks_stmt)).scalars().all()

    # 4. Load Violations
    viols_stmt = (
        select(Violation)
        .where(Violation.inspection_id == inspection_id)
        .order_by(Violation.created_at.asc())
    )
    violations = (await db.execute(viols_stmt)).scalars().all()

    # 5. Load Evidence Items
    ev_stmt = (
        select(Evidence)
        .where(Evidence.inspection_id == inspection_id)
        .order_by(Evidence.created_at.asc())
    )
    evidence_items = (await db.execute(ev_stmt)).scalars().all()

    # 6. Load OCR Results
    ocr_stmt = (
        select(OCRResult)
        .join(InspectionImage, OCRResult.image_id == InspectionImage.id)
        .where(InspectionImage.inspection_id == inspection_id)
    )
    ocr_results = (await db.execute(ocr_stmt)).scalars().all()

    # 7. Validate NOTICE_SEC36 applicability
    if report_type == ReportType.NOTICE_SEC36:
        has_violations = len(violations) > 0 or any(c.result == CheckResult.FAIL for c in checks)
        if not has_violations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate Section 36 Notice of Non-Compliance: Inspection has no failed compliance checks or violations.",
            )

    # 8. Generate Unique Report Number
    report_number = await generate_report_number(db, inspection.state)

    # 9. Render Document Bytes
    inspector = inspection.inspector or current_user
    declaration = inspection.declaration

    if report_type in (ReportType.PDF, ReportType.NOTICE_SEC36, ReportType.INSPECTION_MEMO):
        doc_bytes = _build_pdf_report(
            inspection=inspection,
            inspector=inspector,
            declaration=declaration,
            checks=checks,
            violations=violations,
            evidence_items=evidence_items,
            report_number=report_number,
            report_type=report_type,
        )
        ext = "pdf"
        media_type = "application/pdf"
    elif report_type == ReportType.JSON:
        json_bundle = _build_json_export(
            inspection=inspection,
            inspector=inspector,
            declaration=declaration,
            checks=checks,
            violations=violations,
            evidence_items=evidence_items,
            ocr_results=ocr_results,
            report_number=report_number,
            report_type=report_type,
        )
        doc_bytes = json_bundle.model_dump_json(indent=2).encode("utf-8")
        ext = "json"
        media_type = "application/json"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported report type: '{report_type}'",
        )

    # 10. Persist File to Storage
    filename = f"{report_number.replace('/', '_')}.{ext}"
    saved_url = await storage_service.save_report(
        file_bytes=doc_bytes,
        filename=filename,
        inspection_id=inspection_id,
    )

    # 11. Create Record in Reports Table
    report = Report(
        inspection_id=inspection_id,
        report_number=report_number,
        report_type=report_type,
        file_url=saved_url,
        generated_by=current_user.id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report, doc_bytes, media_type

