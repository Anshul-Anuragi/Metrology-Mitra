import asyncio
import io
import json
import uuid
from datetime import date, datetime, timezone
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    CheckResult,
    ComplianceResult,
    ImageType,
    InspectionStatus,
    ReportType,
    UserRole,
)
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.legal_rule import LegalRule
from app.models.user import User
from app.services.barcode_service import lookup_master_catalog, verify_mrp_against_catalog
from app.services.image_quality import QualityGateDecision, QualityStatus, assess_image_quality
from app.services.listing_service import DigitalListingData, cross_check_digital_listing
from app.services.measurement_service import evaluate_reference_assisted_measurement, get_schedule_ii_min_height
from app.services.report_service import create_inspection_report
from app.services.rule_engine import evaluate_inspection
from app.services.rule_seeder import seed_legal_rules
from app.services.storage import compute_sha256, storage_service


async def test_rule_seeding_and_versioning():
    """Verifies that 18 statutory rules are seeded with versioning and channel metadata."""
    async with AsyncSessionLocal() as db:
        count = await seed_legal_rules(db)
        assert count == 18, f"Expected 18 statutory rules, found {count}"

        rules_res = await db.execute(select(LegalRule).where(LegalRule.is_active == True))
        active_rules = rules_res.scalars().all()
        assert len(active_rules) == 18

        codes = {r.rule_code: r for r in active_rules}
        assert "LMPC-R6-COMMODITY-NAME" in codes
        assert "LMPC-R6-MANUFACTURER" in codes
        assert "LMPC-R6-NET-QUANTITY" in codes
        assert "LMPC-R6-MRP" in codes
        assert "LMPC-R6-DATE" in codes
        assert "LMPC-R6-CONSUMER-CARE" in codes
        assert "LMPC-R6-ORIGIN" in codes
        assert "LMPC-R6-USP" in codes
        assert "LMPC-R6-EXPIRY" in codes
        assert "LMPC-R7-FONT-HEIGHT" in codes
        assert "LMPC-R8-PDP-PLACEMENT" in codes
        assert "LMPC-R9-LEGIBILITY" in codes
        assert "LMPC-R18-DUAL-MRP" in codes
        assert "LMPC-R6-PACKER-DISTINCTION" in codes
        assert "LMPC-R12-SYMBOL-PLACEMENT" in codes
        assert "LMPC-R10-ECOM-DECLARATIONS" in codes
        assert "LMPC-R14-STANDARD-PACK" in codes
        assert "LMPC-R27-REGISTRATION" in codes

        # Verify temporal metadata
        usp_rule = codes["LMPC-R6-USP"]
        assert usp_rule.version == "2021.1"
        assert usp_rule.effective_from == date(2022, 12, 1)

        ecom_rule = codes["LMPC-R10-ECOM-DECLARATIONS"]
        assert ecom_rule.channel == "ECOMMERCE"
        assert ecom_rule.source_version == "2017.1"


async def test_rule_7_schedule_ii_pdp_tiers_and_measurement():
    """Verifies Rule 7 numeral height thresholds and reference-assisted measurement logic."""
    # Test PDP Area Tiers under Schedule II Table 1
    assert get_schedule_ii_min_height(30.0) == 1.0
    assert get_schedule_ii_min_height(75.0) == 1.5
    assert get_schedule_ii_min_height(250.0) == 2.0
    assert get_schedule_ii_min_height(1000.0) == 4.0
    assert get_schedule_ii_min_height(3000.0) == 6.0
    assert get_schedule_ii_min_height(75.0, is_blown_or_moulded=True) == 2.0

    # Uncalibrated scale strictly returns REVIEW
    uncalibrated = evaluate_reference_assisted_measurement(
        pdp_area_cm2=150.0,
        pixel_height=25.0,
        pixel_scale_mm_per_px=None,
        scale_source="UNAVAILABLE",
    )
    assert uncalibrated.result == CheckResult.REVIEW
    assert "unavailable" in uncalibrated.reason.lower()
    assert uncalibrated.threshold_mm == 2.0

    # Calibrated scale meeting threshold
    calibrated_pass = evaluate_reference_assisted_measurement(
        pdp_area_cm2=80.0,  # threshold is 1.5 mm
        pixel_height=25.0,
        pixel_scale_mm_per_px=0.08,  # -> 2.0 mm
        scale_source="REFERENCE_OBJECT",
        scale_confidence=0.9,
    )
    assert calibrated_pass.result == CheckResult.PASS
    assert calibrated_pass.physical_height_mm == 2.0
    assert calibrated_pass.threshold_mm == 1.5

    # Calibrated scale below threshold -> REVIEW for inspector verification
    calibrated_below = evaluate_reference_assisted_measurement(
        pdp_area_cm2=80.0,  # threshold is 1.5 mm
        pixel_height=12.0,
        pixel_scale_mm_per_px=0.08,  # -> 0.96 mm
        scale_source="REFERENCE_OBJECT",
        scale_confidence=0.9,
    )
    assert calibrated_below.result == CheckResult.REVIEW
    assert "below" in calibrated_below.reason.lower()


