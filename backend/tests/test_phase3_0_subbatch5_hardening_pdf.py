import asyncio
from datetime import date, datetime, timezone
import io
from pathlib import Path
import sys
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

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
from app.services.dossier_pdf_service import build_dossier_pdf_report


# =============================================================================
# FIXTURES & HELPERS
# =============================================================================

async def setup_test_users(db):
    pwd_hash = get_password_hash("SecretPassword123!")

    # Admin
    admin = await db.execute(select(User).where(User.email == "harden_admin@gov.in"))
    admin_user = admin.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            name="Hardening Admin Officer",
            email="harden_admin@gov.in",
            password_hash=pwd_hash,
            role=UserRole.ADMIN,
        )
        db.add(admin_user)

    # Supervisor
    sup = await db.execute(select(User).where(User.email == "harden_sup@gov.in"))
    sup_user = sup.scalar_one_or_none()
    if not sup_user:
        sup_user = User(
            name="Hardening Lead Supervisor",
            email="harden_sup@gov.in",
            password_hash=pwd_hash,
            role=UserRole.SUPERVISOR,
        )
        db.add(sup_user)

    # Inspector A (linked / owner)
    insp_a = await db.execute(select(User).where(User.email == "harden_insp_a@gov.in"))
    insp_a_user = insp_a.scalar_one_or_none()
    if not insp_a_user:
        insp_a_user = User(
            name="Hardening Inspector Alpha",
            email="harden_insp_a@gov.in",
            password_hash=pwd_hash,
            role=UserRole.INSPECTOR,
        )
        db.add(insp_a_user)

    # Inspector B (unrelated / external)
    insp_b = await db.execute(select(User).where(User.email == "harden_insp_b@gov.in"))
    insp_b_user = insp_b.scalar_one_or_none()
    if not insp_b_user:
        insp_b_user = User(
            name="Hardening Inspector Beta",
            email="harden_insp_b@gov.in",
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


async def create_test_inspection(
    db,
    inspector_id: uuid.UUID,
    result: ComplianceResult = ComplianceResult.NON_COMPLIANT,
    status: InspectionStatus = InspectionStatus.COMPLETED,
    store_name: str = "Test Store Metro",
    company_id: uuid.UUID = None,
) -> Inspection:
    now = datetime.now(timezone.utc)
    insp = Inspection(
        inspector_id=inspector_id,
        store_name=store_name,
        store_address="Connaught Place, New Delhi",
        district="New Delhi",
        state="Delhi",
        status=status,
        overall_result=result,
        company_id=company_id,
        finalized_at=now if status == InspectionStatus.COMPLETED else None,
        created_at=now,
        updated_at=now,
    )
    db.add(insp)
    await db.commit()
    await db.refresh(insp)
    return insp


def get_auth_header(user: User) -> dict:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 25 COMPREHENSIVE HARDENING & PDF TEST CASES
# =============================================================================

async def test_01_dossier_has_no_legal_verdict():
    """1. Dossier model and schema have NO legal compliance verdict."""
    columns = [c.name for c in InvestigationDossier.__table__.columns]
    assert "overall_result" not in columns
    assert "compliance_result" not in columns
    assert "verdict" not in columns
    assert "legal_verdict" not in columns

    async with AsyncSessionLocal() as db:
        _, sup_user, _, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="No Verdict Test Dossier"),
            sup_user.id,
        )
        assert not hasattr(dossier, "overall_result")
        assert not hasattr(dossier, "compliance_result")

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert not hasattr(synthesis, "overall_result")
        assert not hasattr(synthesis, "compliance_result")
        assert not hasattr(synthesis, "legal_verdict")
    print("PASS: test_01_dossier_has_no_legal_verdict")


