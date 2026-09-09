import asyncio
from datetime import date, datetime, timezone
from pathlib import Path
import sys
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.enums import (
    CheckResult,
    ComplianceResult,
    DossierPriority,
    DossierStatus,
    InspectionStatus,
    ProductCategory,
    UserRole,
    ViolationSeverity,
    ViolationStatus,
)

from app.core.security import create_access_token, get_password_hash
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.company import Company, NominatedDirector
from app.models.compliance_check import ComplianceCheck
from app.models.dossier import DossierInspection, InvestigationDossier

from app.models.inspection import Inspection
from app.models.legal_rule import LegalRule
from app.models.seizure import SeizureItem, SeizureRecord
from app.models.user import User
from app.models.violation import Violation
from app.schemas.dossier import (
    DossierInspectionCreate,
    InvestigationDossierCreate,
    InvestigationDossierUpdate,
)
from app.services.dossier_service import DossierService


# =============================================================================
# FIXTURES & HELPERS
# =============================================================================

async def setup_test_users(db):
    """Creates test admin, supervisor, and two distinct inspectors."""
    pwd_hash = get_password_hash("SecretPassword123!")

    # 1. Admin
    admin = await db.execute(select(User).where(User.email == "dossier_admin@gov.in"))
    admin_user = admin.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            name="Dossier Admin Officer",
            email="dossier_admin@gov.in",
            password_hash=pwd_hash,
            role=UserRole.ADMIN,
        )
        db.add(admin_user)

    # 2. Supervisor
    sup = await db.execute(select(User).where(User.email == "dossier_sup@gov.in"))
    sup_user = sup.scalar_one_or_none()
    if not sup_user:
        sup_user = User(
            name="Lead Surveillance Supervisor",
            email="dossier_sup@gov.in",
            password_hash=pwd_hash,
            role=UserRole.SUPERVISOR,
        )
        db.add(sup_user)

    # 3. Inspector A
    insp_a = await db.execute(select(User).where(User.email == "inspector_alpha@gov.in"))
    insp_a_user = insp_a.scalar_one_or_none()
    if not insp_a_user:
        insp_a_user = User(
            name="Field Inspector Alpha",
            email="inspector_alpha@gov.in",
            password_hash=pwd_hash,
            role=UserRole.INSPECTOR,
        )
        db.add(insp_a_user)

    # 4. Inspector B (unrelated inspector)
    insp_b = await db.execute(select(User).where(User.email == "inspector_beta@gov.in"))
    insp_b_user = insp_b.scalar_one_or_none()
    if not insp_b_user:
        insp_b_user = User(
            name="Field Inspector Beta",
            email="inspector_beta@gov.in",
            password_hash=pwd_hash,
            role=UserRole.INSPECTOR,
        )
        db.add(insp_b_user)

    await db.commit()
    await db.refresh(admin_user)
    await db.refresh(sup_user)
    await db.refresh(insp_a_user)
    await db.refresh(insp_b_user)

    return admin_user, sup_user, insp_a_user, insp_b_user


async def create_sample_inspection(
    db,
    inspector_id: uuid.UUID,
    legal_result: ComplianceResult = ComplianceResult.NON_COMPLIANT,
    status: InspectionStatus = InspectionStatus.COMPLETED,
    store_name: str = "Surveillance Mart",
    city: str = "Bengaluru",
    state: str = "Karnataka",
) -> Inspection:
    """Creates a sample inspection with specified attributes."""
    insp = Inspection(
        inspector_id=inspector_id,
        store_name=store_name,
        district=city,
        state=state,
        status=status,
        overall_result=legal_result,
        finalized_at=datetime.now(timezone.utc) if status == InspectionStatus.COMPLETED else None,
    )
    db.add(insp)
    await db.commit()
    await db.refresh(insp)
    return insp



# =============================================================================
# TEST SUITE IMPLEMENTATION
# =============================================================================

