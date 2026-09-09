import asyncio
import datetime
import sys
from pathlib import Path
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.enums import (
    CheckResult,
    ComplianceResult,
    ImageType,
    InspectionStatus,
    UserRole,
    ViolationSeverity,
)
from app.core.security import create_access_token, get_password_hash
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.company import Company, NominatedDirector
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.gravimetric_test import GravimetricTest
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.legal_rule import LegalRule
from app.models.ocr_result import OCRResult
from app.models.user import User
from app.models.violation import Violation
from app.schemas.case_intelligence import EvidenceFacetStatus, PriorityLevel
from app.services.case_intelligence_service import (
    compute_case_priority,
    compute_evidence_completeness,
    generate_action_recommendations,
)


async def test_evidence_completeness_empty_inspection():
    """1. Empty inspection yields zero or low completeness with explicit gaps."""
    inspection = Inspection(
        id=uuid.uuid4(),
        status=InspectionStatus.CREATED,
        overall_result=ComplianceResult.PENDING,
    )
    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=None,
        images=[],
        ocr_results=[],
        checks=[],
    )
    assert completeness.score <= 30.0
    assert completeness.status in ["EMPTY", "INCOMPLETE"]
    assert len(completeness.gaps) >= 2
    gap_codes = [g.code for g in completeness.gaps]
    assert "MISSING_PACKAGE_IMAGES" in gap_codes
    assert "MISSING_DECLARATIONS_DATA" in gap_codes
    print("PASS: test_evidence_completeness_empty_inspection")


async def test_evidence_completeness_full_applicable():
    """2. Complete applicable evidence yields high/100 completeness."""
    inspection = Inspection(
        id=uuid.uuid4(),
        status=InspectionStatus.REVIEW_REQUIRED,
        overall_result=ComplianceResult.COMPLIANT,
    )
    images = [
        InspectionImage(id=uuid.uuid4(), inspection_id=inspection.id, image_type=ImageType.FRONT, image_url="/img1.jpg"),
        InspectionImage(id=uuid.uuid4(), inspection_id=inspection.id, image_type=ImageType.BACK, image_url="/img2.jpg"),
    ]
    ocr_results = [
        OCRResult(id=uuid.uuid4(), image_id=images[0].id, confidence=0.92, raw_text="Sample text"),
    ]
    declaration = Declaration(
        id=uuid.uuid4(),
        inspection_id=inspection.id,
        commodity_name="Atta",
        manufacturer_name="ITC Limited",
        address="37 J.L. Nehru Road, Kolkata 700071",
        net_quantity="5 kg",
        mrp="₹ 245.00",
        manufacturing_date="01/2026",
        consumer_care="1800-425-4444",
        is_human_verified=True,
    )

    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=declaration,
        images=images,
        ocr_results=ocr_results,
        checks=[],
    )
    assert completeness.score >= 90.0
    assert completeness.status == "EXCELLENT"
    print("PASS: test_evidence_completeness_full_applicable")


async def test_not_applicable_facet_does_not_penalize_score():
    """3. NOT_APPLICABLE facet (e.g. non-corporate, non-gravimetric) does not reduce score."""
    inspection = Inspection(
        id=uuid.uuid4(),
        status=InspectionStatus.REVIEW_REQUIRED,
        company_id=None,
        batch_id=None,
    )
    images = [
        InspectionImage(id=uuid.uuid4(), inspection_id=inspection.id, image_type=ImageType.FRONT, image_url="/f.jpg"),
        InspectionImage(id=uuid.uuid4(), inspection_id=inspection.id, image_type=ImageType.SIDE, image_url="/s.jpg"),
    ]
    declaration = Declaration(
        id=uuid.uuid4(),
        inspection_id=inspection.id,
        commodity_name="Biscuits",
        manufacturer_name="Bakery Enterprise",
        address="Plot 5, Industrial Area, Delhi 110020",
        net_quantity="100 g",
        mrp="₹ 20.00",
        manufacturing_date="02/2026",
        consumer_care="care@bakery.in",
        is_human_verified=True,
    )
    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=declaration,
        images=images,
        ocr_results=[],
        checks=[],
    )
    # Check that Facet 5 and 6 are NOT_APPLICABLE
    facet5 = next(f for f in completeness.facets if f.facet_code == "FACET_PHYSICAL_MEASUREMENT")
    facet6 = next(f for f in completeness.facets if f.facet_code == "FACET_CORPORATE_GOVERNANCE")
    assert facet5.status == EvidenceFacetStatus.NOT_APPLICABLE
    assert facet6.status == EvidenceFacetStatus.NOT_APPLICABLE
    assert completeness.score >= 90.0
    print("PASS: test_not_applicable_facet_does_not_penalize_score")