async def test_mrp_demo_catalog_neutral_discrepancy_semantics():
    """Verifies that catalog price differences produce REVIEW with neutral terminology."""
    # Catalog product: Tata Sampann Toor Dal (MRP ₹175.00)
    cat_product = lookup_master_catalog("8901030889211")
    assert cat_product is not None
    assert cat_product["standard_mrp"] == 175.00
    assert cat_product["is_demo_record"] is True

    # Case 1: Matching MRP
    status, reason, obs, cat = verify_mrp_against_catalog(
        "MRP Rs. 175.00 incl. of all taxes", cat_product
    )
    assert status == "MATCH"
    assert obs == 175.00
    assert "matches" in reason

    # Case 2: Mismatched MRP (Observed ₹210 vs Catalog ₹175)
    status, reason, obs, cat = verify_mrp_against_catalog(
        "MRP Rs. 210.00 incl. of all taxes", cat_product
    )
    assert status == "MISMATCH"
    assert obs == 210.00
    assert "MRP discrepancy detected against reference data" in reason
    assert "fraud" not in reason.lower()
    assert "tampering" not in reason.lower()


async def test_digital_listing_cross_check():
    """Verifies physical package vs digital marketplace listing cross-check."""
    decl = Declaration(
        commodity_name="Dark Chocolate Bar",
        country_of_origin="Switzerland",
        net_quantity="100 g",
        mrp="MRP Rs. 450.00 incl. of all taxes",
        is_imported=True,
    )

    # Contradictory listing (Origin stated as India instead of Switzerland)
    listing_contradiction = DigitalListingData(
        title="Swiss Dark Chocolate",
        description="Premium Imported Chocolate",
        price=450.00,
        country_of_origin="India",  # Contradiction!
        net_quantity="100 g",
        manufacturer_name="Chocolatier Suisse",
        listing_url="https://example.com/product/123",
    )
    report = cross_check_digital_listing(listing_contradiction, decl)
    assert report.has_contradictions is True
    assert report.summary_verdict == CheckResult.REVIEW
    assert any("Contradictory declaration" in it.finding for it in report.items)

    # Consistent listing
    listing_matching = DigitalListingData(
        title="Swiss Dark Chocolate",
        description="Premium Imported Chocolate",
        price=450.00,
        country_of_origin="Switzerland",
        net_quantity="100 g",
        manufacturer_name="Chocolatier Suisse",
        listing_url="https://example.com/product/123",
    )
    report_match = cross_check_digital_listing(listing_matching, decl)
    assert report_match.has_contradictions is False
    assert report_match.summary_verdict == CheckResult.PASS