async def test_01_supervisor_can_create_dossier():
    """1. Supervisor can create an investigation dossier via service & API."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/dossiers/",
            json={
                "title": "Operation Clean Retail - FMCG Brand Audit",
                "description": "Cross-district surveillance of packaged edible oils.",
                "target_entity_name": "Apex Edibles Ltd",
                "priority": "HIGH",
            },
            headers=headers,
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["title"] == "Operation Clean Retail - FMCG Brand Audit"
        assert data["dossier_number"].startswith("DOS-")
        assert data["status"] == "ACTIVE"
        assert data["priority"] == "HIGH"
        assert data["lead_supervisor_id"] == str(sup_user.id)
        print("PASS: test_01_supervisor_can_create_dossier")


async def test_02_inspector_cannot_create_dossier():
    """2. Inspector role is prohibited from creating dossiers (403 Forbidden)."""
    async with AsyncSessionLocal() as db:
        _, _, insp_a_user, _ = await setup_test_users(db)

    token = create_access_token(insp_a_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/dossiers/",
            json={"title": "Unauthorized Inspector Dossier"},
            headers=headers,
        )
        assert res.status_code == 403, res.text
        print("PASS: test_02_inspector_cannot_create_dossier")


async def test_03_supervisor_can_link_inspection():
    """3. Supervisor can link an existing inspection with contextual relevance notes."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Test Link Dossier", target_entity_name="Test Brand"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/dossiers/{dossier.id}/inspections",
            json={
                "inspection_id": str(insp.id),
                "relevance_notes": "Inspection included because same target brand was observed.",
            },
            headers=headers,
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["dossier_id"] == str(dossier.id)
        assert data["inspection_id"] == str(insp.id)
        assert "same target brand was observed" in data["relevance_notes"]
        print("PASS: test_03_supervisor_can_link_inspection")


async def test_04_inspector_cannot_link_inspection():
    """4. Inspector cannot link an inspection to a dossier (403 Forbidden)."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="RBAC Dossier"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)

    token = create_access_token(insp_a_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/dossiers/{dossier.id}/inspections",
            json={"inspection_id": str(insp.id)},
            headers=headers,
        )
        assert res.status_code == 403
        print("PASS: test_04_inspector_cannot_link_inspection")


async def test_05_duplicate_inspection_link_rejected():
    """5. Linking the same inspection twice to the same dossier is rejected (400 Bad Request)."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Duplicate Link Test"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/dossiers/{dossier.id}/inspections",
            json={"inspection_id": str(insp.id)},
            headers=headers,
        )
        assert res.status_code == 400
        assert "already linked" in res.json()["detail"].lower()
        print("PASS: test_05_duplicate_inspection_link_rejected")


async def test_06_unlink_does_not_delete_inspection():
    """6. Unlinking an inspection removes only the associative relationship; underlying inspection remains intact."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Unlink Isolation Test"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.delete(
            f"/api/v1/dossiers/{dossier.id}/inspections/{insp.id}",
            headers=headers,
        )
        assert res.status_code == 200, res.text

    # Verify underlying inspection still exists in database
    async with AsyncSessionLocal() as db:
        existing_insp = await db.get(Inspection, insp.id)
        assert existing_insp is not None
        # Verify link is deleted
        link = (
            await db.execute(
                select(DossierInspection).where(
                    DossierInspection.dossier_id == dossier.id,
                    DossierInspection.inspection_id == insp.id,
                )
            )
        ).scalar_one_or_none()
        assert link is None
    print("PASS: test_06_unlink_does_not_delete_inspection")


async def test_07_dossier_deletion_does_not_delete_inspection():
    """7. Deleting a dossier does NOT delete or mutate the underlying inspection records."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Dossier Delete Cascade Test"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        # Delete dossier directly
        await db.delete(dossier)
        await db.commit()

        # Verify inspection is intact
        persisted_insp = await db.get(Inspection, insp.id)
        assert persisted_insp is not None
    print("PASS: test_07_dossier_deletion_does_not_delete_inspection")


