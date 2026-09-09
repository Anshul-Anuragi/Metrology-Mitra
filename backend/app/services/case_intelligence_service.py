import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import CheckResult, ComplianceResult, ImageType, InspectionStatus, ViolationSeverity
from app.models.company import Company, NominatedDirector
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.gravimetric_test import GravimetricTest
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.packer_registration import PackerRegistration
from app.models.product import Product
from app.models.user import User
from app.models.violation import Violation
from app.schemas.case_intelligence import (
    ActionRecommendation,
    ActionRecommendationCategory,
    CaseIntelligenceResponse,
    CasePriority,
    EvidenceCompleteness,
    EvidenceFacet,
    EvidenceFacetStatus,
    EvidenceGap,
    PriorityFactor,
    PriorityLevel,
    SupervisorTriageItem,
    SupervisorTriageResponse,
)

# Application-level workflow weights for Evidence Completeness calculation.
# NOTE: These are operational workflow heuristics and NOT statutory legal requirements.
FACET_WEIGHTS = {
    "FACET_VISUAL_PACKAGING": 20.0,
    "FACET_MANDATORY_DECLARATIONS": 25.0,
    "FACET_PERCEPTION_QUALITY": 15.0,
    "FACET_REGULATORY_REGISTRY": 15.0,
    "FACET_PHYSICAL_MEASUREMENT": 15.0,
    "FACET_CORPORATE_GOVERNANCE": 10.0,
}