async def test_low_ocr_confidence_creates_gap():
    """4. Low OCR confidence creates an evidence gap."""
    inspection = Inspection(id=uuid.uuid4())
    images = [InspectionImage(id=uuid.uuid4(), inspection_id=inspection.id, image_type=ImageType.FRONT, image_url="/f.jpg")]
    ocr_results = [OCRResult(id=uuid.uuid4(), image_id=images[0].id, confidence=0.55, raw_text="Blurry text")]
    declaration = Declaration(
        id=uuid.uuid4(),
        inspection_id=inspection.id,
        commodity_name="Snacks",
        is_human_verified=False,
    )
    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=declaration,
        images=images,
        ocr_results=ocr_results,
        checks=[],
    )
    facet3 = next(f for f in completeness.facets if f.facet_code == "FACET_PERCEPTION_QUALITY")
    assert facet3.status == EvidenceFacetStatus.PARTIAL
    gap_codes = [g.code for g in completeness.gaps]
    assert "LOW_OCR_CONFIDENCE" in gap_codes
    print("PASS: test_low_ocr_confidence_creates_gap")


async def test_missing_physical_measurement_when_gravimetric_active():
    """5. Missing physical measurement creates gap only when gravimetric test is active."""
    inspection = Inspection(id=uuid.uuid4())
    grav_test = GravimetricTest(
        id=uuid.uuid4(),
        inspection_id=inspection.id,
        nominal_quantity_value=500.0,
        nominal_quantity_unit="g",
        sample_units_data=None,  # No readings logged
        created_by_id=uuid.uuid4(),
    )
    completeness = compute_evidence_completeness(
        inspection=inspection,
        declaration=None,
        images=[],
        ocr_results=[],
        checks=[],
        gravimetric_test=grav_test,
    )
    facet5 = next(f for f in completeness.facets if f.facet_code == "FACET_PHYSICAL_MEASUREMENT")
    assert facet5.status == EvidenceFacetStatus.PARTIAL
    gap_codes = [g.code for g in completeness.gaps]
    assert "INCOMPLETE_GRAVIMETRIC_LOG" in gap_codes
    print("PASS: test_missing_physical_measurement_when_gravimetric_active")


async def test_case_priority_clean_inspection():
    """6. Clean inspection with complete evidence yields LOW priority."""
    inspection = Inspection(id=uuid.uuid4(), status=InspectionStatus.COMPLETED, overall_result=ComplianceResult.COMPLIANT)
    declaration = Declaration(id=uuid.uuid4(), is_human_verified=True)
    completeness = compute_evidence_completeness(inspection, declaration, [], [], [])
    priority = compute_case_priority(
        inspection=inspection,
        declaration=declaration,
        checks=[],
        violations=[],
        completeness=completeness,
        repeat_offence_count=0,
    )
    assert priority.level == PriorityLevel.LOW
    assert priority.score < 20.0
    print("PASS: test_case_priority_clean_inspection")


async def test_case_priority_severe_violations_and_repeat_offender():
    """7 & 8. Multiple high/critical violations and repeat offender increase priority."""
    inspection = Inspection(id=uuid.uuid4(), status=InspectionStatus.REVIEW_REQUIRED, overall_result=ComplianceResult.NON_COMPLIANT)
    violations = [
        Violation(id=uuid.uuid4(), severity=ViolationSeverity.CRITICAL, title="Deceptive Slack Fill"),
        Violation(id=uuid.uuid4(), severity=ViolationSeverity.HIGH, title="Missing Mandatory Net Quantity"),
    ]
    declaration = Declaration(id=uuid.uuid4(), is_human_verified=False)
    completeness = compute_evidence_completeness(inspection, declaration, [], [], [])
    priority = compute_case_priority(
        inspection=inspection,
        declaration=declaration,
        checks=[],
        violations=violations,
        completeness=completeness,
        repeat_offence_count=2,
    )
    assert priority.level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    assert priority.score >= 50.0
    factor_codes = [f.code for f in priority.factors]
    assert "CRITICAL_VIOLATIONS" in factor_codes
    assert "REPEAT_OFFENDER_HISTORY" in factor_codes
    print("PASS: test_case_priority_severe_violations_and_repeat_offender")


async def test_priority_never_alters_legal_result():
    """10. Legal invariant: Priority calculation NEVER mutates legal result."""
    inspection = Inspection(id=uuid.uuid4(), status=InspectionStatus.REVIEW_REQUIRED, overall_result=ComplianceResult.COMPLIANT)
    # Even if artificially high priority factors exist:
    violations = [Violation(id=uuid.uuid4(), severity=ViolationSeverity.CRITICAL, title="Critical Finding")]
    completeness = compute_evidence_completeness(inspection, None, [], [], [])
    priority = compute_case_priority(
        inspection=inspection,
        declaration=None,
        checks=[],
        violations=violations,
        completeness=completeness,
        repeat_offence_count=3,
    )
    assert priority.level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    # The underlying inspection legal result remains strictly COMPLIANT!
    assert inspection.overall_result == ComplianceResult.COMPLIANT
    print("PASS: test_priority_never_alters_legal_result")