async def test_08_finalized_inspection_can_be_linked_and_read():
    """8. A finalized inspection can be linked to a dossier and read without mutation."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Finalized Inspection Read Test"),
            sup_user.id,
        )
        finalized_insp = await create_sample_inspection(
            db,
            insp_a_user.id,
            legal_result=ComplianceResult.NON_COMPLIANT,
            status=InspectionStatus.COMPLETED,
        )

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Link finalized inspection
        res_link = await client.post(
            f"/api/v1/dossiers/{dossier.id}/inspections",
            json={"inspection_id": str(finalized_insp.id)},
            headers=headers,
        )
        assert res_link.status_code == 201

        # Read dossier detail
        res_get = await client.get(f"/api/v1/dossiers/{dossier.id}", headers=headers)
        assert res_get.status_code == 200
        detail = res_get.json()
        assert len(detail["dossier_inspections"]) == 1
        link_data = detail["dossier_inspections"][0]
        assert link_data["inspection_id"] == str(finalized_insp.id)
        assert link_data["legal_result"] == "NON_COMPLIANT"
        assert link_data["inspection_status"] == "COMPLETED"
    print("PASS: test_08_finalized_inspection_can_be_linked_and_read")


async def test_09_inspection_legal_result_remains_unchanged_after_linking():
    """9. Statutory legal result is strictly immutable; linking does not touch compliance result."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Immutability Verification Dossier"),
            sup_user.id,
        )
        insp_review = await create_sample_inspection(
            db,
            insp_a_user.id,
            legal_result=ComplianceResult.NEEDS_REVIEW,
            status=InspectionStatus.REVIEW_REQUIRED,
        )

        # Link
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp_review.id), sup_user
        )

        # Re-fetch inspection directly from DB
        refreshed = await db.get(Inspection, insp_review.id)
        assert refreshed.overall_result == ComplianceResult.NEEDS_REVIEW
        assert refreshed.status == InspectionStatus.REVIEW_REQUIRED
    print("PASS: test_09_inspection_legal_result_remains_unchanged_after_linking")



async def test_10_synthesis_counts_linked_inspections_correctly():
    """10. Dossier synthesis counts linked inspections accurately."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Synthesis Count Test"),
            sup_user.id,
        )
        insp1 = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.COMPLIANT, InspectionStatus.COMPLETED)
        insp2 = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.NON_COMPLIANT, InspectionStatus.COMPLETED)
        insp3 = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.NEEDS_REVIEW, InspectionStatus.REVIEW_REQUIRED)

        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp1.id), sup_user)
        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp2.id), sup_user)
        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp3.id), sup_user)

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.summary_counts.total_inspections == 3
        assert synthesis.summary_counts.completed_inspections == 2
        assert synthesis.summary_counts.review_required_inspections == 1
    print("PASS: test_10_synthesis_counts_linked_inspections_correctly")


async def test_11_synthesis_separates_verdicts():
    """11. Dossier synthesis cleanly separates COMPLIANT, NON_COMPLIANT, and NEEDS_REVIEW counts."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Verdict Separation Dossier"),
            sup_user.id,
        )
        insp_c = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.COMPLIANT)
        insp_nc = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.NON_COMPLIANT)
        insp_nr = await create_sample_inspection(db, insp_a_user.id, ComplianceResult.NEEDS_REVIEW)

        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp_c.id), sup_user)
        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp_nc.id), sup_user)
        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp_nr.id), sup_user)

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.summary_counts.compliant_count == 1
        assert synthesis.summary_counts.non_compliant_count == 1
        assert synthesis.summary_counts.needs_review_count == 1
    print("PASS: test_11_synthesis_separates_verdicts")