def compute_evidence_completeness(
    inspection: Inspection,
    declaration: Optional[Declaration],
    images: List[InspectionImage],
    ocr_results: List[OCRResult],
    checks: List[ComplianceCheck],
    gravimetric_test: Optional[GravimetricTest] = None,
    company: Optional[Company] = None,
) -> EvidenceCompleteness:
    """
    Computes a deterministic Evidence Completeness Index (0-100) across six standard facets.
    Measures the sufficiency of collected inspection data for decision-support.
    Does NOT determine or alter statutory legal compliance.
    """
    facets: List[EvidenceFacet] = []
    gaps: List[EvidenceGap] = []

    # =========================================================================
    # Facet 1 — Visual Packaging Evidence (Weight: 20)
    # =========================================================================
    facet1_weight = FACET_WEIGHTS["FACET_VISUAL_PACKAGING"]
    facet1_present: List[str] = []
    facet1_missing: List[str] = []
    facet1_gap: Optional[str] = None
    facet1_score: float = 0.0

    if not images:
        facet1_status = EvidenceFacetStatus.MISSING
        facet1_missing.append("No package photographs uploaded")
        facet1_gap = "Upload primary photograph of package Principal Display Panel (PDP)."
        gaps.append(
            EvidenceGap(
                code="MISSING_PACKAGE_IMAGES",
                title="No package photographs attached",
                description="The inspection session has no attached packaging images for visual verification.",
                severity=ViolationSeverity.HIGH,
                action="Capture and attach at least one clear photograph of the package Principal Display Panel.",
                facet_code="FACET_VISUAL_PACKAGING",
                is_blocking=True,
            )
        )
    else:
        has_front_or_label = any(
            img.image_type in [ImageType.FRONT, ImageType.LABEL] for img in images
        )
        has_multi_angle = len(images) >= 2 or any(
            img.image_type in [ImageType.BACK, ImageType.SIDE, ImageType.TOP, ImageType.BOTTOM] for img in images
        )
        has_severe_quality_issue = any(
            img.quality_gate_result and img.quality_gate_result.get("decision") == "RETAKE_RECOMMENDED"
            for img in images
        )

        if has_front_or_label:
            facet1_present.append(f"{len(images)} package image(s) attached")
        if has_multi_angle:
            facet1_present.append("Multi-angle package views available")

        if has_severe_quality_issue:
            facet1_status = EvidenceFacetStatus.PARTIAL
            facet1_score = 50.0
            facet1_missing.append("One or more images flagged for retake due to blur or glare")
            facet1_gap = "Retake degraded photograph under balanced diffuse illumination."
            gaps.append(
                EvidenceGap(
                    code="IMAGE_QUALITY_DEGRADED",
                    title="Package photograph quality degraded",
                    description="Optical diagnostics detected excessive blur or specular glare on one or more attached images.",
                    severity=ViolationSeverity.MEDIUM,
                    action="Retake the affected package panel under balanced diffuse lighting to ensure readability.",
                    facet_code="FACET_VISUAL_PACKAGING",
                    is_blocking=False,
                )
            )
        elif has_front_or_label and has_multi_angle:
            facet1_status = EvidenceFacetStatus.COMPLETE
            facet1_score = 100.0
        elif has_front_or_label:
            facet1_status = EvidenceFacetStatus.PARTIAL
            facet1_score = 75.0
            facet1_missing.append("Secondary angle (rear/side label) not provided")
            facet1_gap = "Attach secondary photograph of rear/side declaration panel if declarations are split."
        else:
            facet1_status = EvidenceFacetStatus.PARTIAL
            facet1_score = 40.0
            facet1_missing.append("Principal Display Panel (PDP) front angle missing")
            facet1_gap = "Attach a direct front view of the Principal Display Panel."
            gaps.append(
                EvidenceGap(
                    code="MISSING_PDP_IMAGE",
                    title="Front Principal Display Panel view missing",
                    description="The session lacks a direct front image of the Principal Display Panel.",
                    severity=ViolationSeverity.MEDIUM,
                    action="Capture and upload a clear photograph of the primary front packaging panel.",
                    facet_code="FACET_VISUAL_PACKAGING",
                    is_blocking=False,
                )
            )

    facets.append(
        EvidenceFacet(
            name="Visual Packaging Evidence",
            facet_code="FACET_VISUAL_PACKAGING",
            status=facet1_status,
            score=facet1_score,
            weight=facet1_weight,
            is_required=True,
            is_applicable=True,
            evidence_present=facet1_present,
            evidence_missing=facet1_missing,
            actionable_gap=facet1_gap,
        )
    )

    # =========================================================================
    # Facet 2 — Mandatory Declaration Evidence (Weight: 25)
    # =========================================================================
    facet2_weight = FACET_WEIGHTS["FACET_MANDATORY_DECLARATIONS"]
    facet2_present: List[str] = []
    facet2_missing: List[str] = []
    facet2_gap: Optional[str] = None
    facet2_score: float = 0.0

    core_decl_fields = [
        ("commodity_name", "Commodity Name"),
        ("manufacturer_name", "Manufacturer/Packer Name"),
        ("address", "Physical Address"),
        ("net_quantity", "Net Quantity"),
        ("mrp", "Maximum Retail Price (MRP)"),
        ("manufacturing_date", "Date of Mfg/Packing"),
        ("consumer_care", "Consumer Care Contacts"),
    ]

    if not declaration:
        facet2_status = EvidenceFacetStatus.MISSING
        facet2_missing.append("No statutory declarations recorded or extracted")
        facet2_gap = "Execute OCR pipeline or record declaration values manually."
        gaps.append(
            EvidenceGap(
                code="MISSING_DECLARATIONS_DATA",
                title="Statutory declarations missing",
                description="No extracted or human-verified declaration data is present for this commodity.",
                severity=ViolationSeverity.HIGH,
                action="Run automated OCR extraction or populate declaration fields manually in the workspace.",
                facet_code="FACET_MANDATORY_DECLARATIONS",
                is_blocking=True,
            )
        )
    else:
        present_count = 0
        for attr, label in core_decl_fields:
            val = getattr(declaration, attr, None)
            if attr == "manufacturer_name" and not val:
                val = getattr(declaration, "packer_name", None) or getattr(declaration, "importer_name", None)
            if attr == "manufacturing_date" and not val:
                val = getattr(declaration, "packing_date", None) or getattr(declaration, "import_date", None)
            if attr == "consumer_care" and not val:
                val = getattr(declaration, "consumer_care_phone", None) or getattr(declaration, "consumer_care_email", None)

            if val and str(val).strip():
                present_count += 1
                facet2_present.append(f"{label}: '{str(val).strip()}'")
            else:
                facet2_missing.append(label)

        ratio = present_count / len(core_decl_fields)
        facet2_score = round(ratio * 100.0, 1)

        if ratio >= 0.85:
            facet2_status = EvidenceFacetStatus.COMPLETE
        elif ratio >= 0.40:
            facet2_status = EvidenceFacetStatus.PARTIAL
            missing_labels = ", ".join(facet2_missing[:3])
            facet2_gap = f"Complete missing declaration fields: {missing_labels}."
            gaps.append(
                EvidenceGap(
                    code="PARTIAL_DECLARATIONS",
                    title="Key statutory declarations missing",
                    description=f"The package record is missing core declarations: {missing_labels}.",
                    severity=ViolationSeverity.MEDIUM,
                    action="Verify package label and record missing statutory declaration values.",
                    facet_code="FACET_MANDATORY_DECLARATIONS",
                    is_blocking=False,
                )
            )
        else:
            facet2_status = EvidenceFacetStatus.MISSING
            facet2_gap = "Major core declarations missing. Extract or verify package label fields."
            gaps.append(
                EvidenceGap(
                    code="INCOMPLETE_CORE_DECLARATIONS",
                    title="Major core declarations missing",
                    description="Fewer than 40% of standard mandatory declarations are present on the record.",
                    severity=ViolationSeverity.HIGH,
                    action="Perform comprehensive ocular inspection and transcribe missing mandatory declarations.",
                    facet_code="FACET_MANDATORY_DECLARATIONS",
                    is_blocking=True,
                )
            )

    facets.append(
        EvidenceFacet(
            name="Mandatory Declaration Evidence",
            facet_code="FACET_MANDATORY_DECLARATIONS",
            status=facet2_status,
            score=facet2_score,
            weight=facet2_weight,
            is_required=True,
            is_applicable=True,
            evidence_present=facet2_present,
            evidence_missing=facet2_missing,
            actionable_gap=facet2_gap,
        )
    )

    # =========================================================================
    # Facet 3 — Perception Quality (Weight: 15)
    # =========================================================================
    facet3_weight = FACET_WEIGHTS["FACET_PERCEPTION_QUALITY"]
    facet3_present: List[str] = []
    facet3_missing: List[str] = []
    facet3_gap: Optional[str] = None
    facet3_score: float = 0.0

    if not ocr_results and not (declaration and declaration.is_human_verified):
        facet3_status = EvidenceFacetStatus.MISSING
        facet3_missing.append("No OCR perception results or human verification")
        facet3_gap = "Run OCR text extraction or confirm declarations with human verification."
        gaps.append(
            EvidenceGap(
                code="NO_PERCEPTION_DATA",
                title="Optical perception not executed",
                description="OCR extraction has not been performed on attached packaging imagery.",
                severity=ViolationSeverity.MEDIUM,
                action="Execute OCR pipeline to extract text tokens and spatial coordinates.",
                facet_code="FACET_PERCEPTION_QUALITY",
                is_blocking=False,
            )
        )
    else:
        avg_confidence = 0.0
        if ocr_results:
            conf_list = [r.confidence for r in ocr_results if r.confidence is not None]
            if conf_list:
                avg_confidence = sum(conf_list) / len(conf_list)
                facet3_present.append(f"OCR Average Confidence: {round(avg_confidence * 100, 1)}%")

        if declaration and declaration.is_human_verified:
            facet3_present.append("Human inspector verified declarations")
            facet3_status = EvidenceFacetStatus.COMPLETE
            facet3_score = 100.0
        elif avg_confidence >= 0.80:
            facet3_status = EvidenceFacetStatus.COMPLETE
            facet3_score = round(avg_confidence * 100, 1)
        elif avg_confidence >= 0.50:
            facet3_status = EvidenceFacetStatus.PARTIAL
            facet3_score = round(avg_confidence * 100, 1)
            facet3_missing.append("OCR confidence below 80% threshold")
            facet3_gap = "Review extracted tokens against package image to confirm transcription accuracy."
            gaps.append(
                EvidenceGap(
                    code="LOW_OCR_CONFIDENCE",
                    title="OCR text extraction confidence is low",
                    description=f"Average OCR confidence is {round(avg_confidence * 100, 1)}%. Text tokens may contain recognition errors.",
                    severity=ViolationSeverity.LOW,
                    action="Review extracted declaration fields and apply manual corrections where necessary.",
                    facet_code="FACET_PERCEPTION_QUALITY",
                    is_blocking=False,
                )
            )
        else:
            facet3_status = EvidenceFacetStatus.MISSING
            facet3_score = round(avg_confidence * 100, 1)
            facet3_missing.append("OCR confidence severely degraded (< 50%)")
            facet3_gap = "Recapture label image under clearer lighting or enter declarations manually."
            gaps.append(
                EvidenceGap(
                    code="SEVERELY_DEGRADED_OCR",
                    title="Optical text recognition severely degraded",
                    description="OCR text extraction yielded low confidence. Image may be out of focus or glare-obscured.",
                    severity=ViolationSeverity.MEDIUM,
                    action="Recapture the label panel or verify declarations manually in the workspace.",
                    facet_code="FACET_PERCEPTION_QUALITY",
                    is_blocking=False,
                )
            )

    facets.append(
        EvidenceFacet(
            name="Perception Quality",
            facet_code="FACET_PERCEPTION_QUALITY",
            status=facet3_status,
            score=facet3_score,
            weight=facet3_weight,
            is_required=True,
            is_applicable=True,
            evidence_present=facet3_present,
            evidence_missing=facet3_missing,
            actionable_gap=facet3_gap,
        )
    )

    # =========================================================================
    # Facet 4 — Regulatory Registry Evidence (Weight: 15)
    # =========================================================================
    facet4_weight = FACET_WEIGHTS["FACET_REGULATORY_REGISTRY"]
    facet4_present: List[str] = []
    facet4_missing: List[str] = []
    facet4_gap: Optional[str] = None
    facet4_score: float = 0.0

    reg_checks = [c for c in checks if c.legal_rule and "RULE-27" in c.legal_rule.rule_code]
    if not reg_checks:
        # If Rule 27 check is not in active rule set for this inspection, check if manufacturer name exists
        has_mfg = declaration and (declaration.manufacturer_name or declaration.packer_name or declaration.importer_name)
        if has_mfg:
            facet4_status = EvidenceFacetStatus.PARTIAL
            facet4_score = 50.0
            facet4_present.append("Manufacturer identity recorded")
            facet4_missing.append("Rule 27 pre-packer registration verification not evaluated")
            facet4_gap = "Verify manufacturer in Rule 27 statutory registry if registration number is declared."
        else:
            facet4_status = EvidenceFacetStatus.NOT_APPLICABLE
            facet4_score = 100.0
            facet4_present.append("No pre-packer registration requirement triggered")
    else:
        reg_check = reg_checks[0]
        if reg_check.result == CheckResult.PASS:
            facet4_status = EvidenceFacetStatus.COMPLETE
            facet4_score = 100.0
            facet4_present.append("Rule 27 Pre-Packer Registry Verified (Valid)")
        elif reg_check.result == CheckResult.REVIEW:
            facet4_status = EvidenceFacetStatus.PARTIAL
            facet4_score = 50.0
            facet4_missing.append("Pre-packer registration unverified in local registry")
            facet4_gap = "Verify the packer registration using the available regulatory registry record."
            gaps.append(
                EvidenceGap(
                    code="UNVERIFIED_PACKER_REGISTRY",
                    title="Pre-packer registration unverified",
                    description="The declared manufacturer/packer registration number is not indexed in the local Rule 27 registry.",
                    severity=ViolationSeverity.LOW,
                    action="Search the Rule 27 pre-packer registry or request registration certificate from the packer.",
                    facet_code="FACET_REGULATORY_REGISTRY",
                    is_blocking=False,
                )
            )
        else:
            facet4_status = EvidenceFacetStatus.PARTIAL
            facet4_score = 25.0
            facet4_missing.append("Rule 27 pre-packer registration non-compliance flagged")
            facet4_gap = "Review registration validity dates or jurisdiction authority."

    facets.append(
        EvidenceFacet(
            name="Regulatory Registry Evidence",
            facet_code="FACET_REGULATORY_REGISTRY",
            status=facet4_status,
            score=facet4_score,
            weight=facet4_weight,
            is_required=False,
            is_applicable=(facet4_status != EvidenceFacetStatus.NOT_APPLICABLE),
            evidence_present=facet4_present,
            evidence_missing=facet4_missing,
            actionable_gap=facet4_gap,
        )
    )

    # =========================================================================
    # Facet 5 — Physical Measurement Evidence (Weight: 15)
    # =========================================================================
    facet5_weight = FACET_WEIGHTS["FACET_PHYSICAL_MEASUREMENT"]
    facet5_present: List[str] = []
    facet5_missing: List[str] = []
    facet5_gap: Optional[str] = None
    facet5_score: float = 0.0

    # Physical gravimetric measurement is required if a gravimetric test was explicitly initiated or batch inspection
    is_batch_lot = inspection.batch_id is not None
    has_gravimetric = gravimetric_test is not None

    if has_gravimetric:
        has_readings = bool(gravimetric_test.sample_units_data)
        if has_readings:
            unit_count = len(gravimetric_test.sample_units_data) if isinstance(gravimetric_test.sample_units_data, list) else 0
            facet5_status = EvidenceFacetStatus.COMPLETE
            facet5_score = 100.0
            facet5_present.append(f"Gravimetric test logged ({unit_count} sample units evaluated)")
        else:
            facet5_status = EvidenceFacetStatus.PARTIAL
            facet5_score = 30.0
            facet5_missing.append("Physical gross/tare scale readings not logged")
            facet5_gap = "Record gross and tare weight sample readings on calibrated scale."
            gaps.append(
                EvidenceGap(
                    code="INCOMPLETE_GRAVIMETRIC_LOG",
                    title="Gravimetric sample readings incomplete",
                    description="A gravimetric test record exists for this inspection, but individual sample weights are missing.",
                    severity=ViolationSeverity.MEDIUM,
                    action="Log individual sample gross/tare weights to complete the Rule 24 net quantity assessment.",
                    facet_code="FACET_PHYSICAL_MEASUREMENT",
                    is_blocking=False,
                )
            )
    elif is_batch_lot:
        facet5_status = EvidenceFacetStatus.PARTIAL
        facet5_score = 40.0
        facet5_missing.append("Physical scale sampling not conducted for batch lot")
        facet5_gap = "Conduct physical gravimetric scale testing under Fifth Schedule sampling criteria."
        gaps.append(
            EvidenceGap(
                code="BATCH_SAMPLING_NOT_CONDUCTED",
                title="Batch lot physical sampling missing",
                description="This inspection belongs to a batch/lot, but physical scale sampling has not been recorded.",
                severity=ViolationSeverity.LOW,
                action="Draw required sample size (32 or 80 units) and perform gravimetric net content testing.",
                facet_code="FACET_PHYSICAL_MEASUREMENT",
                is_blocking=False,
            )
        )
    else:
        # For standard retail package visual label inspections, physical scale weighing is optional/not required
        facet5_status = EvidenceFacetStatus.NOT_APPLICABLE
        facet5_score = 100.0
        facet5_present.append("Standard visual declaration inspection; physical scale test optional")

    facets.append(
        EvidenceFacet(
            name="Physical Measurement Evidence",
            facet_code="FACET_PHYSICAL_MEASUREMENT",
            status=facet5_status,
            score=facet5_score,
            weight=facet5_weight,
            is_required=(has_gravimetric or is_batch_lot),
            is_applicable=(facet5_status != EvidenceFacetStatus.NOT_APPLICABLE),
            evidence_present=facet5_present,
            evidence_missing=facet5_missing,
            actionable_gap=facet5_gap,
        )
    )

    # =========================================================================
    # Facet 6 — Corporate Governance Evidence (Weight: 10)
    # =========================================================================
    facet6_weight = FACET_WEIGHTS["FACET_CORPORATE_GOVERNANCE"]
    facet6_present: List[str] = []
    facet6_missing: List[str] = []
    facet6_gap: Optional[str] = None
    facet6_score: float = 0.0

    is_corporate_entity = (inspection.company_id is not None) or (company is not None)

    if is_corporate_entity and company:
        has_cin = bool(company.cin)
        has_directors = bool(company.nominated_directors)
        if has_cin and has_directors:
            facet6_status = EvidenceFacetStatus.COMPLETE
            facet6_score = 100.0
            facet6_present.append(f"Company CIN: {company.cin}")
            facet6_present.append(f"{len(company.nominated_directors)} Section 49(2) Nominated Director(s) registered")
        elif has_cin:
            facet6_status = EvidenceFacetStatus.PARTIAL
            facet6_score = 60.0
            facet6_present.append(f"Company CIN: {company.cin}")
            facet6_missing.append("No Section 49(2) Form I nominated director registered")
            facet6_gap = "Verify whether Form I director nomination was given to Controller."
            gaps.append(
                EvidenceGap(
                    code="NO_NOMINATED_DIRECTOR",
                    title="No nominated director on record",
                    description=f"Corporate entity '{company.company_name}' has no Form I nominated director under Section 49(2).",
                    severity=ViolationSeverity.LOW,
                    action="Check if the corporate entity has submitted a Form I director nomination to the Legal Metrology Controller.",
                    facet_code="FACET_CORPORATE_GOVERNANCE",
                    is_blocking=False,
                )
            )
        else:
            facet6_status = EvidenceFacetStatus.MISSING
            facet6_score = 20.0
            facet6_missing.append("Corporate registration details incomplete")
            facet6_gap = "Record Corporate Identification Number (CIN) and registered office."
    elif is_corporate_entity:
        facet6_status = EvidenceFacetStatus.PARTIAL
        facet6_score = 40.0
        facet6_missing.append("Company record linked but details not loaded")
        facet6_gap = "Verify corporate record linkage in Section 49 module."
    else:
        # Non-corporate sole proprietorship or unclassified entity
        facet6_status = EvidenceFacetStatus.NOT_APPLICABLE
        facet6_score = 100.0
        facet6_present.append("Inspected entity is not a corporate packer; Section 49 not applicable")

    facets.append(
        EvidenceFacet(
            name="Corporate Governance Evidence",
            facet_code="FACET_CORPORATE_GOVERNANCE",
            status=facet6_status,
            score=facet6_score,
            weight=facet6_weight,
            is_required=is_corporate_entity,
            is_applicable=(facet6_status != EvidenceFacetStatus.NOT_APPLICABLE),
            evidence_present=facet6_present,
            evidence_missing=facet6_missing,
            actionable_gap=facet6_gap,
        )
    )

    # =========================================================================
    # Composite Completeness Index Calculation
    # =========================================================================
    applicable_facets = [f for f in facets if f.is_applicable]
    if not applicable_facets:
        total_score = 0.0
    else:
        total_weight = sum(f.weight for f in applicable_facets)
        weighted_score_sum = sum(f.score * (f.weight / total_weight) for f in applicable_facets)
        total_score = round(weighted_score_sum, 1)

    if total_score >= 85.0:
        overall_status = "EXCELLENT"
    elif total_score >= 65.0:
        overall_status = "ADEQUATE"
    elif total_score >= 40.0:
        overall_status = "PARTIAL"
    elif total_score > 0.0:
        overall_status = "INCOMPLETE"
    else:
        overall_status = "EMPTY"

    return EvidenceCompleteness(
        score=total_score,
        status=overall_status,
        facets=facets,
        gaps=gaps,
    )


