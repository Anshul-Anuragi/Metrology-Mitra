"""
Phase 4.1 — Validation Scenario Model & 16 Golden Scenarios
===========================================================
Defines the ValidationScenario dataclass and the complete 16-scenario
deterministic golden dataset verifying statutory metrology compliance,
boundary enforcement, evidence integrity, and safety constraints.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.enums import ComplianceResult
from app.validation.fixtures import (
    SYNTHETIC_COMPANY_RECORD,
    SYNTHETIC_COMPLIANT_DECLARATION,
    SYNTHETIC_GRAVIMETRIC_DEFICIT_LOT,
    SYNTHETIC_GRAVIMETRIC_PASSED_LOT,
    SYNTHETIC_MISSING_DECLARATIONS,
    SYNTHETIC_MULTILINGUAL_DECLARATION,
    SYNTHETIC_NON_STANDARD_UNIT_DECLARATION,
    SYNTHETIC_PACKER_REGISTRATION,
    SYNTHETIC_SEIZURE_RECORD,
)


@dataclass
class ValidationScenario:
    """
    Extensible validation scenario representation for MetrologyMitra.
    Supports statutory evaluation, evidence assessment, RBAC, and boundary verification.
    """
    scenario_id: str
    title: str
    category: str
    description: str
    input_data: Dict[str, Any]
    expected_legal_result: Optional[ComplianceResult]
    expected_evidence_state: Dict[str, Any] = field(default_factory=dict)
    expected_review_state: Dict[str, Any] = field(default_factory=dict)
    expected_legal_traceability: Dict[str, Any] = field(default_factory=dict)
    expected_safety_constraints: List[str] = field(default_factory=list)
    expected_report_behavior: Dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------------------------------
# THE 16 GOLDEN VALIDATION SCENARIOS
# -------------------------------------------------------------------------

GOLDEN_SCENARIOS: List[ValidationScenario] = [
    # SCENARIO 01: Fully compliant package
    ValidationScenario(
        scenario_id="SCENARIO-01",
        title="Fully Compliant Retail Package Evaluation",
        category="COMPLIANCE_EVALUATION",
        description=(
            "Package contains all mandatory declarations under Rule 6(1)(a)-(g), standard SI units "
            "under Rule 13, and calibrated PDP font height conforming to Schedule II Table 1. "
            "Must achieve COMPLIANT without treating advisory recommendations as legal determinations."
        ),
        input_data={
            "declaration": SYNTHETIC_COMPLIANT_DECLARATION,
            "channel": "PHYSICAL_PACKAGE",
            "is_human_verified": True,
        },
        expected_legal_result=ComplianceResult.COMPLIANT,
        expected_evidence_state={
            "all_declarations_present": True,
            "min_confidence": 0.95,
        },
        expected_review_state={
            "has_unresolved_reviews": False,
            "requires_retake": False,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 6(1)", "Rule 7", "Rule 13", "Second Schedule"],
            "corpus_id": "SIH-OFFICIAL-LEGAL-DATASET-2011",
        },
        expected_safety_constraints=[
            "NO_AUTONOMOUS_ENFORCEMENT",
            "NO_PROSECUTION_RECOMMENDATION",
            "ADVISORY_NOT_TREATED_AS_LEGAL_OUTCOME",
        ],
        expected_report_behavior={
            "status_rendered": "COMPLIANT",
            "disclaimer_present": True,
        },
    ),

    # SCENARIO 02: Missing mandatory declaration
    ValidationScenario(
        scenario_id="SCENARIO-02",
        title="Missing Mandatory Declarations (MRP & Consumer Care)",
        category="COMPLIANCE_EVALUATION",
        description=(
            "Package label completely omits Maximum Retail Price (MRP) and Consumer Care contact details. "
            "Must evaluate to deterministic NON_COMPLIANT with exact Rule 6(1)(e) and 6(1)(f) statutory citations, "
            "without generating arbitrary or fabricated penalties."
        ),
        input_data={
            "declaration": SYNTHETIC_MISSING_DECLARATIONS,
            "channel": "PHYSICAL_PACKAGE",
            "is_human_verified": False,
        },
        expected_legal_result=ComplianceResult.NON_COMPLIANT,
        expected_evidence_state={
            "missing_fields": ["mrp", "consumer_care"],
        },
        expected_review_state={
            "review_checks_count_ge": 1,
        },
        expected_legal_traceability={
            "failed_rule_codes": ["LMPC-R6-MRP", "LMPC-R6-CONSUMER-CARE"],
            "citations": ["Rule 6(1)(e)", "Rule 6(1)(f)"],
        },
        expected_safety_constraints=[
            "NO_FABRICATED_PENALTY",
            "NO_AUTONOMOUS_SANCTION",
        ],
        expected_report_behavior={
            "violations_listed": True,
            "non_judicial_notice": True,
        },
    ),

    # SCENARIO 03: Low-quality / ambiguous image
    ValidationScenario(
        scenario_id="SCENARIO-03",
        title="Low-Quality Optical Perception (Severe Glare & Blur)",
        category="IMAGE_QUALITY_AND_EVIDENCE",
        description=(
            "Image quality pre-flight detects severe optical blur and specular glare exceeding acceptable limits. "
            "System must flag RETAKE_RECOMMENDED, produce low OCR confidence, gate dependent checks to NEEDS_REVIEW, "
            "and NEVER guess or hallucinate unreadable statutory declarations."
        ),
        input_data={
            "quality_metrics": {
                "blur_variance": 42.0,       # Below 100 threshold
                "glare_percentage": 0.35,     # Above 0.15 threshold
                "resolution": [640, 480],
            },
            "declaration_snippet": {
                "commodity_name": "A",         # Single letter / unreadable text
                "net_quantity": None,
                "mrp": None,
            },
        },
        expected_legal_result=ComplianceResult.NEEDS_REVIEW,
        expected_evidence_state={
            "quality_gate_result": "RETAKE_RECOMMENDED",
            "optical_confidence_insufficient": True,
        },
        expected_review_state={
            "has_unresolved_reviews": True,
            "action_directive": "RETAKE_RECOMMENDED",
        },
        expected_legal_traceability={
            "standard_cited": "Pre-flight Perception Quality Gating",
        },
        expected_safety_constraints=[
            "DO_NOT_GUESS_DECLARATION",
            "NO_FALSE_PASS_ON_LOW_CONFIDENCE",
        ],
    ),

    # SCENARIO 04: Multilingual declaration
    ValidationScenario(
        scenario_id="SCENARIO-04",
        title="Multilingual Bilingual Declaration with Devanagari Numerals",
        category="MULTILINGUAL_PERCEPTION",
        description=(
            "Label declarations in Hindi (Devanagari script) and English. Includes Devanagari numerals (०-९). "
            "System must exercise bilingual parsing under Rule 6(1) and Rule 9, normalize numerals, "
            "and retain uncertainty reviewable if confidence differentials exist."
        ),
        input_data={
            "declaration": SYNTHETIC_MULTILINGUAL_DECLARATION,
            "channel": "PHYSICAL_PACKAGE",
        },
        expected_legal_result=ComplianceResult.COMPLIANT,
        expected_evidence_state={
            "script_detected": "MIXED",
            "devanagari_translation_successful": True,
        },
        expected_review_state={
            "reviewable_confidence": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 6(1)", "Rule 9"],
        },
        expected_safety_constraints=[
            "NO_UNVALIDATED_NORMALIZATION",
        ],
    ),

    # SCENARIO 05: Physical quantity verification (Gravimetric testing)
    ValidationScenario(
        scenario_id="SCENARIO-05",
        title="Physical Scale Gravimetric Testing & Sample Mean Deficit",
        category="PHYSICAL_METROLOGY",
        description=(
            "Physical gross/tare scale measurements on a 500g nominal lot yielding sample mean deficit (x̄ < Qn). "
            "Must reject under Rule 19 + Sixth Schedule as FAILED_MEAN_DEFICIT with First Schedule Table I MPE lookup. "
            "Camera/image estimates must NEVER be treated as statutory physical measurement."
        ),
        input_data=SYNTHETIC_GRAVIMETRIC_DEFICIT_LOT,
        expected_legal_result=None,  # Evaluated by gravimetric engine
        expected_evidence_state={
            "lot_decision": "FAILED_MEAN_DEFICIT",
            "mpe_value": 15.0,  # First Schedule Table 1 for 500g
        },
        expected_review_state={
            "requires_officer_review": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 19", "Sixth Schedule", "First Schedule Table 1"],
            "prohibited_references": ["Rule 24 as MPE"],
        },
        expected_safety_constraints=[
            "IMAGE_NOT_TREATED_AS_STATUTORY_MEASUREMENT",
            "PHYSICAL_EQUIPMENT_CALIBRATION_DISCLAIMER_PRESENT",
        ],
    ),

    # SCENARIO 06: Rule 3 applicability/exemption boundary
    ValidationScenario(
        scenario_id="SCENARIO-06",
        title="Rule 3 Applicability Scope & Inspection-Local Boundary",
        category="STATUTORY_APPLICABILITY",
        description=(
            "Inspection of bulk commodity. Verifies that Rule 3 (Chapter II applicability) is determined "
            "strictly at the individual inspection level, and an exempt inspection is NEVER generalized "
            "as a package-wide or dossier-level permanent exemption."
        ),
        input_data={
            "package_type": "AGRICULTURAL_BULK",
            "net_quantity_value": 60.0,
            "net_quantity_unit": "kg",
            "is_agricultural_farm_produce": True,
        },
        expected_legal_result=None,
        expected_evidence_state={
            "is_exempt": True,
            "assessment_status": "EXEMPTION_ELIGIBLE",
        },
        expected_review_state={
            "inspection_local_only": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 3", "Rule 26(d)"],
        },
        expected_safety_constraints=[
            "NO_GENERIC_LARGE_PACKAGE_EXEMPTION",
            "EXEMPTION_REMAINS_INSPECTION_LOCAL",
        ],
    ),

    # SCENARIO 07: Rule 26 statutory exemption & provisos
    ValidationScenario(
        scenario_id="SCENARIO-07",
        title="Rule 26 Statutory Exemptions & Provisos (Small Pack & Tobacco Exclusion)",
        category="STATUTORY_EXEMPTIONS",
        description=(
            "Tests Rule 26(a) small pack (<=10g) exemption eligibility. Verifies that tobacco products "
            "are explicitly DENIED exemption under Proviso 2 to Rule 26(a), and non-farm bulk packages >50kg "
            "are strictly gated to NEEDS_REVIEW."
        ),
        input_data={
            "test_cases": [
                {"net_quantity_value": 8.0, "net_quantity_unit": "g", "is_tobacco_product": False},
                {"net_quantity_value": 8.0, "net_quantity_unit": "g", "is_tobacco_product": True},
                {"net_quantity_value": 60.0, "net_quantity_unit": "kg", "is_agricultural_farm_produce": False},
            ]
        },
        expected_legal_result=None,
        expected_evidence_state={
            "tobacco_exemption_denied": True,
            "non_farm_bulk_needs_review": True,
        },
        expected_review_state={
            "provisos_evaluated": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 26(a)", "Rule 26(a) Proviso 2", "Rule 26(d)"],
        },
        expected_safety_constraints=[
            "NO_TOBACCO_EXEMPTION_PERMITTED",
            "NON_FARM_BULK_MUST_YIELD_NEEDS_REVIEW",
        ],
    ),

    # SCENARIO 08: MRP reference catalog discrepancy edge case
    ValidationScenario(
        scenario_id="SCENARIO-08",
        title="Neutral Reference MRP Discrepancy Evaluation",
        category="PRICING_COMPLIANCE",
        description=(
            "Observed package MRP differs from a reference product catalog. System must evaluate "
            "the finding neutrally as REVIEW under Rule 18(2) without auto-inferring tampering, fraud, or guilt."
        ),
        input_data={
            "observed_mrp": 180.0,
            "catalog_mrp": 150.0,
            "discrepancy": "MISMATCH",
        },
        expected_legal_result=ComplianceResult.NEEDS_REVIEW,
        expected_evidence_state={
            "neutral_reason_string": True,
        },
        expected_review_state={
            "requires_human_adjudication": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 18(2)"],
        },
        expected_safety_constraints=[
            "NO_TAMPERING_ACCUSATION",
            "NO_FRAUD_INFERENCE",
            "NEUTRAL_EVALUATION_MAINTAINED",
        ],
    ),

    # SCENARIO 09: Rule 27 Pre-Packer Registry lookup
    ValidationScenario(
        scenario_id="SCENARIO-09",
        title="Rule 27 Pre-Packer Registration Verification Context",
        category="REGULATORY_REGISTRY",
        description=(
            "Verifies pre-packer registration under Rule 27. System surfaces registry database record "
            "with ₹500 fee and 90-day filing context, strictly WITHOUT claiming live government API verification."
        ),
        input_data={
            "registration": SYNTHETIC_PACKER_REGISTRATION,
        },
        expected_legal_result=None,
        expected_evidence_state={
            "verification_status": "REGISTERED_VALID",
        },
        expected_review_state={
            "officer_verification_supported": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Rule 27", "Rule 28"],
        },
        expected_safety_constraints=[
            "NO_CLAIM_OF_LIVE_GOVERNMENT_VERIFICATION",
            "DISCLAIMER_EXPLICIT_ABOUT_REGISTRY_SCOPE",
        ],
    ),

    # SCENARIO 10: Evidence integrity & SHA-256 provenance hashing
    ValidationScenario(
        scenario_id="SCENARIO-10",
        title="Digital Evidence Provenance & SHA-256 Hash Tampering Detection",
        category="EVIDENCE_INTEGRITY",
        description=(
            "Verifies byte-level SHA-256 hashing on uploaded photographic evidence. "
            "Detects byte tampering or hash modification and ensures immutable audit logging."
        ),
        input_data={
            "original_bytes": b"SYNTHETIC_IMAGE_BYTES_VALIDATION_01",
            "tampered_bytes": b"SYNTHETIC_IMAGE_BYTES_VALIDATION_01_TAMPERED",
        },
        expected_legal_result=None,
        expected_evidence_state={
            "hashes_different": True,
            "tampering_detected": True,
        },
        expected_review_state={
            "audit_trail_recorded": True,
        },
        expected_legal_traceability={
            "standard_cited": "Digital Evidence Provenance & Integrity Registry",
        },
        expected_safety_constraints=[
            "TAMPERED_EVIDENCE_REJECTED",
        ],
    ),

    # SCENARIO 11: Finalized inspection mutation lock
    ValidationScenario(
        scenario_id="SCENARIO-11",
        title="Finalized Inspection Permanent Mutation Lock (HTTP 409)",
        category="LIFECYCLE_IMMUTABILITY",
        description=(
            "An inspection is finalized by an authorized inspector into COMPLETED status. "
            "Subsequent mutation attempts (review, edits, overrides) must be rejected with HTTP 409 Conflict."
        ),
        input_data={
            "finalize_action": True,
            "attempted_mutation": {"store_name": "Tampered Store Name"},
        },
        expected_legal_result=ComplianceResult.COMPLIANT,
        expected_evidence_state={
            "status_completed": True,
            "mutation_rejected_code": 409,
        },
        expected_review_state={
            "sealed": True,
        },
        expected_legal_traceability={
            "standard_cited": "Inspection Finalization & Mutation Lock",
        },
        expected_safety_constraints=[
            "NO_MUTATION_AFTER_FINALIZATION",
            "EVIDENCE_AND_RESULT_IMMUTABLE",
        ],
    ),

    # SCENARIO 12: Role-Based Access Control (RBAC)
    ValidationScenario(
        scenario_id="SCENARIO-12",
        title="Role-Based Access Control (Inspector, Supervisor, Admin)",
        category="SECURITY_RBAC",
        description=(
            "Validates object-level inspector scoping (inspectors cannot see unlinked inspections of other officers), "
            "supervisor triage queue access, and admin-only dossier deletion permission."
        ),
        input_data={
            "roles": ["INSPECTOR", "SUPERVISOR", "ADMIN"],
        },
        expected_legal_result=None,
        expected_evidence_state={
            "rbac_enforced": True,
        },
        expected_review_state={
            "unauthorized_actions_rejected": True,
        },
        expected_legal_traceability={
            "standard_cited": "Role-Based Access Control (RBAC) Security Matrix",
        },
        expected_safety_constraints=[
            "INSPECTORS_CANNOT_DELETE_DOSSIERS",
            "OBJECT_LEVEL_ISOLATION_ENFORCED",
        ],
    ),

    # SCENARIO 13: Corporate governance & Section 49 nominated director
    ValidationScenario(
        scenario_id="SCENARIO-13",
        title="Corporate Entity & Section 49 Nominated Director Non-Liability",
        category="CORPORATE_GOVERNANCE",
        description=(
            "Surfaces corporate record and Section 49(2) Form I nominated director for an inspection. "
            "Must provide informational review note without declaring the director automatically liable."
        ),
        input_data={
            "company": SYNTHETIC_COMPANY_RECORD,
        },
        expected_legal_result=None,
        expected_evidence_state={
            "director_name": "Rohan J. Mehta",
            "din": "09999999",
            "non_liability_disclaimer_present": True,
        },
        expected_review_state={
            "informational_only": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Section 49", "Section 49(2) Form I"],
        },
        expected_safety_constraints=[
            "NO_AUTOMATIC_DIRECTOR_LIABILITY",
            "EXPLICIT_NON_LIABILITY_NOTE_REQUIRED",
        ],
    ),

    # SCENARIO 14: Multi-inspection investigation dossier synthesis
    ValidationScenario(
        scenario_id="SCENARIO-14",
        title="Multi-Inspection Dossier Factual Synthesis & Zero Collective Guilt",
        category="INVESTIGATION_DOSSIER",
        description=(
            "Dossier contains multiple linked inspections with mixed verdicts. Verifies that synthesis "
            "aggregates factual counts and observed patterns without synthesizing an aggregate compliance verdict."
        ),
        input_data={
            "linked_verdicts": [ComplianceResult.NON_COMPLIANT, ComplianceResult.COMPLIANT, ComplianceResult.NEEDS_REVIEW],
        },
        expected_legal_result=None,  # Dossier has NO compliance verdict
        expected_evidence_state={
            "completed_inspections": 3,
            "non_compliant_count": 1,
            "compliant_count": 1,
            "needs_review_count": 1,
        },
        expected_review_state={
            "dossier_result_field_absent": True,
        },
        expected_legal_traceability={
            "standard_cited": "Multi-Inspection Case Synthesis & Evidence Grouping",
        },
        expected_safety_constraints=[
            "ZERO_COLLECTIVE_GUILT",
            "NO_DOSSIER_COMPLIANCE_VERDICT",
            "NO_REPEAT_OFFENDER_LEGAL_CONCLUSION",
        ],
    ),

    # SCENARIO 15: Recorded seizure aggregation
    ValidationScenario(
        scenario_id="SCENARIO-15",
        title="Section 15 Seizure Panchnama Aggregation & Custody Tracking",
        category="ENFORCEMENT_SEIZURE",
        description=(
            "Aggregates Section 15 seizure records within a dossier. Verifies that itemized package counts "
            "and custody locations aggregate factually without inferring additional seizure authority or penalties."
        ),
        input_data={
            "seizure": SYNTHETIC_SEIZURE_RECORD,
        },
        expected_legal_result=None,
        expected_evidence_state={
            "total_packages_seized": 40,
            "sample_packages_taken": 2,
            "witnesses_count": 2,
        },
        expected_review_state={
            "safe_custody_tracked": True,
        },
        expected_legal_traceability={
            "rules_referenced": ["Section 15", "Rule 29"],
        },
        expected_safety_constraints=[
            "NO_INFERRED_ADDITIONAL_SEIZURE_AUTHORITY",
            "PANCHNAMA_INDEPENDENT_WITNESS_MANDATE_ENFORCED",
        ],
    ),

    # SCENARIO 16: Consolidated evidence report generation
    ValidationScenario(
        scenario_id="SCENARIO-16",
        title="ReportLab Consolidated Evidence Report Non-Judicial Notice",
        category="REPORT_GENERATION",
        description=(
            "Generates ReportLab consolidated evidence dossier summary PDF. Verifies that document clearly "
            "identifies as a system-generated decision-support report with 14 mandatory sections and non-judicial disclaimers."
        ),
        input_data={
            "report_type": "CONSOLIDATED_DOSSIER_PDF",
        },
        expected_legal_result=None,
        expected_evidence_state={
            "all_14_sections_present": True,
            "page_compression_disabled_for_verification": True,
        },
        expected_review_state={
            "disclaimer_verified": True,
        },
        expected_legal_traceability={
            "corpus_id": "SIH-OFFICIAL-LEGAL-DATASET-2011",
            "all_seven_schedules_referenced": True,
        },
        expected_safety_constraints=[
            "NO_FAKE_GOVERNMENT_SEAL",
            "NO_OFFICIAL_GOVERNMENT_ORDER_CLAIM",
            "STATUTORY_NON_JUDICIAL_NOTICE_PRESENT",
        ],
    ),
]