async def test_12_synthesis_aggregates_recorded_seizure_quantities():
    """12. Dossier synthesis aggregates recorded seizure quantities arithmetic-only with safe disclaimer."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Seizure Aggregation Dossier"),
            sup_user.id,
        )
        insp1 = await create_sample_inspection(db, insp_a_user.id)
        insp2 = await create_sample_inspection(db, insp_a_user.id)

        # Create Seizure Records
        sr1 = SeizureRecord(
            inspection_id=insp1.id,
            inspecting_officer_id=sup_user.id,
            seizure_memo_number=f"PAN-{uuid.uuid4().hex[:8].upper()}",
            premises_name="Warehouse A",
            premises_address="Warehouse A Address",
            seizure_date=datetime.now(timezone.utc),
            witness_1_name="Witness 1",
            witness_1_address="Address 1",
            witness_2_name="Witness 2",
            witness_2_address="Address 2",
            statutory_grounds="Suspected Rule 6 non-compliance",
        )
        sr2 = SeizureRecord(
            inspection_id=insp2.id,
            inspecting_officer_id=sup_user.id,
            seizure_memo_number=f"PAN-{uuid.uuid4().hex[:8].upper()}",
            premises_name="Warehouse B",
            premises_address="Warehouse B Address",
            seizure_date=datetime.now(timezone.utc),
            witness_1_name="Witness 1",
            witness_1_address="Address 1",
            witness_2_name="Witness 2",
            witness_2_address="Address 2",
            statutory_grounds="Suspected Rule 18 violation",
        )
        db.add_all([sr1, sr2])
        await db.commit()
        await db.refresh(sr1)
        await db.refresh(sr2)

        item1 = SeizureItem(
            seizure_id=sr1.id,
            commodity_name="Edible Oil 1L Packs",
            total_packages_seized=50,
        )
        item2 = SeizureItem(
            seizure_id=sr2.id,
            commodity_name="Edible Oil 5L Tins",
            total_packages_seized=100,
        )
        db.add_all([item1, item2])
        await db.commit()


        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp1.id), sup_user)
        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp2.id), sup_user)

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.seizure_summary.total_seizure_records == 2
        assert synthesis.seizure_summary.total_seized_quantity == 150.0
        assert synthesis.seizure_summary.seizure_items_count == 2
        assert "Recorded seizure quantity" in synthesis.seizure_summary.description
    print("PASS: test_12_synthesis_aggregates_recorded_seizure_quantities")


async def test_13_synthesis_does_not_create_new_legal_violations():
    """13. Dossier synthesis groups existing findings as 'Observed finding pattern', not new statutory violations."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Finding Grouping Dossier"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)

        # Query or create a test legal rule
        rule_stmt = select(LegalRule).limit(1)
        rule = (await db.execute(rule_stmt)).scalar_one_or_none()
        if not rule:
            rule = LegalRule(
                rule_code="TEST_RULE_6_1",
                name="Rule 6(1) Declarations",
                statutory_reference="Rule 6(1), LM(PC) Rules 2011",
                rule_type="REQUIRED_FIELD",
            )
            db.add(rule)
            await db.commit()
            await db.refresh(rule)

        cc = ComplianceCheck(
            inspection_id=insp.id,
            legal_rule_id=rule.id,
            result=CheckResult.FAIL,
        )
        db.add(cc)
        await db.commit()
        await db.refresh(cc)

        violation = Violation(
            inspection_id=insp.id,
            compliance_check_id=cc.id,
            severity=ViolationSeverity.HIGH,
            status=ViolationStatus.OPEN,
            title="Missing Mandatory Declaration",
            description="Rule 6(1) violation",
            rule_citation="Rule 6(1)",
        )
        db.add(violation)
        await db.commit()

        await DossierService.link_inspection(db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user)

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert len(synthesis.observed_findings) >= 1
        finding = synthesis.observed_findings[0]
        assert finding.observation_label == "Observed finding pattern"
        assert finding.affected_inspection_count == 1
    print("PASS: test_13_synthesis_does_not_create_new_legal_violations")



async def test_14_company_association_remains_explicit():
    """14. Company linkage requires explicit user selection; target_entity_name does not auto-link company."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)

        # Create company
        cin_code = f"L{uuid.uuid4().hex[:7].upper()}2026PLC000001"
        comp = Company(
            cin=cin_code,
            company_name="Explicit Industries Ltd",
            registered_office="123 Corporate Road, Mumbai",
            state="Maharashtra",
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)

        # 1. Create dossier with matching text name but NO company_id
        dossier_unlinked = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Unlinked Corporate Text Dossier",
                target_entity_name="Explicit Industries Ltd",
                company_id=None,
            ),
            sup_user.id,
        )
        assert dossier_unlinked.company_id is None
        assert dossier_unlinked.company is None

        # 2. Create dossier WITH explicit company_id
        dossier_linked = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Explicit Corporate Dossier",
                target_entity_name="Explicit Industries Ltd",
                company_id=comp.id,
            ),
            sup_user.id,
        )
        assert dossier_linked.company_id == comp.id
        assert dossier_linked.company.company_name == "Explicit Industries Ltd"
    print("PASS: test_14_company_association_remains_explicit")


async def test_15_nominated_director_information_remains_informational():
    """15. Nominated directors are presented as records for review with safe wording, never liable directors."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)

        cin_code = f"U{uuid.uuid4().hex[:7].upper()}2026PTC000002"
        comp = Company(
            cin=cin_code,
            company_name="Director Governance Corp Ltd",
            registered_office="789 Marine Lines, Mumbai",
            state="Maharashtra",
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)

        director = NominatedDirector(
            company_id=comp.id,
            director_name="Rajesh Kumar Sharma",
            din="00123456",
            designation="Managing Director",
            form_i_notice_date=date(2025, 1, 15),
            effective_from=date(2025, 1, 15),
        )
        db.add(director)
        await db.commit()

        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Director Review Dossier",
                company_id=comp.id,
            ),
            sup_user.id,
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert len(synthesis.nominated_directors_review) == 1
        dir_info = synthesis.nominated_directors_review[0]
        assert dir_info.director_name == "Rajesh Kumar Sharma"
        assert "for authorized officer review" in dir_info.review_note
        assert "liable" not in dir_info.review_note.lower()
        assert "guilty" not in dir_info.review_note.lower()
    print("PASS: test_15_nominated_director_information_remains_informational")