async def test_action_recommendations_advisory_invariant():
    """11-14. Recommendations are always advisory (is_advisory=True) with actionable guidance."""
    inspection = Inspection(id=uuid.uuid4(), status=InspectionStatus.REVIEW_REQUIRED, overall_result=ComplianceResult.NON_COMPLIANT)
    rule = LegalRule(id=uuid.uuid4(), rule_code="LMPC-RULE-06-MRP", title="MRP Declaration", source_reference="Rule 6(1)(e)")
    check = ComplianceCheck(id=uuid.uuid4(), legal_rule=rule, result=CheckResult.REVIEW)
    violations = [Violation(id=uuid.uuid4(), severity=ViolationSeverity.HIGH, title="Missing MRP")]
    completeness = compute_evidence_completeness(inspection, None, [], [], [check])
    priority = compute_case_priority(inspection, None, [check], violations, completeness)

    recs = generate_action_recommendations(
        inspection=inspection,
        declaration=None,
        checks=[check],
        violations=violations,
        completeness=completeness,
        priority=priority,
    )

    assert len(recs) >= 1
    for r in recs:
        assert r.is_advisory is True
        assert r.action_label is not None
        assert len(r.title) > 0
    print("PASS: test_action_recommendations_advisory_invariant")


async def test_rbac_and_supervisor_triage_endpoints():
    """15 & 16. Supervisor can access /triage; inspector cannot."""
    async with AsyncSessionLocal() as session:
        insp_user = User(
            id=uuid.uuid4(),
            email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("Pass123!"),
            name="Field Officer Rajesh",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        sup_user = User(
            id=uuid.uuid4(),
            email=f"supervisor_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("Pass123!"),
            name="Supervisor Patel",
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        session.add(insp_user)
        session.add(sup_user)
        await session.commit()

        insp_token = create_access_token(subject=str(insp_user.id))
        sup_token = create_access_token(subject=str(sup_user.id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Access as supervisor
        res_sup = await ac.get("/api/v1/inspections/triage", headers={"Authorization": f"Bearer {sup_token}"})
        assert res_sup.status_code == 200
        data = res_sup.json()
        assert "total_items" in data
        assert "items" in data
        assert "priority_counts" in data

        # 2. Access as inspector -> 403 Forbidden
        res_insp = await ac.get("/api/v1/inspections/triage", headers={"Authorization": f"Bearer {insp_token}"})
        assert res_insp.status_code == 403

    print("PASS: test_rbac_and_supervisor_triage_endpoints")


async def test_inspection_case_intelligence_endpoint():
    """17 & 18. Case intelligence endpoint returns full response and does not mutate finalized case."""
    async with AsyncSessionLocal() as session:
        insp_user = User(
            id=uuid.uuid4(),
            email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("Pass123!"),
            name="Field Officer Neha",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        other_user = User(
            id=uuid.uuid4(),
            email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("Pass123!"),
            name="Field Officer Other",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        session.add(insp_user)
        session.add(other_user)
        await session.commit()

        insp_token = create_access_token(subject=str(insp_user.id))
        other_token = create_access_token(subject=str(other_user.id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create an inspection as inspector
        create_res = await ac.post(
            "/api/v1/inspections/",
            headers={"Authorization": f"Bearer {insp_token}"},
            json={"store_name": "Intelligence Test Store", "state": "Delhi", "district": "New Delhi"},
        )
        assert create_res.status_code == 201
        insp_id = create_res.json()["id"]

        # 2. Query intelligence by creator
        intel_res = await ac.get(f"/api/v1/inspections/{insp_id}/intelligence", headers={"Authorization": f"Bearer {insp_token}"})
        assert intel_res.status_code == 200
        intel_data = intel_res.json()
        assert intel_data["inspection_id"] == insp_id
        assert "evidence_completeness" in intel_data
        assert "case_priority" in intel_data
        assert "recommendations" in intel_data
        assert intel_data["evidence_completeness"]["score"] >= 0.0
        assert intel_data["case_priority"]["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        # 3. Query intelligence by unauthorized inspector -> 403 Forbidden
        unauth_res = await ac.get(f"/api/v1/inspections/{insp_id}/intelligence", headers={"Authorization": f"Bearer {other_token}"})
        assert unauth_res.status_code == 403

        # 4. Finalize inspection
        fin_res = await ac.post(
            f"/api/v1/inspections/{insp_id}/finalize",
            headers={"Authorization": f"Bearer {insp_token}"},
            json={"override_result": "COMPLIANT", "finalization_notes": "All verified"},
        )
        assert fin_res.status_code == 200

        # 5. Query intelligence on finalized inspection (remains read-only and succeeds)
        intel_res2 = await ac.get(f"/api/v1/inspections/{insp_id}/intelligence", headers={"Authorization": f"Bearer {insp_token}"})
        assert intel_res2.status_code == 200
        assert intel_res2.json()["legal_context"]["is_finalized"] is True

    print("PASS: test_inspection_case_intelligence_endpoint")


async def test_needs_review_immutability_under_case_intelligence():
    """19. Verified Invariant: Case Intelligence never alters NEEDS_REVIEW to NON_COMPLIANT or vice versa."""
    inspection = Inspection(
        id=uuid.uuid4(),
        status=InspectionStatus.REVIEW_REQUIRED,
        overall_result=ComplianceResult.NEEDS_REVIEW,
    )
    rule = LegalRule(id=uuid.uuid4(), rule_code="LMPC-RULE-06-MRP", title="MRP Declaration", source_reference="Rule 6(1)(e)")
    check = ComplianceCheck(id=uuid.uuid4(), legal_rule=rule, result=CheckResult.REVIEW)
    completeness = compute_evidence_completeness(inspection, None, [], [], [check])
    priority = compute_case_priority(
        inspection=inspection,
        declaration=None,
        checks=[check],
        violations=[],
        completeness=completeness,
        repeat_offence_count=5,  # High repeat count
        inspection_age_days=10,   # Aging queue
    )
    recs = generate_action_recommendations(
        inspection=inspection,
        declaration=None,
        checks=[check],
        violations=[],
        completeness=completeness,
        priority=priority,
    )
    # The inspection's overall result remains strictly NEEDS_REVIEW
    assert inspection.overall_result == ComplianceResult.NEEDS_REVIEW
    assert priority.level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    # Recommendations point to human adjudication, not autonomous penalty
    rec_codes = [r.code for r in recs]
    assert "REC_RESOLVE_REVIEWS" in rec_codes
    print("PASS: test_needs_review_immutability_under_case_intelligence")


async def test_advisory_wording_safety():
    """20. Verified Invariant: Advisory text avoids autonomous enforcement words."""
    inspection = Inspection(
        id=uuid.uuid4(),
        status=InspectionStatus.REVIEW_REQUIRED,
        overall_result=ComplianceResult.NON_COMPLIANT,
    )
    rule = LegalRule(id=uuid.uuid4(), rule_code="LMPC-RULE-06-NETQTY", title="Net Quantity", source_reference="Rule 6(1)(d)")
    check = ComplianceCheck(id=uuid.uuid4(), legal_rule=rule, result=CheckResult.FAIL)
    violations = [Violation(id=uuid.uuid4(), severity=ViolationSeverity.CRITICAL, title="Severe Deficit")]
    completeness = compute_evidence_completeness(inspection, None, [], [], [check])
    priority = compute_case_priority(inspection, None, [check], violations, completeness)
    recs = generate_action_recommendations(
        inspection=inspection,
        declaration=None,
        checks=[check],
        violations=violations,
        completeness=completeness,
        priority=priority,
    )

    forbidden_autonomous_terms = [
        "system ordered",
        "guilty",
        "convicted",
        "automatically fined",
        "autonomous seizure executed",
        "live mca verified",
    ]

    for rec in recs:
        assert rec.is_advisory is True
        text_corpus = f"{rec.title} {rec.description} {rec.action_label}".lower()
        for forbidden in forbidden_autonomous_terms:
            assert forbidden not in text_corpus, f"Forbidden autonomous enforcement phrase found: '{forbidden}'"

    print("PASS: test_advisory_wording_safety")


if __name__ == "__main__":
    async def run_all():
        print("\n=======================================================")
        print("  RUNNING PHASE 2.9 CASE INTELLIGENCE TEST SUITE       ")
        print("=======================================================\n")
        await test_evidence_completeness_empty_inspection()
        await test_evidence_completeness_full_applicable()
        await test_not_applicable_facet_does_not_penalize_score()
        await test_low_ocr_confidence_creates_gap()
        await test_missing_physical_measurement_when_gravimetric_active()
        await test_case_priority_clean_inspection()
        await test_case_priority_severe_violations_and_repeat_offender()
        await test_priority_never_alters_legal_result()
        await test_action_recommendations_advisory_invariant()
        await test_rbac_and_supervisor_triage_endpoints()
        await test_inspection_case_intelligence_endpoint()
        await test_needs_review_immutability_under_case_intelligence()
        await test_advisory_wording_safety()
        print("\n=======================================================")
        print("  ALL PHASE 2.9 TESTS PASSED SUCCESSFULLY! (13/13)    ")
        print("=======================================================\n")

    asyncio.run(run_all())