def compute_case_priority(
    inspection: Inspection,
    declaration: Optional[Declaration],
    checks: List[ComplianceCheck],
    violations: List[Violation],
    completeness: EvidenceCompleteness,
    repeat_offence_count: int = 0,
    inspection_age_days: int = 0,
) -> CasePriority:
    """
    Computes deterministic operational case priority indicator (0-100) and priority level.
    NOTE: Operational prioritization weights. Not statutory thresholds and not legal conclusions.
    Never alters or overwrites the underlying statutory legal compliance result.
    """
    factors: List[PriorityFactor] = []
    base_points = 0.0

    # 1. Statutory Violation Severity & Count
    critical_viols = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
    high_viols = [v for v in violations if v.severity == ViolationSeverity.HIGH]
    medium_viols = [v for v in violations if v.severity == ViolationSeverity.MEDIUM]
    low_viols = [v for v in violations if v.severity == ViolationSeverity.LOW]

    if critical_viols:
        pts = min(35.0, len(critical_viols) * 20.0)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="CRITICAL_VIOLATIONS",
                description=f"{len(critical_viols)} CRITICAL severity statutory violation(s) detected.",
                points_contributed=pts,
                severity="CRITICAL",
            )
        )
    elif high_viols:
        pts = min(25.0, len(high_viols) * 12.5)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="HIGH_VIOLATIONS",
                description=f"{len(high_viols)} HIGH severity statutory violation(s) detected.",
                points_contributed=pts,
                severity="HIGH",
            )
        )
    elif medium_viols or low_viols:
        tot = len(medium_viols) + len(low_viols)
        pts = min(15.0, tot * 5.0)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="STANDARD_VIOLATIONS",
                description=f"{tot} standard statutory violation(s) detected.",
                points_contributed=pts,
                severity="MEDIUM",
            )
        )

    # 2. Unresolved NEEDS_REVIEW Checks
    unresolved_reviews = [c for c in checks if c.result == CheckResult.REVIEW]
    if unresolved_reviews and (not declaration or not declaration.is_human_verified):
        pts = min(20.0, len(unresolved_reviews) * 5.0)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="UNRESOLVED_REVIEWS",
                description=f"{len(unresolved_reviews)} compliance check(s) require human review/adjudication.",
                points_contributed=pts,
                severity="MEDIUM",
            )
        )

    # 3. Repeat Historical Non-Compliance (Offence history)
    if repeat_offence_count > 0:
        pts = min(25.0, repeat_offence_count * 10.0)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="REPEAT_OFFENDER_HISTORY",
                description=f"Manufacturer/entity has {repeat_offence_count} prior non-compliant inspection(s) on record.",
                points_contributed=pts,
                severity="HIGH",
            )
        )

    # 4. Evidence Incompleteness Concern
    if completeness.score < 50.0 and inspection.status != InspectionStatus.COMPLETED:
        pts = 10.0
        base_points += pts
        factors.append(
            PriorityFactor(
                code="EVIDENCE_INCOMPLETE",
                description=f"Evidence Completeness Index is {completeness.score}% (below 50% threshold).",
                points_contributed=pts,
                severity="LOW",
            )
        )

    # 5. Inspection Age / Review Urgency
    if inspection.status == InspectionStatus.REVIEW_REQUIRED and inspection_age_days >= 3:
        pts = min(15.0, inspection_age_days * 3.0)
        base_points += pts
        factors.append(
            PriorityFactor(
                code="AGING_REVIEW_QUEUE",
                description=f"Inspection has been pending review for {inspection_age_days} day(s).",
                points_contributed=pts,
                severity="MEDIUM",
            )
        )

    # Final clamped priority score
    final_score = min(100.0, max(0.0, round(base_points, 1)))

    if final_score >= 70.0:
        level = PriorityLevel.CRITICAL
        summary = "Critical operational priority: Severe statutory violations or high-frequency repeat non-compliance."
    elif final_score >= 45.0:
        level = PriorityLevel.HIGH
        summary = "High operational priority: Significant violations or unverified review items require prompt supervisory review."
    elif final_score >= 20.0:
        level = PriorityLevel.MEDIUM
        summary = "Medium operational priority: Standard compliance review or minor evidentiary gaps."
    else:
        level = PriorityLevel.LOW
        summary = "Low operational priority: Clean compliance findings and complete evidentiary record."

    return CasePriority(
        score=final_score,
        level=level,
        factors=factors,
        summary=summary,
    )