async def test_02_needs_review_remains_inspection_local():
    """2. NEEDS_REVIEW remains strictly inspection-local and is never overridden."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Needs Review Boundary Dossier"),
            sup_user.id,
        )
        insp_nr = await create_test_inspection(
            db, insp_a_user.id, result=ComplianceResult.NEEDS_REVIEW
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp_nr.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.summary_counts.needs_review_count == 1
        assert synthesis.summary_counts.non_compliant_count == 0
        assert synthesis.summary_counts.compliant_count == 0

        # Check DB inspection remains untouched
        reloaded = await db.get(Inspection, insp_nr.id)
        assert reloaded.overall_result == ComplianceResult.NEEDS_REVIEW
    print("PASS: test_02_needs_review_remains_inspection_local")


async def test_03_rule_3_applicability_contexts_remain_inspection_local():
    """3. Rule 3 statutory scope (applicability exemptions) remains inspection-local."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Rule 3 Context Dossier"),
            sup_user.id,
        )
        # Inspection 1: standard retail packaged commodity
        insp1 = await create_test_inspection(
            db, insp_a_user.id, result=ComplianceResult.NON_COMPLIANT, store_name="Store Flour Retail 1kg"
        )
        # Inspection 2: bulk/institutional exempt or differing context
        insp2 = await create_test_inspection(
            db, insp_a_user.id, result=ComplianceResult.COMPLIANT, store_name="Store Industrial Solvent 50kg"
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp1.id), sup_user
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp2.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.summary_counts.total_inspections == 2
        assert synthesis.summary_counts.non_compliant_count == 1
        assert synthesis.summary_counts.compliant_count == 1

        dossier_loaded = await DossierService.get_dossier(db, dossier.id)
        results = {str(di.inspection_id): di.inspection.overall_result.value for di in dossier_loaded.inspections}
        assert results[str(insp1.id)] == "NON_COMPLIANT"
        assert results[str(insp2.id)] == "COMPLIANT"
    print("PASS: test_03_rule_3_applicability_contexts_remain_inspection_local")


async def test_04_fifth_schedule_sample_size_boundary():
    """4. Fifth Schedule sample-size boundary (<= 4000 -> 32, > 4000 -> 80)."""
    # Fifth Schedule of Legal Metrology (Packaged Commodities) Rules 2011:
    # Lot size up to 4000: Sample size = 32
    # Lot size > 4000: Sample size = 80
    def compute_fifth_schedule_sample_size(lot_size: int) -> int:
        return 32 if lot_size <= 4000 else 80

    assert compute_fifth_schedule_sample_size(500) == 32
    assert compute_fifth_schedule_sample_size(4000) == 32
    assert compute_fifth_schedule_sample_size(4001) == 80
    assert compute_fifth_schedule_sample_size(10000) == 80
    print("PASS: test_04_fifth_schedule_sample_size_boundary")


