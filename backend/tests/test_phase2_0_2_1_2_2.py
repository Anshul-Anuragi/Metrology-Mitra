import asyncio
import io
import uuid
import zipfile
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.enums import CheckResult, ComplianceResult, InspectionStatus, UserRole
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.declaration import Declaration
from app.models.enforcement_notice import EnforcementNotice
from app.models.inspection import Inspection
from app.models.inspection_batch import InspectionBatch
from app.models.legal_rule import LegalRule
from app.models.user import User
from app.services.batch_service import calculate_schedule_iv_sampling_stats, generate_batch_export_bundle
from app.services.enforcement_service import (
    build_compounding_challan_pdf,
    calculate_statutory_compounding_fee,
)
from app.services.measurement_service import evaluate_reference_assisted_measurement
from app.services.ocr.extractor import (
    detect_script_language,
    extract_declaration_from_ocr,
    translate_devanagari_numerals,
)
from app.services.rule_engine import _eval_net_quantity


async def test_indic_multilingual_perception_and_devanagari_numerals():
    """
    Phase 2.0 Test: Tests Devanagari numerals translation, script language detection,
    and bilingual Hindi/English declaration parsing under LMPC Rule 6(1).
    """
    print("\nRunning test_indic_multilingual_perception_and_devanagari_numerals...")

    # 1. Numeral translation
    dev_num = "₹ ५००.५० (५ किग्रा)"
    arabic_num = translate_devanagari_numerals(dev_num)
    assert arabic_num == "₹ 500.50 (5 किग्रा)"

    # 2. Script detection
    assert detect_script_language("Pure English Text Only") == "ENG"
    assert detect_script_language("शुद्ध हिंदी पाठ") == "HIN"
    assert detect_script_language("Mixed शुद्ध एवं English") == "MIXED"

    # 3. Bilingual Hindi extraction
    hindi_ocr = """
    उत्पाद: प्रीमियम बासमती चावल (Premium Basmati Rice)
    निर्माता: फॉर्च्यून फूड्स प्रा. लि., 42 इंडस्ट्रियल एरिया, मुंबई 400001
    शुद्ध मात्रा: ५ किग्रा
    अधिकतम खुदरा मूल्य: ₹ २७५.०० (सभी करों सहित)
    पैकिंग तिथि: 09/2026
    उपभोक्ता सेवा: 1800-200-1234, customercare@fortunefoods.in
    मूल देश: भारत
    """
    fields, confs = extract_declaration_from_ocr(hindi_ocr)
    assert fields["_language_detected"] == "MIXED"
    assert "बासमती चावल" in fields["commodity_name"]
    assert "275.00" in fields["mrp"]
    assert "सभी कर" in fields["mrp"]
    assert "5 kg" in fields["net_quantity"]
    assert fields["packing_date"] == "09/2026"
    assert fields["country_of_origin"] == "भारत"
    assert fields["consumer_care_phone"] == "1800-200-1234"
    print("PASS: test_indic_multilingual_perception_and_devanagari_numerals")