async def test_image_quality_preflight_gate(tmp_path):
    """Verifies pre-flight quality gate classifications (READY_FOR_ANALYSIS, RETAKE_RECOMMENDED)."""
    # 1. Clear sharp synthetic image with high contrast checkerboard pattern
    sharp_img = Image.new("L", (800, 800))
    for x in range(800):
        for y in range(800):
            if ((x // 8) + (y // 8)) % 2 == 0:
                sharp_img.putpixel((x, y), 200)
            else:
                sharp_img.putpixel((x, y), 50)
    sharp_path = tmp_path / "sharp.jpg"
    sharp_img.save(sharp_path)

    res_sharp = assess_image_quality(sharp_path)
    assert res_sharp.gate_decision == QualityGateDecision.READY_FOR_ANALYSIS
    assert res_sharp.is_acceptable is True

    # 2. Heavy blur / uniform image -> RETAKE_RECOMMENDED
    blurry_img = Image.new("RGB", (800, 800), color=(128, 128, 128))
    blur_path = tmp_path / "blurry.jpg"
    blurry_img.save(blur_path)

    res_blur = assess_image_quality(blur_path)
    assert res_blur.gate_decision == QualityGateDecision.RETAKE_RECOMMENDED
    assert res_blur.blur_status == QualityStatus.FAIL
    assert len(res_blur.actionable_reasons) > 0


async def test_sha256_evidence_integrity_hashing():
    """Verifies byte-level SHA-256 evidence integrity hashing on image ingestion."""
    dummy_bytes = b"MetrologyMitra Evidence Photograph Sample Bytes 12345"
    expected_hash = compute_sha256(dummy_bytes)
    assert len(expected_hash) == 64

    test_insp_id = uuid.uuid4()
    saved_url, returned_hash = await storage_service.save_image(
        file_bytes=dummy_bytes,
        filename="test_evidence.jpg",
        inspection_id=test_insp_id,
    )
    assert returned_hash == expected_hash
    assert str(test_insp_id) in saved_url


async def test_full_inspection_evaluation_and_adjudication():
    """Verifies end-to-end deterministic rule evaluation and inspector finalization."""
    async with AsyncSessionLocal() as db:
        await seed_legal_rules(db)

        # Get or create inspector user
        user_res = await db.execute(select(User).where(User.role == UserRole.INSPECTOR))
        inspector = user_res.scalars().first()
        if not inspector:
            inspector = User(
                name="Officer Sharma",
                email="sharma@doca.gov.in",
                password_hash="fakehash",
                role=UserRole.INSPECTOR,
            )
            db.add(inspector)
            await db.commit()
            await db.refresh(inspector)

        # Create test inspection
        insp = Inspection(
            inspector_id=inspector.id,
            store_name="Metro Cash & Carry",
            district="South Delhi",
            state="Delhi",
            status=InspectionStatus.CREATED,
            overall_result=ComplianceResult.PENDING,
            started_at=datetime.now(timezone.utc),
        )
        db.add(insp)
        await db.flush()

        # Declaration with missing MRP and non-standard net qty (500 Gms)
        decl = Declaration(
            inspection_id=insp.id,
            commodity_name="Pulses",
            manufacturer_name="Grain Mills India",
            address="Plot 5, Industrial Area, Okhla, New Delhi 110020",
            net_quantity="500 Gms",  # Illegal casing! Should fail Rule 13 / Rule 12(2)
            mrp="MRP Rs. 85.00",    # Missing 'incl. of all taxes' -> Fail
            manufacturing_date="05/2026",
            consumer_care="1800-111-222, care@grainmills.in",
            is_human_verified=False,
        )
        db.add(decl)
        await db.flush()

        # Run deterministic evaluation
        verdict, checks = await evaluate_inspection(db, insp, decl)
        assert verdict == ComplianceResult.NON_COMPLIANT
        assert any(c.result == CheckResult.FAIL for c in checks)

        # Inspector applies human verification and corrections
        decl.net_quantity = "500 g"
        decl.mrp = "MRP Rs. 85.00 incl. of all taxes"
        decl.unit_sale_price = "Rs. 0.17/g"
        decl.expiry_date = "12/2026"
        decl.is_human_verified = True
        await db.flush()

        # Re-evaluate
        new_verdict, new_checks = await evaluate_inspection(db, insp, decl)
        assert new_verdict == ComplianceResult.COMPLIANT
        assert all(c.result == CheckResult.PASS for c in new_checks)

        # Generate Safe PDF Report
        report, pdf_bytes, media_type = await create_inspection_report(
            db=db,
            inspection_id=insp.id,
            report_type=ReportType.PDF,
            current_user=inspector,
        )
        assert report is not None
        assert media_type == "application/pdf"
        assert len(pdf_bytes) > 500


async def run_all_tests():
    import tempfile
    from pathlib import Path
    print("Running test_image_quality_preflight_gate...")
    with tempfile.TemporaryDirectory() as td:
        await test_image_quality_preflight_gate(Path(td))
    print("PASS: test_image_quality_preflight_gate")

    print("Running test_rule_seeding_and_versioning...")
    await test_rule_seeding_and_versioning()
    print("PASS: test_rule_seeding_and_versioning")

    print("Running test_rule_7_schedule_ii_pdp_tiers_and_measurement...")
    await test_rule_7_schedule_ii_pdp_tiers_and_measurement()
    print("PASS: test_rule_7_schedule_ii_pdp_tiers_and_measurement")

    print("Running test_mrp_demo_catalog_neutral_discrepancy_semantics...")
    await test_mrp_demo_catalog_neutral_discrepancy_semantics()
    print("PASS: test_mrp_demo_catalog_neutral_discrepancy_semantics")

    print("Running test_digital_listing_cross_check...")
    await test_digital_listing_cross_check()
    print("PASS: test_digital_listing_cross_check")

    print("Running test_sha256_evidence_integrity_hashing...")
    await test_sha256_evidence_integrity_hashing()
    print("PASS: test_sha256_evidence_integrity_hashing")

    print("Running test_full_inspection_evaluation_and_adjudication...")
    await test_full_inspection_evaluation_and_adjudication()
    print("PASS: test_full_inspection_evaluation_and_adjudication")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
    print("\n=======================================================")
    print("ALL PHASE 1.7, 1.8, 1.9 TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")
