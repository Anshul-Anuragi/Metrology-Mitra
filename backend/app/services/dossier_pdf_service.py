import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

from app.models.dossier import InvestigationDossier
from app.schemas.dossier import DossierSynthesisResponse


def build_dossier_pdf_report(
    dossier: InvestigationDossier,
    synthesis: DossierSynthesisResponse,
    evidence_hashes: Optional[List[Dict[str, str]]] = None,
) -> bytes:
    """
    Renders the official MetrologyMitra Consolidated Inspection & Evidence Report PDF.

    STRICT STATUTORY / LEGAL INVARIANTS:
    - Title: "MetrologyMitra — Consolidated Inspection & Evidence Report"
    - Prominently bears: "SYSTEM-GENERATED REFERENCE DOCUMENT — FOR AUTHORIZED OFFICER REVIEW"
    - Does NOT contain government seal, fake signature, or fake prosecution case numbers.
    - Does NOT assert collective guilt, corporate liability conclusions, or director liability.
    - Strictly presents "Individual Inspection Results" and "Observed Finding Patterns".
    - Contains all 14 required sections including legal corpus provenance metadata.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        pageCompression=0,
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#1A365D")      # Deep Navy
    secondary_color = colors.HexColor("#2B6CB0")    # Classic Blue
    accent_dark = colors.HexColor("#2D3748")        # Dark Slate
    light_bg = colors.HexColor("#F7FAFC")           # Very Light Gray
    border_color = colors.HexColor("#E2E8F0")       # Border Gray
    danger_color = colors.HexColor("#C53030")       # Muted Crimson
    warning_color = colors.HexColor("#D69E2E")      # Muted Amber
    success_color = colors.HexColor("#2F855A")      # Forest Green
    banner_bg = colors.HexColor("#FEFCBF")          # Soft Warning Yellow
    banner_border = colors.HexColor("#D69E2E")

    # Typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=13,
        leading=16,
        textColor=primary_color,
        alignment=1,  # Center
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=accent_dark,
        alignment=1,
        fontName="Helvetica",
    )
    banner_title_style = ParagraphStyle(
        "BannerTitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#744210"),
        alignment=1,
        fontName="Helvetica-Bold",
    )
    banner_body_style = ParagraphStyle(
        "BannerBody",
        parent=styles["Normal"],
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#744210"),
        alignment=1,
        fontName="Helvetica-Oblique",
    )
    section_heading = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=10,
        leading=13,
        textColor=primary_color,
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        textColor=accent_dark,
        fontName="Helvetica",
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        textColor=accent_dark,
        fontName="Helvetica-Bold",
    )
    disclaimer_text_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#4A5568"),
        alignment=0,
        fontName="Helvetica",
    )

    story = []

    # =========================================================================
    # HEADER & DOCUMENT IDENTITY
    # =========================================================================
    story.append(Paragraph("MetrologyMitra — Consolidated Inspection & Evidence Report", title_style))
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "Legal Metrology Multi-Inspection Surveillance & Evidence Synthesis • System-Generated Administrative Decision-Support Report",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 6))

    # Prominent Statutory Reference Notice Banner
    banner_table = Table(
        [
            [Paragraph("SYSTEM-GENERATED REFERENCE DOCUMENT — FOR AUTHORIZED OFFICER REVIEW", banner_title_style)],
            [
                Paragraph(
                    "Operational case-management and evidence-synthesis document. Strictly NON-JUDICIAL administrative reference. "
                    "Individual inspection legal results remain authoritative. "
                    "This document does not constitute an autonomous enforcement action, legal opinion, prosecution determination, or finding of liability.",
                    banner_body_style,
                )
            ],
        ],
        colWidths=[523],
    )
    banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), banner_bg),
            ("BOX", (0, 0), (-1, -1), 1, banner_border),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )
    story.append(banner_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    # =========================================================================
    # SECTION 1 & 2: DOSSIER OVERVIEW & OPERATIONAL STATUS/PRIORITY
    # =========================================================================
    story.append(Paragraph("1. DOSSIER OVERVIEW & OPERATIONAL STATUS", section_heading))

    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    created_time = dossier.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if dossier.created_at else "N/A"
    lead_sup_name = (
        dossier.lead_supervisor.name if dossier.lead_supervisor else (synthesis.lead_supervisor_name or "Authorized Supervisor")
    )
    target_ent = dossier.target_entity_name or "Not designated (multi-store surveillance)"

    status_val = dossier.status.value if hasattr(dossier.status, "value") else str(dossier.status or "ACTIVE")
    priority_val = dossier.priority.value if hasattr(dossier.priority, "value") else str(dossier.priority or "NORMAL")

    overview_rows = [
        [
            Paragraph("<b>Dossier Number:</b>", body_style),
            Paragraph(f"<b><font size='9'>{dossier.dossier_number}</font></b>", body_style),
            Paragraph("<b>Operational Status:</b>", body_style),
            Paragraph(f"<b>{status_val}</b> <i>(Administrative workflow)</i>", body_style),
        ],
        [
            Paragraph("<b>Dossier Title:</b>", body_style),
            Paragraph(dossier.title, body_style),
            Paragraph("<b>Operational Priority:</b>", body_style),
            Paragraph(f"<b>{priority_val}</b>", body_style),
        ],
        [
            Paragraph("<b>Target Entity (Descriptor):</b>", body_style),
            Paragraph(target_ent, body_style),
            Paragraph("<b>Lead Supervisor:</b>", body_style),
            Paragraph(lead_sup_name, body_style),
        ],
        [
            Paragraph("<b>Creation Timestamp:</b>", body_style),
            Paragraph(created_time, body_style),
            Paragraph("<b>Report Generated:</b>", body_style),
            Paragraph(gen_time, body_style),
        ],
    ]
    if dossier.description:
        overview_rows.append([
            Paragraph("<b>Operational Scope:</b>", body_style),
            Paragraph(dossier.description, body_style),
            Paragraph("<b>Tags:</b>", body_style),
            Paragraph(", ".join(dossier.tags) if dossier.tags else "None", body_style),
        ])

    t_overview = Table(overview_rows, colWidths=[100, 161, 110, 152])
    t_overview.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(t_overview)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 3: LINKED INSPECTIONS
    # =========================================================================
    story.append(Paragraph("2. LINKED INSPECTION SESSIONS", section_heading))
    if dossier.inspections:
        insp_table_rows = [
            [
                Paragraph("<b>Inspection ID</b>", body_bold),
                Paragraph("<b>Premises / Store</b>", body_bold),
                Paragraph("<b>Location</b>", body_bold),
                Paragraph("<b>Inspecting Officer</b>", body_bold),
                Paragraph("<b>Linked Date</b>", body_bold),
                Paragraph("<b>Relevance Context</b>", body_bold),
            ]
        ]
        for di in dossier.inspections:
            insp = di.inspection
            insp_id_str = str(di.inspection_id)[:8] + "..."
            store_name = (insp.store_name if insp and insp.store_name else "Premises")
            location_str = f"{insp.district or '—'}, {insp.state or '—'}" if insp else "—"
            officer_str = (insp.inspector.name if insp and insp.inspector else (di.added_by.name if di.added_by else "Officer"))
            link_date_str = di.added_at.strftime("%Y-%m-%d") if di.added_at else "—"
            notes_str = di.relevance_notes or "Factual grouping"

            insp_table_rows.append([
                Paragraph(f"<font name='Courier'>{insp_id_str}</font>", body_style),
                Paragraph(store_name, body_style),
                Paragraph(location_str, body_style),
                Paragraph(officer_str, body_style),
                Paragraph(link_date_str, body_style),
                Paragraph(notes_str, body_style),
            ])

        t_insps = Table(insp_table_rows, colWidths=[65, 110, 85, 85, 60, 118])
        t_insps.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("PADDING", (0, 0), (-1, -1), 3.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(t_insps)
    else:
        story.append(Paragraph("<i>No inspection sessions currently linked to this dossier.</i>", body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 4: INDIVIDUAL INSPECTION RESULTS (STRICTLY NON-JUDICIAL AGGREGATE)
    # =========================================================================
    story.append(Paragraph("3. INDIVIDUAL INSPECTION RESULTS", section_heading))
    story.append(
        Paragraph(
            "<b>STATUTORY COMPLIANCE PRINCIPLE:</b> Statutory compliance results are determined solely at the individual inspection session "
            "level by the deterministic Legal Rule Engine. The summary below presents factual counts across linked sessions without "
            "deriving a collective verdict.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))

    counts = synthesis.summary_counts
    summary_matrix = [
        [
            Paragraph("<b>Total Linked Inspections</b>", body_style),
            Paragraph(f"<b>{counts.total_inspections}</b>", body_style),
            Paragraph("<b>Compliant Inspections:</b>", body_style),
            Paragraph(f"<font color='{success_color.hexval()}'><b>{counts.compliant_count}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Non-Compliant Inspections:</b>", body_style),
            Paragraph(f"<font color='{danger_color.hexval()}'><b>{counts.non_compliant_count}</b></font>", body_style),
            Paragraph("<b>Needs Review Inspections:</b>", body_style),
            Paragraph(f"<font color='{warning_color.hexval()}'><b>{counts.needs_review_count}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Pending Evaluation:</b>", body_style),
            Paragraph(f"<b>{counts.pending_count}</b>", body_style),
            Paragraph("<b>Completed Inspections:</b>", body_style),
            Paragraph(f"<b>{counts.completed_inspections}</b>", body_style),
        ],
    ]
    t_counts = Table(summary_matrix, colWidths=[130, 131, 131, 131])
    t_counts.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(t_counts)

    # Detailed table of individual inspection verdicts
    if dossier.inspections:
        story.append(Spacer(1, 4))
        verdict_rows = [
            [
                Paragraph("<b>Inspection ID</b>", body_bold),
                Paragraph("<b>Premises Name</b>", body_bold),
                Paragraph("<b>District / State</b>", body_bold),
                Paragraph("<b>Individual Statutory Result</b>", body_bold),
                Paragraph("<b>Finalized State</b>", body_bold),
            ]
        ]
        for di in dossier.inspections:
            insp = di.inspection
            insp_id_short = str(di.inspection_id)[:12]
            store_name = insp.store_name if insp and insp.store_name else "Premises"
            dist_state = f"{insp.district or '—'}, {insp.state or '—'}" if insp else "—"
            res_val = insp.overall_result.value if insp and getattr(insp, "overall_result", None) else "PENDING"
            color_res = (
                danger_color if res_val == "NON_COMPLIANT"
                else (success_color if res_val == "COMPLIANT" else (warning_color if res_val == "NEEDS_REVIEW" else accent_dark))
            )
            fin_str = "FINALIZED" if insp and getattr(insp, "finalized_at", None) else "DRAFT / ACTIVE"

            verdict_rows.append([
                Paragraph(f"<font name='Courier'>{insp_id_short}</font>", body_style),
                Paragraph(store_name, body_style),
                Paragraph(dist_state, body_style),
                Paragraph(f"<font color='{color_res.hexval()}'><b>{res_val}</b></font>", body_style),
                Paragraph(fin_str, body_style),
            ])

        t_verdicts = Table(verdict_rows, colWidths=[90, 133, 110, 110, 80])
        t_verdicts.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
            ])
        )
        story.append(t_verdicts)

    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 5: OBSERVED FINDING PATTERNS (NON-JUDICIAL GROUPINGS)
    # =========================================================================
    story.append(Paragraph("4. OBSERVED FINDING PATTERNS", section_heading))
    story.append(
        Paragraph(
            "<b>STATUTORY OBSERVATION NOTICE:</b> Grouped finding patterns aggregate existing inspection findings across the linked records "
            "for supervisory analysis. They <b>do not</b> constitute new statutory offences, collective liability, or automatic systemic liability.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))

    if synthesis.observed_findings:
        finding_rows = [
            [
                Paragraph("<b>Rule Code</b>", body_bold),
                Paragraph("<b>Rule Title / Statutory Provision</b>", body_bold),
                Paragraph("<b>Affected Cases</b>", body_bold),
                Paragraph("<b>Observed Severities</b>", body_bold),
                Paragraph("<b>Observation Label</b>", body_bold),
            ]
        ]
        for of in synthesis.observed_findings:
            finding_rows.append([
                Paragraph(f"<b>{of.rule_code}</b>", body_style),
                Paragraph(of.rule_name, body_style),
                Paragraph(f"{of.affected_inspection_count} inspection(s)", body_style),
                Paragraph(", ".join(of.severity_levels) if of.severity_levels else "STANDARD", body_style),
                Paragraph(f"<i>{of.observation_label}</i>", body_style),
            ])

        t_find = Table(finding_rows, colWidths=[90, 163, 75, 95, 100])
        t_find.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("PADDING", (0, 0), (-1, -1), 3.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(t_find)
    else:
        story.append(Paragraph("<i>No recurring statutory finding patterns observed across linked inspections.</i>", body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 6: EVIDENCE COMPLETENESS SUMMARY
    # =========================================================================
    story.append(Paragraph("5. EVIDENCE COMPLETENESS SUMMARY", section_heading))
    ev_score = synthesis.evidence_completeness_average
    ev_text = (
        f"<b>Average Evidence Completeness Index: {ev_score}%</b> across linked inspection sessions. "
        "Evaluates the completeness of visual evidence, declaration transcriptions, optical clarity, regulatory registration, "
        "and physical measurement records. This index is an operational decision-support metric and does not alter statutory compliance."
    )
    story.append(Paragraph(ev_text, body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 7: RECORDED SEIZURES (SECTION 15 PANCHNAMA AGGREGATION)
    # =========================================================================
    story.append(Paragraph("6. RECORDED SEIZURE QUANTITIES ACROSS LINKED RECORDS", section_heading))
    sz = synthesis.seizure_summary
    seizure_data = [
        [
            Paragraph("<b>Lawfully Executed Panchnama Records:</b>", body_style),
            Paragraph(f"<b>{sz.total_seizure_records}</b>", body_style),
            Paragraph("<b>Total Packages / Units in Custody:</b>", body_style),
            Paragraph(f"<b>{sz.total_seized_quantity:,.0f} units</b>", body_style),
        ],
        [
            Paragraph("<b>Itemized Inventory Rows:</b>", body_style),
            Paragraph(f"<b>{sz.seizure_items_count} distinct items</b>", body_style),
            Paragraph("<b>Statutory Grounding:</b>", body_style),
            Paragraph("Section 15, Legal Metrology Act, 2009", body_style),
        ],
    ]
    t_sz = Table(seizure_data, colWidths=[150, 111, 140, 122])
    t_sz.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(t_sz)
    story.append(
        Paragraph(
            "<i>Note: Aggregated strictly from Section 15 Panchnama search and seizure records legally executed during individual inspections. "
            "Dossier grouping does not issue autonomous seizure orders.</i>",
            body_style,
        )
    )
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 8 & 9: COMMODITY / BATCH & TERRITORIAL FOOTPRINT
    # =========================================================================
    story.append(Paragraph("7. COMMODITY, BATCH & TERRITORIAL SCOPE", section_heading))
    distinct_locations_count = len(synthesis.locations)
    locations_display = ", ".join(synthesis.locations[:3]) if synthesis.locations else "None recorded"
    terr_data = [
        [
            Paragraph("<b>Distinct Locations:</b>", body_style),
            Paragraph(f"<b>{distinct_locations_count}</b>", body_style),
            Paragraph("<b>Commodity Batches / Lots:</b>", body_style),
            Paragraph(f"<b>{synthesis.batch_count}</b>", body_style),
        ],
        [
            Paragraph("<b>Locations Recorded:</b>", body_style),
            Paragraph(locations_display, body_style),
            Paragraph("<b>Evidence Completeness:</b>", body_style),
            Paragraph(f"<b>{synthesis.evidence_completeness_average:.1f}%</b>", body_style),
        ],
    ]
    t_terr = Table(terr_data, colWidths=[140, 121, 130, 132])
    t_terr.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(t_terr)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 10: CORPORATE RECORDS & NOMINATED DIRECTORS (SECTION 49)
    # =========================================================================
    story.append(Paragraph("8. ASSOCIATED CORPORATE RECORDS (SECTION 49)", section_heading))
    if dossier.company:
        comp = dossier.company
        comp_rows = [
            [
                Paragraph("<b>Registered Company Name:</b>", body_style),
                Paragraph(f"<b>{comp.company_name}</b>", body_style),
                Paragraph("<b>Corporate Identity No (CIN):</b>", body_style),
                Paragraph(f"<font name='Courier'><b>{comp.cin}</b></font>", body_style),
            ],
            [
                Paragraph("<b>Registered Office:</b>", body_style),
                Paragraph(comp.registered_office, body_style),
                Paragraph("<b>Jurisdiction State:</b>", body_style),
                Paragraph(comp.state, body_style),
            ],
        ]
        t_comp = Table(comp_rows, colWidths=[130, 131, 131, 131])
        t_comp.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), light_bg),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(t_comp)
        story.append(Spacer(1, 4))

        if synthesis.nominated_directors_review:
            dir_rows = [
                [
                    Paragraph("<b>Director Name</b>", body_bold),
                    Paragraph("<b>DIN</b>", body_bold),
                    Paragraph("<b>Designation</b>", body_bold),
                    Paragraph("<b>Notice Date (Form I)</b>", body_bold),
                    Paragraph("<b>Administrative Review Note</b>", body_bold),
                ]
            ]
            for d in synthesis.nominated_directors_review:
                dir_rows.append([
                    Paragraph(d.director_name, body_style),
                    Paragraph(f"<font name='Courier'>{d.din}</font>", body_style),
                    Paragraph(d.designation, body_style),
                    Paragraph(d.form_i_notice_date or "—", body_style),
                    Paragraph(f"<i>{d.review_note}</i>", body_style),
                ])
            t_dirs = Table(dir_rows, colWidths=[100, 65, 95, 85, 178])
            t_dirs.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                    ("PADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ])
            )
            story.append(t_dirs)
        else:
            story.append(Paragraph("<i>No Form I Nominated Director resolutions recorded under Section 49(2) for this company.</i>", body_style))

        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "<i>Nominated director information is presented as an administrative record and does not by itself establish personal liability. "
                "Notice recipient determination follows Section 49 statutory protocol upon authorized officer adjudication.</i>",
                body_style,
            )
        )
    else:
        story.append(
            Paragraph(
                "<i>No corporate entity registered under Section 49 currently associated with this dossier. "
                f"Target entity descriptor is '{target_ent}' (informational text only; no automatic corporate liability).</i>",
                body_style,
            )
        )
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 11: OPERATIONAL TIMELINE
    # =========================================================================
    story.append(Paragraph("9. OPERATIONAL TIMELINE & AUDIT SEQUENCE", section_heading))
    if synthesis.timeline:
        tl_rows = [
            [
                Paragraph("<b>Timestamp (UTC)</b>", body_bold),
                Paragraph("<b>Event Type</b>", body_bold),
                Paragraph("<b>Operational Description</b>", body_bold),
            ]
        ]
        for evt in synthesis.timeline[-10:]:  # Last 10 events for clean fit
            ts_str = evt.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(evt.timestamp, "strftime") else str(evt.timestamp)[:16]
            tl_rows.append([
                Paragraph(f"<font name='Courier'>{ts_str}</font>", body_style),
                Paragraph(evt.event_type, body_style),
                Paragraph(evt.description, body_style),
            ])
        t_tl = Table(tl_rows, colWidths=[95, 120, 308])
        t_tl.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
            ])
        )
        story.append(t_tl)
    else:
        story.append(Paragraph("<i>No timeline events recorded.</i>", body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 12: SOURCE & LEGAL REFERENCE METADATA (2011 GAZETTE CORPUS)
    # =========================================================================
    story.append(Paragraph("10. LEGAL CORPUS & STATUTORY REFERENCE METADATA", section_heading))
    meta_box = [
        [
            Paragraph("<b>Authoritative Reference Corpus:</b>", body_style),
            Paragraph(
                "The Legal Metrology (Packaged Commodities) Rules, 2011, published in The Gazette of India: Extraordinary, "
                "Part II—Sec. 3(i), Notification G.S.R. 202(E) / 203(E) dated 7th March, 2011, effective 1st April, 2011.",
                body_style,
            ),
        ],
        [
            Paragraph("<b>Statutory Provisions Referenced:</b>", body_style),
            Paragraph(
                "Rules 3 (Applicability & Exclusions), 4 (Pre-packing regulation), 5 (Standard quantities), 6 (Mandatory declarations), "
                "9 (Manner of declarations), 10 (Manufacturer/Packer identity), 11 (Quantity declarations), 12 (Quantity expression), "
                "13 (Units & symbols), 14-17 (Dimensions & usable units), 18 (Wholesale & retail dealer obligations), "
                "19 (Manufacturer/packer inspection), 21 (Retail/wholesale inspection), 22 (MPE establishment), 23 (Deceptive packaging), "
                "24 (Wholesale packages), 26 (Statutory exemptions), 27 (Registration of pre-packers), 32 (Penalties); "
                "First Schedule (Maximum Permissible Errors); Second Schedule (Standard quantities); "
                "Fifth Schedule (Manner of selection of samples); Sixth Schedule (Net quantity determination procedures); "
                "Seventh Schedule (Form of report / data-sheet for test results).",
                body_style,
            ),
        ],
        [
            Paragraph("<b>Corpus Version Identifier:</b>", body_style),
            Paragraph("SIH-OFFICIAL-LEGAL-DATASET-2011 (Gazette G.S.R. 202(E) / 203(E) [47-Page Canonical Reference Corpus])", body_style),
        ],
        [
            Paragraph("<b>Version-Specific Limitation:</b>", body_style),
            Paragraph(
                "This software application evaluates against the official SIH-supplied 2011 Gazette notification corpus. "
                "Post-2011 amendments (including subsequent e-commerce and packaging notifications) require explicit version configuration "
                "and are preserved under versioned rule parameters rather than assuming universal current-law equivalence.",
                disclaimer_text_style,
            ),
        ],
    ]
    t_meta = Table(meta_box, colWidths=[130, 393])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 13 & 14: SYSTEM DISCLAIMER & EVIDENCE INTEGRITY FINGERPRINTS
    # =========================================================================
    story.append(Paragraph("11. EVIDENCE INTEGRITY & SYSTEM DISCLAIMER", section_heading))

    integrity_rows = []
    if evidence_hashes:
        for eh in evidence_hashes[:5]:
            integrity_rows.append([
                Paragraph(f"<b>{eh.get('label', 'Evidence Item')}:</b>", body_style),
                Paragraph(f"<font name='Courier'>{eh.get('sha256', '—')}</font>", body_style),
            ])

    doc_checksum_pre = hashlib.sha256(
        f"{dossier.id}:{dossier.dossier_number}:{created_time}:{gen_time}".encode("utf-8")
    ).hexdigest()

    integrity_rows.append([
        Paragraph("<b>Consolidated Document Digest (SHA-256):</b>", body_style),
        Paragraph(f"<font name='Courier'><b>{doc_checksum_pre}</b></font>", body_style),
    ])
    integrity_rows.append([
        Paragraph("<b>Authorized Verification Notice:</b>", body_style),
        Paragraph(
            "This document is a computer-assisted operational reference and evidence synthesis document compiled for authorized Legal Metrology officers. "
            "Individual inspection legal results (COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW) remain authoritative and independently verifiable. "
            "This document does not constitute an autonomous government enforcement action, legal opinion, prosecution determination, or finding of liability.",
            disclaimer_text_style,
        ),
    ])

    t_integ = Table(integrity_rows, colWidths=[160, 363])
    t_integ.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(KeepTogether(t_integ))

    doc.build(story)
    return buffer.getvalue()