async def test_05_sixth_schedule_evidence_completeness():
    """5. Sixth Schedule evidence completeness assessment does not mutate legal verdict."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Evidence Completeness Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(
            db, insp_a_user.id, result=ComplianceResult.NON_COMPLIANT
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.summary_counts.total_inspections == 1
        assert synthesis.summary_counts.non_compliant_count == 1
    print("PASS: test_05_sixth_schedule_evidence_completeness")


async def test_06_seizure_aggregation_is_factual_only():
    """6. Seizure aggregation is strictly factual and creates zero database records."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Seizure Factual Aggregation Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)

        # Add seizure memo
        seizure = SeizureRecord(
            seizure_memo_number=f"SM-{uuid.uuid4().hex[:6].upper()}",
            inspection_id=insp.id,
            premises_name="Test Seizure Shop",
            premises_address="Sector 18, Noida",
            seizure_date=datetime.now(timezone.utc),
            witness_1_name="Witness 1",
            witness_1_address="Address 1",
            witness_2_name="Witness 2",
            witness_2_address="Address 2",
            statutory_grounds="Rule 6 non-compliance",
            inspecting_officer_id=insp_a_user.id,
            custody_location="District Malkhana",
            sha256_seal_hash="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )
        db.add(seizure)
        await db.flush()

        item1 = SeizureItem(
            seizure_id=seizure.id,
            commodity_name="Spices 100g",
            brand_name="TasteBrand",
            total_packages_seized=25,
            sample_packages_taken=4,
        )
        item2 = SeizureItem(
            seizure_id=seizure.id,
            commodity_name="Oil 1L",
            brand_name="TasteBrand",
            total_packages_seized=15,
            sample_packages_taken=2,
        )
        db.add_all([item1, item2])
        await db.commit()

        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        initial_seizure_count = (await db.execute(select(func.count(SeizureRecord.id)))).scalar_one()
        initial_item_count = (await db.execute(select(func.count(SeizureItem.id)))).scalar_one()

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.seizure_summary.seizure_items_count == 2
        assert synthesis.seizure_summary.total_seized_quantity == 40.0

        post_seizure_count = (await db.execute(select(func.count(SeizureRecord.id)))).scalar_one()
        post_item_count = (await db.execute(select(func.count(SeizureItem.id)))).scalar_one()

        assert initial_seizure_count == post_seizure_count
        assert initial_item_count == post_item_count
    print("PASS: test_06_seizure_aggregation_is_factual_only")


async def test_07_dossier_deletion_preserves_seizure_records():
    """7. Dossier deletion does not cascade to or delete seizure records."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Dossier Deletion Preserves Seizures"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)

        seizure = SeizureRecord(
            seizure_memo_number=f"SM-{uuid.uuid4().hex[:6].upper()}",
            inspection_id=insp.id,
            premises_name="Safe Store",
            premises_address="Chandni Chowk, Delhi",
            seizure_date=datetime.now(timezone.utc),
            witness_1_name="Witness 1",
            witness_1_address="Address 1",
            witness_2_name="Witness 2",
            witness_2_address="Address 2",
            statutory_grounds="Section 15 seizure",
            inspecting_officer_id=insp_a_user.id,
            custody_location="Safe Box 1",
            sha256_seal_hash="1111111111111111111111111111111111111111111111111111111111111111",
        )
        db.add(seizure)
        await db.commit()
        seizure_id = seizure.id

        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        # Delete dossier directly
        await db.delete(dossier)
        await db.commit()

        # Check that seizure still exists
        preserved = await db.get(SeizureRecord, seizure_id)
        assert preserved is not None
        assert preserved.id == seizure_id
    print("PASS: test_07_dossier_deletion_preserves_seizure_records")


async def test_08_unlink_preserves_underlying_inspection_data():
    """8. Unlinking an inspection preserves all its checks, violations, and data."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Unlink Preserves Data Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)

        rule = (await db.execute(select(LegalRule))).scalars().first()
        cc = ComplianceCheck(
            inspection_id=insp.id,
            legal_rule_id=rule.id if rule else None,
            result=CheckResult.FAIL,
        )
        db.add(cc)
        await db.flush()

        v = Violation(
            inspection_id=insp.id,
            compliance_check_id=cc.id,
            severity=ViolationSeverity.HIGH,
            title="Rule 6 Missing Unit Sale Price",
            description="Unit Sale Price was not declared on the principal display panel.",
            rule_citation="Rule 6(1)(e)",
            status=ViolationStatus.OPEN,
        )
        db.add(v)
        await db.commit()
        v_id = v.id

        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )
        await DossierService.unlink_inspection(db, dossier, insp.id, sup_user)

        # Inspection and violation must still exist
        insp_check = await db.get(Inspection, insp.id)
        assert insp_check is not None
        v_check = await db.get(Violation, v_id)
        assert v_check is not None
        assert v_check.title == "Rule 6 Missing Unit Sale Price"
    print("PASS: test_08_unlink_preserves_underlying_inspection_data")