def generate_action_recommendations(
    inspection: Inspection,
    declaration: Optional[Declaration],
    checks: List[ComplianceCheck],
    violations: List[Violation],
    completeness: EvidenceCompleteness,
    priority: CasePriority,
    gravimetric_test: Optional[GravimetricTest] = None,
    company: Optional[Company] = None,
) -> List[ActionRecommendation]:
    """
    Generates deterministic, non-binding advisory next-step recommendations for inspecting officers and supervisors.
    Always marked is_advisory=True.
    Never autonomously initiates enforcement or issues statutory orders.
    """
    recs: List[ActionRecommendation] = []

    # 1. Blocking Evidence Gaps (Evidence Collection Recommendations)
    for gap in completeness.gaps:
        if gap.is_blocking:
            recs.append(
                ActionRecommendation(
                    code=f"REC_GAP_{gap.code}",
                    title=f"Resolve Evidence Gap: {gap.title}",
                    description=f"{gap.description} Required action: {gap.action}",
                    priority=PriorityLevel.HIGH if gap.severity == ViolationSeverity.HIGH else PriorityLevel.MEDIUM,
                    category=ActionRecommendationCategory.EVIDENCE_COLLECTION,
                    is_advisory=True,
                    related_rule=None,
                    action_label=gap.action[:30] + "..." if len(gap.action) > 30 else gap.action,
                )
            )

    # 2. NEEDS_REVIEW Resolution Guidance
    unresolved_reviews = [c for c in checks if c.result == CheckResult.REVIEW]
    if unresolved_reviews and (not declaration or not declaration.is_human_verified):
        review_rule_codes = ", ".join(c.legal_rule.rule_code for c in unresolved_reviews[:3] if c.legal_rule)
        recs.append(
            ActionRecommendation(
                code="REC_RESOLVE_REVIEWS",
                title="Perform Inspector Adjudication on Review Items",
                description=f"{len(unresolved_reviews)} compliance check(s) ({review_rule_codes}) require human inspection adjudication before finalization.",
                priority=PriorityLevel.HIGH,
                category=ActionRecommendationCategory.VERIFICATION,
                is_advisory=True,
                related_rule=unresolved_reviews[0].legal_rule.source_reference if unresolved_reviews[0].legal_rule else None,
                action_label="Open Review Workspace",
            )
        )

    # 3. Statutory Non-Compliance Advisory Guidance (Rule-aligned, non-autonomous)
    if violations and inspection.status != InspectionStatus.COMPLETED:
        critical_or_high = [v for v in violations if v.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH)]
        if critical_or_high:
            recs.append(
                ActionRecommendation(
                    code="REC_STATUTORY_VIOLATION_WORKFLOW",
                    title="Review Detected Statutory Violations",
                    description=f"{len(critical_or_high)} major statutory violation(s) identified. Review findings and prepare draft Section 36 show-cause memorandum for supervisory approval.",
                    priority=PriorityLevel.CRITICAL if any(v.severity == ViolationSeverity.CRITICAL for v in critical_or_high) else PriorityLevel.HIGH,
                    category=ActionRecommendationCategory.LEGAL_WORKFLOW,
                    is_advisory=True,
                    related_rule="Section 36(1), Legal Metrology Act, 2009",
                    action_label="Prepare Draft Notice",
                )
            )

    # 4. Compounding Fee Assessment Suggestion (Where non-compliant and section 36 applies)
    if inspection.overall_result == ComplianceResult.NON_COMPLIANT:
        recs.append(
            ActionRecommendation(
                code="REC_ASSESS_COMPOUNDING",
                title="Evaluate Section 48 Statutory Compounding",
                description="Use the Section 48 compounding calculator to evaluate statutory compounding eligibility and reference penalty limits for this offence tier.",
                priority=PriorityLevel.MEDIUM,
                category=ActionRecommendationCategory.LEGAL_WORKFLOW,
                is_advisory=True,
                related_rule="Section 48, Legal Metrology Act, 2009",
                action_label="Assess Compounding",
            )
        )

    # 5. Supervisory Finalization Guidance
    if inspection.status != InspectionStatus.COMPLETED and len(unresolved_reviews) == 0:
        if inspection.overall_result == ComplianceResult.COMPLIANT and completeness.score >= 80.0:
            recs.append(
                ActionRecommendation(
                    code="REC_SUPERVISORY_FINALIZATION",
                    title="Ready for Supervisory Finalization",
                    description="Inspection session meets evidentiary completeness standards with zero detected violations. Ready for supervisory sign-off and finalization.",
                    priority=PriorityLevel.LOW,
                    category=ActionRecommendationCategory.SUPERVISORY_ACTION,
                    is_advisory=True,
                    related_rule=None,
                    action_label="Finalize Inspection",
                )
            )

    return recs


