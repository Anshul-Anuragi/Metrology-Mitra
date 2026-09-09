"""
MetrologyMitra — Inspector Dashboard Completed/Compliant Test Suite
===================================================================
Verifies data integrity, lifecycle vs statutory verdict dimensional separation,
RBAC query scoping, demo seed auto-finalization of compliant presets,
and statutory_verdict serialization on the Inspector Dashboard.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.enums import (
    CheckResult,
    ComplianceResult,
    InspectionStatus,
    UserRole,
)
from app.core.security import create_access_token, get_password_hash
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.user import User
from app.services.rule_engine import evaluate_inspection


async def get_or_create_user(db, email: str, name: str, role: UserRole) -> User:
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=get_password_hash("AuditSecret123!"),
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def setup_test_environment(db):
    insp_a = await get_or_create_user(db, "dash_insp_a@gov.in", "Dashboard Inspector A", UserRole.INSPECTOR)
    insp_b = await get_or_create_user(db, "dash_insp_b@gov.in", "Dashboard Inspector B", UserRole.INSPECTOR)
    sup = await get_or_create_user(db, "dash_sup@gov.in", "Dashboard Supervisor", UserRole.SUPERVISOR)
    return insp_a, insp_b, sup


# =============================================================================
# TEST CASES
# =============================================================================

async def test_01_completed_compliant_inspection_persistence():
    """1. An inspection evaluated compliant by rule engine and finalized has status=COMPLETED and overall_result=COMPLIANT in DB."""
    async with AsyncSessionLocal() as db:
        insp_a, _, _ = await setup_test_environment(db)

        # Create inspection
        insp = Inspection(
            inspector_id=insp_a.id,
            store_name="Organic Supermarket Connaught Place",
            store_address="Block B, CP, New Delhi",
            district="New Delhi",
            state="Delhi",
            status=InspectionStatus.REVIEW_REQUIRED,
            started_at=datetime.now(timezone.utc),
        )
        db.add(insp)
        await db.flush()

        # Fully compliant declaration
        decl = Declaration(
            inspection_id=insp.id,
            commodity_name="Organic Whole Wheat Flour",
            manufacturer_name="Natural Harvest Mills Ltd",
            address="Plot 5, Industrial Area, Noida 201301",
            net_quantity="5 kg",
            mrp="MRP Rs. 295.00 incl. of all taxes",
            unit_sale_price="Rs. 59.00/kg",
            manufacturing_date="08/2026",
            expiry_date="02/2027",
            best_before="Best before 6 months from packaging",
            consumer_care="1800-111-222, support@naturalharvest.in",
            country_of_origin="India",
            is_imported=False,
            pdp_area_sq_cm=350.0,
            is_human_verified=True,
        )
        db.add(decl)
        await db.flush()

        # Deterministic rule engine evaluation
        eval_res = await evaluate_inspection(db, insp, decl)
        assert insp.overall_result == ComplianceResult.COMPLIANT, f"Expected COMPLIANT, got {insp.overall_result}"

        # Finalize inspection
        insp.status = InspectionStatus.COMPLETED
        insp.completed_at = datetime.now(timezone.utc)
        insp.finalized_by_id = insp_a.id
        insp.finalized_at = datetime.now(timezone.utc)
        insp.review_notes = "[Audit Verification]: All 18 statutory declarations verified compliant."
        await db.commit()
        await db.refresh(insp)

        assert insp.status == InspectionStatus.COMPLETED
        assert insp.overall_result == ComplianceResult.COMPLIANT
        assert insp.finalized_at is not None

    print("PASS: test_01_completed_compliant_inspection_persistence")


async def test_02_dashboard_list_filters_completed_compliant_records():
    """2. Dashboard API list returns completed compliant records when filtered by status=COMPLETED and result=COMPLIANT."""
    async with AsyncSessionLocal() as db:
        insp_a, _, _ = await setup_test_environment(db)

    token = create_access_token(insp_a.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/inspections/?status_filter=COMPLETED&result_filter=COMPLIANT",
            headers=headers,
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Expected at least 1 completed compliant record"

        for row in data:
            assert row["status"] == "COMPLETED"
            assert row["overall_result"] == "COMPLIANT"
            # Verify computed field statutory_verdict
            assert row["statutory_verdict"] == "COMPLIANT"

    print("PASS: test_02_dashboard_list_filters_completed_compliant_records")


async def test_03_separation_of_lifecycle_and_verdict_dimensions():
    """3. Verify dimensional orthogonality: COMPLETED != COMPLIANT and COMPLIANT != COMPLETED."""
    async with AsyncSessionLocal() as db:
        insp_a, _, _ = await setup_test_environment(db)

        # Create record A: COMPLETED but NON_COMPLIANT
        insp_non_comp = Inspection(
            inspector_id=insp_a.id,
            store_name="Defective Goods Retail",
            store_address="Sector 18, Noida",
            district="Gautam Buddha Nagar",
            state="Uttar Pradesh",
            status=InspectionStatus.COMPLETED,
            overall_result=ComplianceResult.NON_COMPLIANT,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            finalized_by_id=insp_a.id,
            finalized_at=datetime.now(timezone.utc),
        )
        # Create record B: REVIEW_REQUIRED but COMPLIANT (pending officer signoff)
        insp_in_review = Inspection(
            inspector_id=insp_a.id,
            store_name="Pending Review Compliant Mart",
            store_address="Sector 62, Noida",
            district="Gautam Buddha Nagar",
            state="Uttar Pradesh",
            status=InspectionStatus.REVIEW_REQUIRED,
            overall_result=ComplianceResult.COMPLIANT,
            started_at=datetime.now(timezone.utc),
        )
        db.add_all([insp_non_comp, insp_in_review])
        await db.commit()

    token = create_access_token(insp_a.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Query COMPLETED only -> should contain both COMPLIANT and NON_COMPLIANT
        res_completed = await client.get("/api/v1/inspections/?status_filter=COMPLETED", headers=headers)
        assert res_completed.status_code == 200
        completed_data = res_completed.json()
        results_in_completed = {r["overall_result"] for r in completed_data}
        assert "NON_COMPLIANT" in results_in_completed
        assert "COMPLIANT" in results_in_completed

        # Query COMPLIANT only -> should contain both COMPLETED and REVIEW_REQUIRED
        res_compliant = await client.get("/api/v1/inspections/?result_filter=COMPLIANT", headers=headers)
        assert res_compliant.status_code == 200
        compliant_data = res_compliant.json()
        statuses_in_compliant = {r["status"] for r in compliant_data}
        assert "COMPLETED" in statuses_in_compliant
        assert "REVIEW_REQUIRED" in statuses_in_compliant

    print("PASS: test_03_separation_of_lifecycle_and_verdict_dimensions")


async def test_04_rbac_scoping_of_inspector_dashboard():
    """4. Inspector A cannot see Inspector B's inspections, but Supervisor sees all."""
    async with AsyncSessionLocal() as db:
        insp_a, insp_b, sup = await setup_test_environment(db)

        # Inspector B creates a private completed compliant inspection
        insp_b_record = Inspection(
            inspector_id=insp_b.id,
            store_name="Inspector B Private Store",
            store_address="Connaught Place, B-Block",
            district="New Delhi",
            state="Delhi",
            status=InspectionStatus.COMPLETED,
            overall_result=ComplianceResult.COMPLIANT,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            finalized_by_id=insp_b.id,
            finalized_at=datetime.now(timezone.utc),
        )
        db.add(insp_b_record)
        await db.commit()
        await db.refresh(insp_b_record)
        b_id = str(insp_b_record.id)

    token_a = create_access_token(insp_a.id)
    token_b = create_access_token(insp_b.id)
    token_sup = create_access_token(sup.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Inspector A list query
        res_a = await client.get("/api/v1/inspections/", headers={"Authorization": f"Bearer {token_a}"})
        ids_a = {r["id"] for r in res_a.json()}
        assert b_id not in ids_a, "Inspector A should NOT see Inspector B's inspection"

        # Inspector B list query
        res_b = await client.get("/api/v1/inspections/", headers={"Authorization": f"Bearer {token_b}"})
        ids_b = {r["id"] for r in res_b.json()}
        assert b_id in ids_b, "Inspector B SHOULD see their own inspection"

        # Supervisor list query
        res_sup = await client.get("/api/v1/inspections/", headers={"Authorization": f"Bearer {token_sup}"})
        ids_sup = {r["id"] for r in res_sup.json()}
        assert b_id in ids_sup, "Supervisor SHOULD see inspections from all inspectors"

    print("PASS: test_04_rbac_scoping_of_inspector_dashboard")


async def test_05_demo_seed_endpoint_finalizes_compliant_preset():
    """5. /demo-seed properly seeds Preset 1 as COMPLETED + COMPLIANT under current inspector."""
    async with AsyncSessionLocal() as db:
        # Create a fresh inspector specifically for demo seed verification
        demo_insp = await get_or_create_user(db, "demo_seed_audit_user@gov.in", "Demo Seed Officer", UserRole.INSPECTOR)

    token = create_access_token(demo_insp.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. First seed call -> seeds 7 presets
        res_seed = await client.post("/api/v1/inspections/demo-seed", headers=headers)
        assert res_seed.status_code == 201, res_seed.text
        seed_data = res_seed.json()
        assert seed_data["status"] == "SUCCESS"

        # 2. Query COMPLETED & COMPLIANT
        res_list = await client.get(
            "/api/v1/inspections/?status_filter=COMPLETED&result_filter=COMPLIANT",
            headers=headers,
        )
        assert res_list.status_code == 200
        comp_items = res_list.json()
        assert len(comp_items) >= 1, "Freshly seeded demo inspector must have at least 1 completed compliant record"

        # Preset 1 must be among them
        preset_1_matches = [
            i for i in comp_items
            if "Tata Sampann Toor Dal" in (i.get("store_name") or "")
        ]
        assert len(preset_1_matches) == 1, "Preset 1 Tata Sampann Toor Dal must be present and completed compliant"
        p1 = preset_1_matches[0]
        assert p1["status"] == "COMPLETED"
        assert p1["overall_result"] == "COMPLIANT"
        assert p1["statutory_verdict"] == "COMPLIANT"

        # 3. Second seed call -> Idempotent, 0 new
        res_seed2 = await client.post("/api/v1/inspections/demo-seed", headers=headers)
        assert res_seed2.status_code == 201
        assert "Successfully seeded 0" in res_seed2.json()["message"]

    print("PASS: test_05_demo_seed_endpoint_finalizes_compliant_preset")


async def test_06_serialization_contract_includes_statutory_verdict():
    """6. InspectionResponse schema contains both overall_result and statutory_verdict."""
    async with AsyncSessionLocal() as db:
        insp_a, _, _ = await setup_test_environment(db)

    token = create_access_token(insp_a.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/inspections/?limit=5", headers=headers)
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        for item in items:
            assert "overall_result" in item
            assert "statutory_verdict" in item
            assert item["statutory_verdict"] == item["overall_result"]

    print("PASS: test_06_serialization_contract_includes_statutory_verdict")


async def test_07_empty_filter_state_graceful_handling():
    """7. An unmatched filter combination returns empty list [] with HTTP 200."""
    async with AsyncSessionLocal() as db:
        # Create isolated user with no records
        isolated = await get_or_create_user(db, "isolated_empty_user@gov.in", "Empty User", UserRole.INSPECTOR)

    token = create_access_token(isolated.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/inspections/?status_filter=COMPLETED&result_filter=COMPLIANT",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data == [], f"Expected empty list, got: {data}"

    print("PASS: test_07_empty_filter_state_graceful_handling")


# =============================================================================
# MAIN RUNNER
# =============================================================================

async def main():
    print("=" * 80)
    print("METROLOGYMITRA — INSPECTOR DASHBOARD COMPLETED/COMPLIANT TEST SUITE")
    print("=" * 80)
    await test_01_completed_compliant_inspection_persistence()
    await test_02_dashboard_list_filters_completed_compliant_records()
    await test_03_separation_of_lifecycle_and_verdict_dimensions()
    await test_04_rbac_scoping_of_inspector_dashboard()
    await test_05_demo_seed_endpoint_finalizes_compliant_preset()
    await test_06_serialization_contract_includes_statutory_verdict()
    await test_07_empty_filter_state_graceful_handling()
    print("=" * 80)
    print("ALL 7 INSPECTOR DASHBOARD TESTS PASSED (100%)!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