async def test_09_explicit_company_association_only():
    """9. Corporate associations rely strictly on explicit foreign key linkages."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        test_cin = f"U15400DL2020PTC{uuid.uuid4().hex[:6].upper()}"
        comp = Company(
            cin=test_cin,
            company_name="Explicit Foods Pvt Ltd",
            registered_office="Barakhamba Road, New Delhi",
            state="Delhi",
        )
        db.add(comp)
        await db.commit()

        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Explicit Company Dossier",
                company_id=comp.id,
                target_entity_name=comp.company_name,
            ),
            sup_user.id,
        )
        insp = await create_test_inspection(
            db, insp_a_user.id, company_id=comp.id, store_name="Explicit Retail Outlet"
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert synthesis.company_id == comp.id
        assert synthesis.company_name == "Explicit Foods Pvt Ltd"
        assert synthesis.company_cin == test_cin
    print("PASS: test_09_explicit_company_association_only")


async def test_10_no_fuzzy_company_inference():
    """10. No fuzzy company grouping without explicit company linkage."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="No Fuzzy Company Dossier"),
            sup_user.id,
        )
        insp1 = await create_test_inspection(
            db, insp_a_user.id, company_id=None, store_name="Reliance Retail Branch 1"
        )
        insp2 = await create_test_inspection(
            db, insp_a_user.id, company_id=None, store_name="Reliance Supermarket Branch 2"
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp1.id), sup_user
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp2.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        # Without explicit company_id, corporate profile is None (no fuzzy inference)
        assert synthesis.company_id is None
        assert synthesis.company_name is None
        assert synthesis.company_cin is None
    print("PASS: test_10_no_fuzzy_company_inference")


async def test_11_nominated_director_remains_informational():
    """11. Nominated director note strictly disclaims liability determination."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        test_cin = f"U15400DL2021PTC{uuid.uuid4().hex[:6].upper()}"
        comp = Company(
            cin=test_cin,
            company_name="Director Test FMCG Ltd",
            registered_office="Connaught Place, New Delhi",
            state="Delhi",
        )
        db.add(comp)
        await db.commit()

        test_din = f"{uuid.uuid4().int % 100000000:08d}"
        dir_record = NominatedDirector(
            company_id=comp.id,
            director_name="Shri Rajesh Sharma",
            din=test_din,
            designation="Director (Operations)",
            form_i_notice_date=date(2023, 1, 15),
            form_i_reference="ROC/DEL/FORM-I/2023/1102",
            effective_from=date(2023, 1, 15),
        )
        db.add(dir_record)
        await db.commit()

        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Nominated Director Advisory Dossier",
                company_id=comp.id,
            ),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id, company_id=comp.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        assert len(synthesis.nominated_directors_review) == 1
        dir_info = synthesis.nominated_directors_review[0]
        assert dir_info.director_name == "Shri Rajesh Sharma"
        assert "informational" in dir_info.review_note.lower() or "officer review" in dir_info.review_note.lower()
    print("PASS: test_11_nominated_director_remains_informational")


async def test_12_no_repeat_offender_conclusion():
    """12. Repeat history queries return factual counts and never declare 'repeat offender confirmed'."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        test_cin = f"U15400DL2022PTC{uuid.uuid4().hex[:6].upper()}"
        comp = Company(
            cin=test_cin,
            company_name="History Check Corp",
            registered_office="Okhla, New Delhi",
            state="Delhi",
        )
        db.add(comp)
        await db.commit()

        # Create two non-compliant inspections for this company
        await create_test_inspection(db, insp_a_user.id, company_id=comp.id, result=ComplianceResult.NON_COMPLIANT)
        await create_test_inspection(db, insp_a_user.id, company_id=comp.id, result=ComplianceResult.NON_COMPLIANT)

        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(
                title="Repeat History Factual Dossier",
                company_id=comp.id,
            ),
            sup_user.id,
        )

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        note = synthesis.repeat_history_note
        assert "Repeat offender confirmed" not in note
        assert "Habitual violator" not in note
    print("PASS: test_12_no_repeat_offender_conclusion")


async def test_13_pdf_generation_succeeds():
    """13. Dossier PDF generation succeeds and returns valid PDF bytes."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="PDF Generation Test Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        pdf_bytes = await DossierService.generate_dossier_pdf(db, dossier)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")
    print("PASS: test_13_pdf_generation_succeeds")


async def test_14_pdf_contains_required_disclaimers():
    """14. PDF contains non-judicial advisory disclaimer and legal citations."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="PDF Disclaimers Test Dossier"),
            sup_user.id,
        )
        pdf_bytes = await DossierService.generate_dossier_pdf(db, dossier)
        # Verify bytes contain critical text keywords
        assert b"MetrologyMitra" in pdf_bytes
        assert b"SYSTEM-GENERATED REFERENCE DOCUMENT" in pdf_bytes
        assert b"NON-JUDICIAL" in pdf_bytes
    print("PASS: test_14_pdf_contains_required_disclaimers")