async def get_case_intelligence(
    db: AsyncSession,
    inspection_id: uuid.UUID,
) -> CaseIntelligenceResponse:
    """
    Retrieves full operational case intelligence for an inspection session.
    Computes completeness, priority, and recommendations dynamically without mutating the database.
    """
    stmt = (
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            selectinload(Inspection.images).selectinload(InspectionImage.ocr_result),
            selectinload(Inspection.declaration),
            selectinload(Inspection.compliance_checks).selectinload(ComplianceCheck.legal_rule),
            selectinload(Inspection.violations),
            selectinload(Inspection.evidence_items),
            selectinload(Inspection.gravimetric_tests),
            selectinload(Inspection.company).selectinload(Company.nominated_directors),
        )
    )
    res = await db.execute(stmt)
    inspection = res.scalar_one_or_none()

    if not inspection:
        raise ValueError(f"Inspection with ID '{inspection_id}' not found.")

    images = list(inspection.images or [])
    ocr_results: List[OCRResult] = []
    for img in images:
        if img.ocr_result:
            ocr_results.append(img.ocr_result)

    declaration = inspection.declaration
    checks = list(inspection.compliance_checks or [])
    violations = list(inspection.violations or [])
    grav_tests = list(inspection.gravimetric_tests or [])
    gravimetric_test = grav_tests[0] if grav_tests else None
    company = getattr(inspection, "company", None)

    # Check repeat offender history from DB (same manufacturer or brand)
    repeat_offence_count = 0
    entity_name = None
    if declaration:
        entity_name = declaration.manufacturer_name or declaration.packer_name or declaration.importer_name

    if entity_name:
        repeat_stmt = (
            select(func.count(distinct(Inspection.id)))
            .select_from(Inspection)
            .join(Declaration, Inspection.id == Declaration.inspection_id)
            .where(
                Inspection.id != inspection_id,
                Inspection.overall_result == ComplianceResult.NON_COMPLIANT,
                or_(
                    Declaration.manufacturer_name.ilike(f"%{entity_name.strip()}%"),
                    Declaration.packer_name.ilike(f"%{entity_name.strip()}%"),
                    Declaration.importer_name.ilike(f"%{entity_name.strip()}%"),
                ),
            )
        )
        repeat_res = await db.execute(repeat_stmt)
        repeat_offence_count = int(repeat_res.scalar_one() or 0)

    # Calculate inspection age
    created_at = inspection.created_at or datetime.now(timezone.utc)
    now = datetime.now(timezone.utc)
    age_days = max(0, (now - created_at).days)

    # 1. Compute Evidence Completeness
    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=declaration,
        images=images,
        ocr_results=ocr_results,
        checks=checks,
        gravimetric_test=gravimetric_test,
        company=company,
    )

    # 2. Compute Case Priority
    priority = compute_case_priority(
        inspection=inspection,
        declaration=declaration,
        checks=checks,
        violations=violations,
        completeness=completeness,
        repeat_offence_count=repeat_offence_count,
        inspection_age_days=age_days,
    )

    # 3. Generate Advisory Action Recommendations
    recommendations = generate_action_recommendations(
        inspection=inspection,
        declaration=declaration,
        checks=checks,
        violations=violations,
        completeness=completeness,
        priority=priority,
        gravimetric_test=gravimetric_test,
        company=company,
    )

    legal_context = {
        "overall_result": inspection.overall_result.value if inspection.overall_result else "PENDING",
        "inspection_status": inspection.status.value if inspection.status else "CREATED",
        "store_name": inspection.store_name,
        "district": inspection.district,
        "state": inspection.state,
        "is_finalized": inspection.status == InspectionStatus.COMPLETED,
    }

    return CaseIntelligenceResponse(
        inspection_id=inspection.id,
        evidence_completeness=completeness,
        case_priority=priority,
        recommendations=recommendations,
        legal_context=legal_context,
    )


