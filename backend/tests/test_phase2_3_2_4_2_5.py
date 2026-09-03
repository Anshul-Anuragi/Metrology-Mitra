import asyncio
import io
import uuid
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.enums import CheckResult, ComplianceResult, InspectionStatus, UserRole
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.declaration import Declaration
from app.models.gravimetric_test import GravimetricTest
from app.models.inspection import Inspection
from app.models.legal_rule import LegalRule
from app.models.user import User
from app.services.exemption_service import evaluate_statutory_exemption
from app.services.gravimetric_service import (
    build_gravimetric_test_pdf,
    evaluate_gravimetric_samples,
    get_statutory_mpe,
)
from app.services.provenance_service import compute_inspection_provenance_hash, verify_geocoordinates
from app.services.rule_engine import _eval_mrp, _eval_usp, evaluate_inspection


async def test_phase_2_3_gravimetric_mpe_engine():
    """
    Phase 2.3 Test: Tests Schedule IV Table 2 MPE lookup, multi-sample statistical
    aggregation, double-MPE critical defects, mean deficit detection, and PDF generation.
    """
    print("\nRunning test_phase_2_3_gravimetric_mpe_engine...")

    # 1. Test Schedule IV Table 2 MPE Tiers
    # Tier 1: <= 50g -> 9%
    mpe_50g, desc_50g = get_statutory_mpe(50.0, "g")
    assert mpe_50g == 4.5  # 50 * 0.09 = 4.5g

    # Tier 2: 50g < Qn <= 100g -> 4.5g fixed
    mpe_100g, _ = get_statutory_mpe(100.0, "g")
    assert mpe_100g == 4.5

    # Tier 3: 100g < Qn <= 200g -> 4.5%
    mpe_200g, _ = get_statutory_mpe(200.0, "g")
    assert mpe_200g == 9.0  # 200 * 0.045 = 9.0g

    # Tier 5: 300g < Qn <= 500g -> 3%
    mpe_500g, _ = get_statutory_mpe(500.0, "g")
    assert mpe_500g == 15.0  # 500 * 0.03 = 15.0g

    # Tier 7: 1kg < Qn <= 10kg -> 1.5%
    mpe_1kg, _ = get_statutory_mpe(1.0, "kg")
    assert mpe_1kg == 0.015  # 1kg * 0.015 = 0.015kg (15g)

    # 2. Test Passing Gravimetric Evaluation (mean >= Qn, 0 defectives)
    passing_samples = [
        {"unit_number": 1, "gross_weight": 515.0, "tare_weight": 10.0},  # net 505
        {"unit_number": 2, "gross_weight": 512.0, "tare_weight": 10.0},  # net 502
        {"unit_number": 3, "gross_weight": 511.0, "tare_weight": 10.0},  # net 501
    ]
    res_pass = evaluate_gravimetric_samples(500.0, "g", passing_samples)
    assert res_pass["lot_decision"] == "PASSED_MPE"
    assert res_pass["sample_mean_net_quantity"] == 502.6667
    assert res_pass["defective_units_count"] == 0
    assert res_pass["double_mpe_defective_count"] == 0

    # 3. Test Mean Deficit Rejection (mean < Qn)
    deficit_samples = [
        {"unit_number": 1, "gross_weight": 505.0, "tare_weight": 10.0},  # net 495
        {"unit_number": 2, "gross_weight": 504.0, "tare_weight": 10.0},  # net 494
        {"unit_number": 3, "gross_weight": 506.0, "tare_weight": 10.0},  # net 496
    ]
    res_deficit = evaluate_gravimetric_samples(500.0, "g", deficit_samples)
    assert res_deficit["lot_decision"] == "FAILED_MEAN_DEFICIT"
    assert res_deficit["sample_mean_net_quantity"] < 500.0

    # 4. Test Critical Double-MPE Rejection (any single unit deficit > 2 * MPE -> immediate FAIL)
    # For 500g, MPE = 15g, Double MPE = 30g. Net weight 460g has deficit 40g > 30g
    critical_samples = [
        {"unit_number": 1, "gross_weight": 520.0, "tare_weight": 10.0},  # net 510
        {"unit_number": 2, "gross_weight": 470.0, "tare_weight": 10.0},  # net 460 (deficit 40g > 30g)
        {"unit_number": 3, "gross_weight": 550.0, "tare_weight": 10.0},  # net 540 (mean is still > 500)
    ]
    res_crit = evaluate_gravimetric_samples(500.0, "g", critical_samples)
    assert res_crit["lot_decision"] == "FAILED_CRITICAL_DOUBLE_MPE"
    assert res_crit["double_mpe_defective_count"] == 1

    # 5. Test API Endpoints
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_res = await client.post("/api/v1/auth/login", json={"email": "sharma@doca.gov.in", "password": "password123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create Gravimetric Test
        payload = {
            "nominal_quantity_value": 500.0,
            "nominal_quantity_unit": "g",
            "declared_tare_weight": 10.0,
            "samples": [
                {"unit_number": 1, "gross_weight": 512.0, "tare_weight": 10.0},
                {"unit_number": 2, "gross_weight": 514.0, "tare_weight": 10.0},
            ],
            "lot_size": 100,
        }
        create_res = await client.post("/api/v1/gravimetric/tests", json=payload, headers=headers)
        assert create_res.status_code == 201, create_res.text
        test_data = create_res.json()
        assert test_data["lot_decision"] == "PASSED_MPE"
        test_id = test_data["id"]

        # Get Gravimetric Test Detail
        get_res = await client.get(f"/api/v1/gravimetric/tests/{test_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["mpe_value"] == 15.0

        # Download Test Report PDF
        pdf_res = await client.get(f"/api/v1/gravimetric/tests/{test_id}/pdf", headers=headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 1000

    print("PASS: test_phase_2_3_gravimetric_mpe_engine")


async def test_phase_2_4_statutory_exemptions_and_special_packages():
    """
    Phase 2.4 Test: Tests Rule 26 statutory exemptions (<= 10g small packs, > 50kg bulk, institutional)
    and special packaging provisions (Rules 21 & 22), verifying rule engine integration.
    """
    print("\nRunning test_phase_2_4_statutory_exemptions_and_special_packages...")

    # 1. Small Package Exemption (<= 10g) under Rule 26(a)
    ex_small = evaluate_statutory_exemption(
        package_type="SMALL_PACK",
        net_quantity_value=8.0,
        net_quantity_unit="g",
    )
    assert ex_small.is_exempt is True
    assert ex_small.exemption_rule == "Rule 26(a)"
    assert "mrp" in ex_small.exempt_mandatory_declarations
    assert "unit_sale_price" in ex_small.exempt_mandatory_declarations

    # 2. Institutional Consumer Exemption under Rule 26(c) & Rule 2(p)
    ex_inst = evaluate_statutory_exemption(
        package_type="INSTITUTIONAL",
        is_institutional_consumer=True,
    )
    assert ex_inst.is_exempt is True
    assert "Rule 26(c)" in ex_inst.exemption_rule
    assert "mrp" in ex_inst.exempt_mandatory_declarations

    # 3. Multi-Piece Package under Rule 21
    ex_multi = evaluate_statutory_exemption(
        package_type="MULTI_PIECE",
        multi_piece_count=4,
    )
    assert ex_multi.is_exempt is False
    assert "Rule 21 (Multi-Piece Packages)" in ex_multi.applicable_special_rules

    # 4. Rule Engine Exemption Integration Check
    # A small package declaration with missing MRP must PASS (not FAIL or REVIEW)
    mock_rule_mrp = LegalRule(rule_code="LMPC-R6-MRP", title="Maximum Retail Price", rule_type="MANDATORY")
    mock_decl_small = Declaration(
        package_type="SMALL_PACK",
        exemption_applied="Rule 26(a)",
        net_quantity="8 g",
        mrp=None,  # No MRP
    )
    res_mrp, val, conf, reason = _eval_mrp(mock_decl_small, mock_rule_mrp)
    assert res_mrp == CheckResult.PASS
    assert "Exempt" in reason

    # An institutional package declaration with missing USP must PASS
    mock_rule_usp = LegalRule(rule_code="LMPC-R6-USP", title="Unit Sale Price", rule_type="MANDATORY")
    mock_decl_inst = Declaration(
        package_type="INSTITUTIONAL",
        exemption_applied="Rule 26(c)",
        unit_sale_price=None,
    )
    res_usp, val_u, conf_u, reason_u = _eval_usp(mock_decl_inst, mock_rule_usp)
    assert res_usp == CheckResult.PASS
    assert "Exempt" in reason_u

    # 5. Test API Endpoints
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": "sharma@doca.gov.in", "password": "password123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Evaluate Exemption API
        eval_res = await client.post("/api/v1/exemptions/evaluate", json={
            "package_type": "SMALL_PACK",
            "declared_net_quantity_value": 5.0,
            "declared_net_quantity_unit": "g",
        }, headers=headers)
        assert eval_res.status_code == 200
        assert eval_res.json()["is_exempt"] is True

        # Apply Exemption to an Inspection
        insp_res = await client.post("/api/v1/inspections/", json={
            "store_name": "Metro Cash & Carry", "state": "Delhi", "district": "New Delhi"
        }, headers=headers)
        insp_id = insp_res.json()["id"]

        apply_res = await client.post(f"/api/v1/exemptions/apply/{insp_id}", json={
            "package_type": "INSTITUTIONAL",
            "is_institutional_consumer": True,
        }, headers=headers)
        assert apply_res.status_code == 200
        assert apply_res.json()["package_type"] == "INSTITUTIONAL"

    print("PASS: test_phase_2_4_statutory_exemptions_and_special_packages")


async def test_phase_2_5_geofence_and_offline_synchronization():
    """
    Phase 2.5 Test: Tests GPS geofence boundary validation, offline inspection
    batch ingestion, and SHA-256 provenance hash generation.
    """
    print("\nRunning test_phase_2_5_geofence_and_offline_synchronization...")

    # 1. Geocoordinate Validation
    # Valid Delhi Coordinates (28.61°N, 77.20°E) -> VALIDATED
    geo_valid = verify_geocoordinates(28.6139, 77.2090, state="Delhi", district="New Delhi")
    assert geo_valid.is_valid_coordinate is True
    assert geo_valid.in_bounds is True
    assert geo_valid.geofence_status == "VALIDATED"

    # Coordinates outside India (e.g. 51.50°N, 0.12°W - London) -> OUT_OF_JURISDICTION
    geo_outside = verify_geocoordinates(51.5074, -0.1278)
    assert geo_outside.in_bounds is False
    assert geo_outside.geofence_status == "OUT_OF_JURISDICTION"

    # 2. SHA-256 Provenance Chaining
    p_hash = compute_inspection_provenance_hash(
        inspection_id=str(uuid.uuid4()),
        inspector_id=str(uuid.uuid4()),
        lat=28.6139,
        lon=77.2090,
        timestamp="2026-09-03T12:00:00Z",
    )
    assert len(p_hash) == 64  # SHA-256 hex length

    # 3. Test API Endpoints
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": "sharma@doca.gov.in", "password": "password123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Geovalidate API
        geo_api_res = await client.post("/api/v1/provenance/geovalidate", json={
            "latitude": 28.6139,
            "longitude": 77.2090,
            "expected_state": "Delhi",
            "expected_district": "New Delhi",
        }, headers=headers)
        assert geo_api_res.status_code == 200
        assert geo_api_res.json()["geofence_status"] == "VALIDATED"

        # Offline Sync API (Batch Ingest)
        sync_payload = {
            "device_id": "FIELD-TABLET-DELHI-04",
            "offline_inspections": [
                {
                    "client_temp_id": "OFFLINE-DRAFT-001",
                    "store_name": "Azadpur Mandi Wholesaler B-12",
                    "store_address": "Shed 4, Azadpur Mandi, Delhi 110033",
                    "district": "North Delhi",
                    "state": "Delhi",
                    "gps_latitude": 28.7150,
                    "gps_longitude": 77.1720,
                    "created_at_local": "2026-09-03T11:30:00+05:30",
                    "commodity_name": "Chana Dal 1kg Pack",
                    "manufacturer_name": "Desi Agro Foods Ltd.",
                    "net_quantity": "1 kg",
                    "mrp": "Rs. 120.00 (incl. of all taxes)",
                    "package_type": "STANDARD",
                    "review_notes": "Field inspection recorded offline in basement warehouse.",
                }
            ],
        }
        sync_res = await client.post("/api/v1/provenance/sync-offline", json=sync_payload, headers=headers)
        assert sync_res.status_code == 200, sync_res.text
        sync_data = sync_res.json()
        assert sync_data["synced_count"] == 1
        assert sync_data["failed_count"] == 0
        assert len(sync_data["synced_records"]) == 1
        assert sync_data["synced_records"][0]["status"] == "SYNCED"
        assert sync_data["synced_records"][0]["geo_verified"] is True
        assert len(sync_data["synced_records"][0]["provenance_hash"]) == 64

    print("PASS: test_phase_2_5_geofence_and_offline_synchronization")


async def main():
    await test_phase_2_3_gravimetric_mpe_engine()
    await test_phase_2_4_statutory_exemptions_and_special_packages()
    await test_phase_2_5_geofence_and_offline_synchronization()
    print("\n=======================================================")
    print("ALL PHASE 2.3, 2.4, 2.5 TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())