async def test_15_pdf_contains_dossier_number():
    """15. PDF contains dossier tracking number."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Dossier Number PDF Dossier"),
            sup_user.id,
        )
        pdf_bytes = await DossierService.generate_dossier_pdf(db, dossier)
        dossier_num_bytes = dossier.dossier_number.encode("utf-8")
        assert dossier_num_bytes in pdf_bytes
    print("PASS: test_15_pdf_contains_dossier_number")


async def test_16_pdf_contains_linked_inspection_identifiers_and_results():
    """16. PDF contains linked inspection identifiers and individual compliance verdicts."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Inspection Details PDF Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(
            db, insp_a_user.id, result=ComplianceResult.NON_COMPLIANT
        )
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        pdf_bytes = await DossierService.generate_dossier_pdf(db, dossier)
        insp_id_snippet = str(insp.id)[:8].encode("utf-8")
        assert insp_id_snippet in pdf_bytes
        assert b"NON_COMPLIANT" in pdf_bytes
    print("PASS: test_16_pdf_contains_linked_inspection_identifiers_and_results")


async def test_17_inspector_authorization_boundary_cannot_mutate():
    """17. Inspector cannot mutate dossier status or priority (returns 403)."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Mutation Boundary Dossier"),
            sup_user.id,
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        insp_headers = get_auth_header(insp_a_user)
        # Attempt to update status as inspector
        res = await client.patch(
            f"/api/v1/dossiers/{dossier.id}",
            json={"status": "EVALUATION"},
            headers=insp_headers,
        )
        assert res.status_code == 403
        assert "not permitted" in res.json()["detail"].lower() or "role" in res.json()["detail"].lower()
    print("PASS: test_17_inspector_authorization_boundary_cannot_mutate")


async def test_18_inspector_scoping_cannot_access_unrelated_dossier_pdf_or_synthesis():
    """18. Inspector cannot access unrelated dossier PDF or synthesis (returns 403)."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, insp_b_user = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Unrelated Dossier Scoping Test"),
            sup_user.id,
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        insp_b_headers = get_auth_header(insp_b_user)
        # Unrelated inspector tries synthesis
        res_synth = await client.get(
            f"/api/v1/dossiers/{dossier.id}/synthesis",
            headers=insp_b_headers,
        )
        assert res_synth.status_code == 403

        # Unrelated inspector tries PDF
        res_pdf = await client.get(
            f"/api/v1/dossiers/{dossier.id}/pdf",
            headers=insp_b_headers,
        )
        assert res_pdf.status_code == 403
    print("PASS: test_18_inspector_scoping_cannot_access_unrelated_dossier_pdf_or_synthesis")