async def test_16_no_fuzzy_company_inference():
    """16. Similar company names are never fuzzily linked to a corporate record."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)

        # Name is close to an existing company but company_id is omitted
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Fuzzy Non-Inference Test",
                target_entity_name="Explicit Industry Limited",  # slight typo
                company_id=None,
            ),
            sup_user.id,
        )
        assert dossier.company_id is None
    print("PASS: test_16_no_fuzzy_company_inference")


async def test_17_unauthorized_inspector_cannot_access_unrelated_dossier():
    """17. Inspector B cannot access a dossier that does not contain any of their inspections (403 Forbidden)."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, insp_b_user = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Inspector Alpha Only Dossier"),
            sup_user.id,
        )
        # Link inspection authored by Inspector A
        insp_a = await create_sample_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp_a.id), sup_user
        )

    # Inspector B tries to access Inspector A's dossier
    token_b = create_access_token(insp_b_user.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"/api/v1/dossiers/{dossier.id}", headers=headers_b)
        assert res.status_code == 403, res.text

        # Also test synthesis access
        res_synth = await client.get(f"/api/v1/dossiers/{dossier.id}/synthesis", headers=headers_b)
        assert res_synth.status_code == 403
    print("PASS: test_17_unauthorized_inspector_cannot_access_unrelated_dossier")


async def test_18_supervisor_and_admin_access_works():
    """18. Supervisor and Admin have full access to view and manage any dossier."""
    async with AsyncSessionLocal() as db:
        admin_user, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Admin Supervisor Visibility Test"),
            sup_user.id,
        )

    token_admin = create_access_token(admin_user.id)
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"/api/v1/dossiers/{dossier.id}", headers=headers_admin)
        assert res.status_code == 200
        assert res.json()["title"] == "Admin Supervisor Visibility Test"
    print("PASS: test_18_supervisor_and_admin_access_works")