async def get_supervisor_triage_queue(
    db: AsyncSession,
    priority_level: Optional[str] = None,
    status_filter: Optional[str] = None,
    result_filter: Optional[str] = None,
    min_priority_score: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> SupervisorTriageResponse:
    """
    Builds the supervisor operational triage queue with dynamically calculated priority scores.
    Restricted to SUPERVISOR and ADMIN roles.
    """
    stmt = (
        select(Inspection)
        .options(
            selectinload(Inspection.inspector),
            selectinload(Inspection.images).selectinload(InspectionImage.ocr_result),
            selectinload(Inspection.declaration),
            selectinload(Inspection.compliance_checks).selectinload(ComplianceCheck.legal_rule),
            selectinload(Inspection.violations),
            selectinload(Inspection.gravimetric_tests),
            selectinload(Inspection.company).selectinload(Company.nominated_directors),
        )
        .order_by(Inspection.created_at.desc())
    )

    if status_filter:
        stmt = stmt.where(Inspection.status == InspectionStatus(status_filter))
    if result_filter:
        stmt = stmt.where(Inspection.overall_result == ComplianceResult(result_filter))

    res = await db.execute(stmt)
    all_inspections = res.scalars().all()

    now = datetime.now(timezone.utc)
    triage_items: List[SupervisorTriageItem] = []
    priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for insp in all_inspections:
        images = list(insp.images or [])
        ocr_results = [img.ocr_result for img in images if img.ocr_result]
        decl = insp.declaration
        checks = list(insp.compliance_checks or [])
        violations = list(insp.violations or [])
        g_tests = list(insp.gravimetric_tests or [])
        grav_test = g_tests[0] if g_tests else None
        comp = getattr(insp, "company", None)

        created_dt = insp.created_at or now
        age_days = max(0, (now - created_dt).days)

        # Basic entity name
        ent_name = None
        comm_name = None
        if decl:
            ent_name = decl.manufacturer_name or decl.packer_name or decl.importer_name
            comm_name = decl.commodity_name

        completeness = compute_evidence_completeness(
            inspection=insp,
            declaration=decl,
            images=images,
            ocr_results=ocr_results,
            checks=checks,
            gravimetric_test=grav_test,
            company=comp,
        )

        priority = compute_case_priority(
            inspection=insp,
            declaration=decl,
            checks=checks,
            violations=violations,
            completeness=completeness,
            repeat_offence_count=0,  # Quick calculation for bulk triage
            inspection_age_days=age_days,
        )

        priority_counts[priority.level.value] = priority_counts.get(priority.level.value, 0) + 1

        # Search filter
        if search:
            q = search.lower().strip()
            matches = (
                (insp.store_name and q in insp.store_name.lower())
                or (insp.district and q in insp.district.lower())
                or (insp.state and q in insp.state.lower())
                or (ent_name and q in ent_name.lower())
                or (comm_name and q in comm_name.lower())
                or (str(insp.id).lower().startswith(q))
            )
            if not matches:
                continue

        # Priority level filter
        if priority_level and priority.level.value != priority_level.upper():
            continue

        # Minimum score filter
        if min_priority_score is not None and priority.score < min_priority_score:
            continue

        unresolved_count = sum(1 for c in checks if c.result == CheckResult.REVIEW)
        max_sev = None
        if violations:
            if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
                max_sev = "CRITICAL"
            elif any(v.severity == ViolationSeverity.HIGH for v in violations):
                max_sev = "HIGH"
            elif any(v.severity == ViolationSeverity.MEDIUM for v in violations):
                max_sev = "MEDIUM"
            else:
                max_sev = "LOW"

        # Determine primary attention reason
        if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
            attention_reason = "CRITICAL statutory violation detected"
        elif any(v.severity == ViolationSeverity.HIGH for v in violations):
            attention_reason = "HIGH severity declaration violation"
        elif unresolved_count > 0:
            attention_reason = f"{unresolved_count} check(s) require inspector adjudication"
        elif completeness.score < 50.0:
            attention_reason = "Incomplete inspection evidence record"
        elif insp.status == InspectionStatus.REVIEW_REQUIRED:
            attention_reason = "Pending supervisor review & finalization"
        elif insp.overall_result == ComplianceResult.COMPLIANT:
            attention_reason = "Compliant inspection verified"
        else:
            attention_reason = "Standard inspection queue"

        triage_items.append(
            SupervisorTriageItem(
                inspection_id=insp.id,
                created_at=created_dt,
                store_name=insp.store_name,
                district=insp.district,
                state=insp.state,
                inspector_name=insp.inspector.name if insp.inspector else None,
                inspector_id=insp.inspector_id,
                entity_name=ent_name,
                commodity_name=comm_name,
                overall_result=insp.overall_result or ComplianceResult.PENDING,
                status=insp.status or InspectionStatus.CREATED,
                evidence_completeness_score=completeness.score,
                priority_score=priority.score,
                priority_level=priority.level,
                unresolved_review_count=unresolved_count,
                violation_count=len(violations),
                max_violation_severity=max_sev,
                primary_attention_reason=attention_reason,
                has_repeat_offence_history=False,
            )
        )

    # Sort triage items primarily by priority score DESC, then created_at DESC
    triage_items.sort(key=lambda x: (x.priority_score, x.created_at), reverse=True)

    total_count = len(triage_items)
    paginated_items = triage_items[offset : offset + limit]

    return SupervisorTriageResponse(
        total_items=total_count,
        items=paginated_items,
        priority_counts=priority_counts,
    )