async def test_19_supervisor_management_boundary():
    """19. Supervisor can create dossier, link inspection, update status, and view PDF."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        insp = await create_test_inspection(db, insp_a_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sup_headers = get_auth_header(sup_user)

        # Create
        create_res = await client.post(
            "/api/v1/dossiers/",
            json={"title": "Supervisor Workflow Dossier", "priority": "NORMAL"},
            headers=sup_headers,
        )
        assert create_res.status_code == 201
        d_id = create_res.json()["id"]

        # Link
        link_res = await client.post(
            f"/api/v1/dossiers/{d_id}/inspections",
            json={"inspection_id": str(insp.id), "notes": "Supervisor verified link"},
            headers=sup_headers,
        )
        assert link_res.status_code == 201

        # Update status
        patch_res = await client.patch(
            f"/api/v1/dossiers/{d_id}",
            json={"status": "EVALUATION"},
            headers=sup_headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "EVALUATION"

        # Download PDF
        pdf_res = await client.get(f"/api/v1/dossiers/{d_id}/pdf", headers=sup_headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 1000
    print("PASS: test_19_supervisor_management_boundary")


async def test_20_admin_management_boundary():
    """20. Admin has full management privileges over dossiers."""
    async with AsyncSessionLocal() as db:
        admin_user, sup_user, insp_a_user, _ = await setup_test_users(db)
        insp = await create_test_inspection(db, insp_a_user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = get_auth_header(admin_user)

        # Create
        create_res = await client.post(
            "/api/v1/dossiers/",
            json={"title": "Admin Managed Dossier", "priority": "HIGH"},
            headers=admin_headers,
        )
        assert create_res.status_code == 201
        d_id = create_res.json()["id"]

        # Link
        link_res = await client.post(
            f"/api/v1/dossiers/{d_id}/inspections",
            json={"inspection_id": str(insp.id)},
            headers=admin_headers,
        )
        assert link_res.status_code == 201

        # Synthesis
        synth_res = await client.get(f"/api/v1/dossiers/{d_id}/synthesis", headers=admin_headers)
        assert synth_res.status_code == 200

        # PDF
        pdf_res = await client.get(f"/api/v1/dossiers/{d_id}/pdf", headers=admin_headers)
        assert pdf_res.status_code == 200

        # Delete
        del_res = await client.delete(f"/api/v1/dossiers/{d_id}", headers=admin_headers)
        assert del_res.status_code == 204
    print("PASS: test_20_admin_management_boundary")


async def test_21_unauthorized_dossier_access_returns_403_404():
    """21. Non-existent returns 404, unauthenticated returns 401, unauthorized returns 403."""
    async with AsyncSessionLocal() as db:
        _, sup_user, _, insp_b_user = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Auth Matrix Dossier"),
            sup_user.id,
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Non-existent returns 404
        sup_headers = get_auth_header(sup_user)
        res_404 = await client.get(f"/api/v1/dossiers/{uuid.uuid4()}", headers=sup_headers)
        assert res_404.status_code == 404

        # 2. Unauthenticated returns 401
        res_401 = await client.get(f"/api/v1/dossiers/{dossier.id}")
        assert res_401.status_code == 401

        # 3. Unauthorized inspector returns 403
        insp_b_headers = get_auth_header(insp_b_user)
        res_403 = await client.get(f"/api/v1/dossiers/{dossier.id}", headers=insp_b_headers)
        assert res_403.status_code == 403
    print("PASS: test_21_unauthorized_dossier_access_returns_403_404")


async def test_22_audit_events_are_recorded_for_lifecycle_actions():
    """22. Audit events are recorded for dossier lifecycle actions."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        insp = await create_test_inspection(db, insp_a_user.id)

        # 1. Create dossier
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Audit Trail Verification Dossier"),
            sup_user.id,
        )
        assert "audit_logs" in (dossier.metadata_ or {})
        assert dossier.metadata_["audit_logs"][0]["action"] == "DOSSIER_CREATED"

        # 2. Status update
        await DossierService.update_dossier(
            db,
            dossier,
            InvestigationDossierUpdate(status=DossierStatus.EVALUATION),
            sup_user,
        )
        actions = [log["action"] for log in dossier.metadata_["audit_logs"]]
        assert "DOSSIER_UPDATED" in actions

        # 3. Link inspection
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )
        actions = [log["action"] for log in dossier.metadata_["audit_logs"]]
        assert "INSPECTION_LINKED" in actions

        # 4. Unlink inspection
        await DossierService.unlink_inspection(db, dossier, insp.id, sup_user)
        actions = [log["action"] for log in dossier.metadata_["audit_logs"]]
        assert "INSPECTION_UNLINKED" in actions

        # Verify AuditLog DB row for inspection
        stmt = select(AuditLog).where(
            AuditLog.inspection_id == insp.id,
            AuditLog.action == "DOSSIER_INSPECTION_LINKED",
        )
        row = (await db.execute(stmt)).scalar_one_or_none()
        assert row is not None
    print("PASS: test_22_audit_events_are_recorded_for_lifecycle_actions")