async def test_19_dossier_status_remains_workflow_only():
    """19. Dossier status strictly allows workflow states and rejects judicial verdict statuses."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Workflow Status Verification"),
            sup_user.id,
        )

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Valid workflow update
        for valid_status in ["EVALUATION", "NOTICE_REVIEW", "COMPOUNDING_REVIEW", "CLOSED"]:
            res = await client.patch(
                f"/api/v1/dossiers/{dossier.id}",
                json={"status": valid_status},
                headers=headers,
            )
            assert res.status_code == 200, res.text
            assert res.json()["status"] == valid_status

        # Invalid judicial status rejection
        for invalid_status in ["GUILTY", "PROSECUTION_RECOMMENDED", "LIABLE", "PENALIZED"]:
            res_bad = await client.patch(
                f"/api/v1/dossiers/{dossier.id}",
                json={"status": invalid_status},
                headers=headers,
            )
            assert res_bad.status_code == 422
    print("PASS: test_19_dossier_status_remains_workflow_only")


async def test_20_api_validation_rejects_invalid_references():
    """20. API rejects non-existent company_id or non-existent inspection_id."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)

    token = create_access_token(sup_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    non_existent_id = str(uuid.uuid4())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Non-existent company_id on create
        res_comp = await client.post(
            "/api/v1/dossiers/",
            json={"title": "Invalid Company Test", "company_id": non_existent_id},
            headers=headers,
        )
        assert res_comp.status_code == 400

        # 2. Non-existent inspection_id on link
        res_insp = await client.post(
            f"/api/v1/dossiers/{uuid.uuid4()}/inspections",
            json={"inspection_id": non_existent_id},
            headers=headers,
        )
        assert res_insp.status_code == 404
    print("PASS: test_20_api_validation_rejects_invalid_references")


async def test_21_audit_events_are_created():
    """21. Chronological audit events are logged in DB audit_logs and in dossier metadata."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Audit Trail Verification Dossier"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)

        # Link inspection
        await DossierService.link_inspection(
            db,
            dossier,
            DossierInspectionCreate(inspection_id=insp.id, relevance_notes="Audit note"),
            sup_user,
        )

        # Verify DB AuditLog entry
        stmt = select(AuditLog).where(
            AuditLog.inspection_id == insp.id,
            AuditLog.action == "DOSSIER_INSPECTION_LINKED",
        )
        audit_entry = (await db.execute(stmt)).scalar_one_or_none()
        assert audit_entry is not None
        assert audit_entry.actor_user_id == sup_user.id
        assert audit_entry.entity_type == "INVESTIGATION_DOSSIER"
        assert audit_entry.entity_id == dossier.id

        # Verify dossier metadata audit_logs
        refreshed_dossier = await DossierService.get_dossier(db, dossier.id)
        assert "audit_logs" in refreshed_dossier.metadata_
        actions = [log["action"] for log in refreshed_dossier.metadata_["audit_logs"]]
        assert "DOSSIER_CREATED" in actions
        assert "INSPECTION_LINKED" in actions
    print("PASS: test_21_audit_events_are_created")


async def test_22_advisory_wording_is_safe():
    """22. Advisory disclaimers and observation labels maintain strict non-judicial wording."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Advisory Safety Dossier"),
            sup_user.id,
        )
        synthesis = await DossierService.get_dossier_synthesis(db, dossier)

        disclaimer = synthesis.advisory_disclaimer
        assert "Individual inspection legal results remain authoritative" in disclaimer
        assert "Operational case-management view" in disclaimer

        # Verify no unsafe words appear in synthesis
        synth_json = synthesis.model_dump_json()
        assert "collective_guilt" not in synth_json
        assert "prosecution_required" not in synth_json
        assert "director_liable" not in synth_json
    print("PASS: test_22_advisory_wording_is_safe")


async def test_23_dossier_synthesis_is_read_only():
    """23. Executing dossier synthesis multiple times produces identical results without mutating state."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Read-Only Idempotence Dossier"),
            sup_user.id,
        )
        insp = await create_sample_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        synth1 = await DossierService.get_dossier_synthesis(db, dossier)
        synth2 = await DossierService.get_dossier_synthesis(db, dossier)

        assert synth1.summary_counts.total_inspections == synth2.summary_counts.total_inspections
        assert synth1.dossier_number == synth2.dossier_number
    print("PASS: test_23_dossier_synthesis_is_read_only")


# =============================================================================
# MAIN RUNNER
# =============================================================================

async def main():
    print("Running MetrologyMitra Phase 3.0 Dossier Test Suite (23 Tests)...")
    await test_01_supervisor_can_create_dossier()
    await test_02_inspector_cannot_create_dossier()
    await test_03_supervisor_can_link_inspection()
    await test_04_inspector_cannot_link_inspection()
    await test_05_duplicate_inspection_link_rejected()
    await test_06_unlink_does_not_delete_inspection()
    await test_07_dossier_deletion_does_not_delete_inspection()
    await test_08_finalized_inspection_can_be_linked_and_read()
    await test_09_inspection_legal_result_remains_unchanged_after_linking()
    await test_10_synthesis_counts_linked_inspections_correctly()
    await test_11_synthesis_separates_verdicts()
    await test_12_synthesis_aggregates_recorded_seizure_quantities()
    await test_13_synthesis_does_not_create_new_legal_violations()
    await test_14_company_association_remains_explicit()
    await test_15_nominated_director_information_remains_informational()
    await test_16_no_fuzzy_company_inference()
    await test_17_unauthorized_inspector_cannot_access_unrelated_dossier()
    await test_18_supervisor_and_admin_access_works()
    await test_19_dossier_status_remains_workflow_only()
    await test_20_api_validation_rejects_invalid_references()
    await test_21_audit_events_are_created()
    await test_22_advisory_wording_is_safe()
    await test_23_dossier_synthesis_is_read_only()
    print("\nALL 23 PHASE 3.0 DOSSIER TESTS PASSED (100%)!")


if __name__ == "__main__":
    asyncio.run(main())