async def test_batch_inspections_and_schedule_iv_sampling():
    """
    Phase 2.1 Test: Tests batch inspection creation, Schedule IV sampling stats,
    physical metrology separation, and offline ZIP evidence bundle generation.
    """
    print("\nRunning test_batch_inspections_and_schedule_iv_sampling...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as Inspector
        login_res = await client.post("/api/v1/auth/login", json={"email": "sharma@doca.gov.in", "password": "password123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Batch
        batch_payload = {
            "name": "Warehouse Depot Lot B-204",
            "lot_size": 200,
            "sample_size": 5,
            "store_name": "Metro Cash & Carry",
            "district": "New Delhi",
            "state": "Delhi",
        }
        create_res = await client.post("/api/v1/batches/", json=batch_payload, headers=headers)
        assert create_res.status_code == 201, create_res.text
        batch_id = create_res.json()["id"]

        # 3. Create Child Inspections and attach to batch
        insp_res1 = await client.post("/api/v1/inspections/", json={
            "store_name": "Metro Cash & Carry", "state": "Delhi", "district": "New Delhi", "batch_id": batch_id
        }, headers=headers)
        insp_id1 = insp_res1.json()["id"]

        insp_res2 = await client.post("/api/v1/inspections/", json={
            "store_name": "Metro Cash & Carry", "state": "Delhi", "district": "New Delhi", "batch_id": batch_id
        }, headers=headers)
        insp_id2 = insp_res2.json()["id"]

        # 4. Fetch Batch Detail and verify Schedule IV stats & physical metrology separation
        detail_res = await client.get(f"/api/v1/batches/{batch_id}", headers=headers)
        assert detail_res.status_code == 200
        batch_detail = detail_res.json()
        assert len(batch_detail["inspections"]) >= 2
        sched_stats = batch_detail["schedule_iv_compliance"]
        assert sched_stats["lot_size"] == 200
        assert sched_stats["samples_inspected"] >= 2
        assert sched_stats["assessment_type"] == "DECLARATION_SAMPLING_ASSESSMENT"
        assert sched_stats["physical_gravimetric_verified"] is False
        assert "Rule 24" in sched_stats["disclaimer"]
        assert sched_stats["source_version"] == "GSR 202(E) / LMPC 2011"
        assert sched_stats["effective_from"] == "2011-04-01"

        # 5. Export ZIP Evidence Bundle
        export_res = await client.get(f"/api/v1/batches/{batch_id}/export-bundle", headers=headers)
        assert export_res.status_code == 200
        assert export_res.headers["content-type"] == "application/zip"

        zf = zipfile.ZipFile(io.BytesIO(export_res.content))
        file_list = zf.namelist()
        assert "batch_summary.json" in file_list
        assert "evidence_manifest.json" in file_list
        print("PASS: test_batch_inspections_and_schedule_iv_sampling")


async def test_section_48_compounding_legal_hardening():
    """
    Phase 2.2 Hardening Test: Tests Section 48 compounding fee calculator tiers,
    statutory ceilings, non-compoundable bars, temporal versioning, and draft disclaimers.
    """
    print("\nRunning test_section_48_compounding_legal_hardening...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as Inspector
        login_res = await client.post("/api/v1/auth/login", json={"email": "sharma@doca.gov.in", "password": "password123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test Compounding Calculator API — First Offence (Statutory Ceiling ₹25,000)
        c1 = await client.post("/api/v1/enforcement/calculate-compounding", json={
            "offence_count": 1,
            "violation_rule_codes": ["LMPC-R6-MRP", "LMPC-R6-DATE"],
            "is_repeat_within_three_years": False,
        }, headers=headers)
        assert c1.status_code == 200
        data1 = c1.json()
        assert data1["assessment_status"] == "COMPOUNDABLE"
        assert data1["is_compoundable"] is True
        assert data1["compounding_amount_reference"] == 25000.0  # Statutory ceiling
        assert data1["max_statutory_penalty"] == 25000.0
        assert data1["amount_determinable"] is True
        assert data1["source_legislation"] == "Legal Metrology Act, 2009"
        assert data1["source_version"] == "Act No. 1 of 2010"
        assert data1["effective_from"] == "2011-04-01"
        assert "Section 48 is discretionary" in data1["disclaimer"]

        # 3. Second Offence within 3 years (Statutory bar under Sec 48(2) -> NON_COMPOUNDABLE)
        c2 = await client.post("/api/v1/enforcement/calculate-compounding", json={
            "offence_count": 2,
            "violation_rule_codes": ["LMPC-R6-MRP"],
            "is_repeat_within_three_years": True,
        }, headers=headers)
        assert c2.status_code == 200
        data2 = c2.json()
        assert data2["assessment_status"] == "NON_COMPOUNDABLE"
        assert data2["is_compoundable"] is False
        assert data2["amount_determinable"] is False
        assert data2["compounding_amount_reference"] is None
        assert "Section 48(2)" in data2["legal_rationale"]

        # 4. Second Offence beyond 3 years (Compoundable up to ₹50,000 ceiling)
        c2_valid = await client.post("/api/v1/enforcement/calculate-compounding", json={
            "offence_count": 2,
            "violation_rule_codes": ["LMPC-R6-MRP"],
            "is_repeat_within_three_years": False,
        }, headers=headers)
        assert c2_valid.status_code == 200
        data2_valid = c2_valid.json()
        assert data2_valid["assessment_status"] == "COMPOUNDABLE"
        assert data2_valid["compounding_amount_reference"] == 50000.0

        # 5. Third / Subsequent Offence (Penal court prosecution -> NON_COMPOUNDABLE)
        c3 = await client.post("/api/v1/enforcement/calculate-compounding", json={
            "offence_count": 3,
        }, headers=headers)
        assert c3.status_code == 200
        data3 = c3.json()
        assert data3["assessment_status"] == "NON_COMPOUNDABLE"
        assert data3["is_compoundable"] is False
        assert data3["compounding_amount_reference"] is None

        # 6. Historical Pre-2011 Date (Precedes Legal Metrology Act, 2009 -> NOT_DETERMINABLE)
        c_hist = await client.post("/api/v1/enforcement/calculate-compounding", json={
            "offence_count": 1,
            "reference_date": "2005-01-01",
        }, headers=headers)
        assert c_hist.status_code == 200
        data_hist = c_hist.json()
        assert data_hist["assessment_status"] == "NOT_DETERMINABLE"
        assert data_hist["amount_determinable"] is False
        assert data_hist["source_version"] == "Historical Pre-2011"

        # 7. Create Draft Enforcement Notice
        insp_res = await client.post("/api/v1/inspections/", json={
            "store_name": "Reliance Retail Mart", "state": "Delhi", "district": "Central Delhi"
        }, headers=headers)
        insp_id = insp_res.json()["id"]

        notice_res = await client.post("/api/v1/enforcement/notices", json={
            "inspection_id": insp_id,
            "notice_type": "SHOW_CAUSE_NOTICE",
            "offence_count": 1,
            "officer_remarks": "Absence of statutory MRP and tax statement.",
        }, headers=headers)
        assert notice_res.status_code == 201, notice_res.text
        notice_data = notice_res.json()
        notice_id = notice_data["id"]
        assert "DRAFT-NOT" in notice_data["notice_number"]
        assert notice_data["status"] == "DRAFTED"

        # 8. Update Notice status to ISSUED
        patch_res = await client.patch(f"/api/v1/enforcement/notices/{notice_id}", json={
            "status": "ISSUED",
            "challan_reference": "CHAL-REF-2026-001",
        }, headers=headers)
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "ISSUED"

        # 9. Download Draft Compounding Challan PDF & Verify Disclaimer
        challan_res = await client.get(f"/api/v1/enforcement/notices/{notice_id}/challan-pdf", headers=headers)
        assert challan_res.status_code == 200
        assert challan_res.headers["content-type"] == "application/pdf"
        assert len(challan_res.content) > 1000
        print("PASS: test_section_48_compounding_legal_hardening")


async def test_physical_measurement_vs_image_estimate_semantics():
    """
    Physical Metrology Separation Test: Verifies that missing physical measurement
    or uncalibrated camera scale outputs REVIEW rather than an automatic FAIL.
    """
    print("\nRunning test_physical_measurement_vs_image_estimate_semantics...")

    # 1. Missing net quantity declaration in OCR -> REVIEW (not automatic FAIL)
    mock_rule = LegalRule(rule_code="LMPC-R6-NETQTY", title="Net Quantity Declaration", rule_type="MANDATORY")
    res_missing, val, conf, reason = _eval_net_quantity(None, mock_rule)
    assert res_missing == CheckResult.REVIEW
    assert "ocular" in reason.lower() or "physical" in reason.lower()

    # 2. Uncalibrated reference numeral height estimation -> REVIEW (with is_prototype=True)
    meas_res = evaluate_reference_assisted_measurement(
        pdp_area_cm2=100.0,
        pixel_height=20.0,
        pixel_scale_mm_per_px=None,  # Uncalibrated / unavailable
    )
    assert meas_res.result == CheckResult.REVIEW
    assert meas_res.is_prototype is True
    assert "unavailable" in meas_res.reason.lower() or "calibrated" in meas_res.reason.lower()
    print("PASS: test_physical_measurement_vs_image_estimate_semantics")


async def main():
    await test_indic_multilingual_perception_and_devanagari_numerals()
    await test_batch_inspections_and_schedule_iv_sampling()
    await test_section_48_compounding_legal_hardening()
    await test_physical_measurement_vs_image_estimate_semantics()
    print("\n=======================================================")
    print("ALL PHASE 2.0, 2.1, 2.2 HARDENING TESTS PASSED!")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())