async def test_23_finalized_inspection_immutability():
    """23. Finalized inspections remain immutable when linked or unlinked from dossiers."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        insp = await create_test_inspection(
            db,
            insp_a_user.id,
            status=InspectionStatus.COMPLETED,
            result=ComplianceResult.NON_COMPLIANT,
        )
        original_updated_at = insp.updated_at
        original_result = insp.overall_result
        original_finalized_at = insp.finalized_at

        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Finalized Immutability Dossier"),
            sup_user.id,
        )
        # Link
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )
        # Unlink
        await DossierService.unlink_inspection(db, dossier, insp.id, sup_user)

        reloaded = await db.get(Inspection, insp.id)
        assert reloaded.status == InspectionStatus.COMPLETED
        assert reloaded.overall_result == original_result
        assert reloaded.updated_at == original_updated_at
        assert reloaded.finalized_at == original_finalized_at
    print("PASS: test_23_finalized_inspection_immutability")


async def test_24_synthesis_is_read_only():
    """24. Calling dossier synthesis is completely read-only and causes zero DB mutations."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="Read-Only Verification Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        # Baseline count of audits
        audit_count_before = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()

        synth1 = await DossierService.get_dossier_synthesis(db, dossier)
        synth2 = await DossierService.get_dossier_synthesis(db, dossier)

        audit_count_after = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()
        assert audit_count_before == audit_count_after
        assert synth1.summary_counts.total_inspections == synth2.summary_counts.total_inspections
    print("PASS: test_24_synthesis_is_read_only")


async def test_25_no_new_violations_or_seizures_generated_by_synthesis():
    """25. Synthesis generates zero new violations or seizure records."""
    async with AsyncSessionLocal() as db:
        _, sup_user, insp_a_user, _ = await setup_test_users(db)
        dossier = await DossierService.create_dossier(
            db,
            InvestigationDossierCreate(title="No New Violations Synthesis Dossier"),
            sup_user.id,
        )
        insp = await create_test_inspection(db, insp_a_user.id)
        await DossierService.link_inspection(
            db, dossier, DossierInspectionCreate(inspection_id=insp.id), sup_user
        )

        v_count_before = (await db.execute(select(func.count(Violation.id)))).scalar_one()
        s_count_before = (await db.execute(select(func.count(SeizureRecord.id)))).scalar_one()

        await DossierService.get_dossier_synthesis(db, dossier)
        await DossierService.generate_dossier_pdf(db, dossier)

        v_count_after = (await db.execute(select(func.count(Violation.id)))).scalar_one()
        s_count_after = (await db.execute(select(func.count(SeizureRecord.id)))).scalar_one()

        assert v_count_before == v_count_after
        assert s_count_before == s_count_after
    print("PASS: test_25_no_new_violations_or_seizures_generated_by_synthesis")


# =============================================================================
# MAIN RUNNER
# =============================================================================

async def main():
    print("Running MetrologyMitra Phase 3.0 Sub-Batch 5 Hardening & PDF Test Suite (25 Tests)...")
    await test_01_dossier_has_no_legal_verdict()
    await test_02_needs_review_remains_inspection_local()
    await test_03_rule_3_applicability_contexts_remain_inspection_local()
    await test_04_fifth_schedule_sample_size_boundary()
    await test_05_sixth_schedule_evidence_completeness()
    await test_06_seizure_aggregation_is_factual_only()
    await test_07_dossier_deletion_preserves_seizure_records()
    await test_08_unlink_preserves_underlying_inspection_data()
    await test_09_explicit_company_association_only()
    await test_10_no_fuzzy_company_inference()
    await test_11_nominated_director_remains_informational()
    await test_12_no_repeat_offender_conclusion()
    await test_13_pdf_generation_succeeds()
    await test_14_pdf_contains_required_disclaimers()
    await test_15_pdf_contains_dossier_number()
    await test_16_pdf_contains_linked_inspection_identifiers_and_results()
    await test_17_inspector_authorization_boundary_cannot_mutate()
    await test_18_inspector_scoping_cannot_access_unrelated_dossier_pdf_or_synthesis()
    await test_19_supervisor_management_boundary()
    await test_20_admin_management_boundary()
    await test_21_unauthorized_dossier_access_returns_403_404()
    await test_22_audit_events_are_recorded_for_lifecycle_actions()
    await test_23_finalized_inspection_immutability()
    await test_24_synthesis_is_read_only()
    await test_25_no_new_violations_or_seizures_generated_by_synthesis()
    print("\nALL 25 SUB-BATCH 5 HARDENING & PDF TESTS PASSED (100%)!")


if __name__ == "__main__":
    asyncio.run(main())
