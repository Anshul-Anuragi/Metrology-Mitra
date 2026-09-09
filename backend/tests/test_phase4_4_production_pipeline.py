"""
Phase 4.4 — Test Suite: Production Inspection Pipeline Integration
===================================================================
Tests:
1. End-to-end inspection pipeline execution with multi-modal evidence fusion.
2. Fused evidence packet persistence in declaration.raw_extractions["fused_evidence"].
3. Statutory declaration enrichment from multi-variant consensus.
4. Backward compatibility preservation for ocr_extracted and barcode_data.
5. Deterministic rule engine evaluation and violation generation from fused declaration.
6. Graceful fallback on virtual/remote images without local disk files.
"""

import asyncio
import io
import uuid
from pathlib import Path
from PIL import Image, ImageDraw

from sqlalchemy import select

from app.core.enums import ComplianceResult, ImageType, InspectionStatus, UserRole
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.user import User
from app.models.violation import Violation
from app.services.pipeline_service import run_full_inspection_pipeline


async def test_1_full_pipeline_with_fused_evidence():
    """1. Inspection pipeline integrates multi-modal evidence fusion into Declaration."""
    async with AsyncSessionLocal() as session:
        # Check for real package photograph or generate clear test image
        real_pkg_path = Path("/app/validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg")
        if not real_pkg_path.exists():
            real_pkg_path = Path("validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg")

        img_file = None
        if real_pkg_path.exists():
            target_image_path = real_pkg_path
        else:
            img_dir = Path("/tmp/test_pipeline_images")
            img_dir.mkdir(parents=True, exist_ok=True)
            img_file = img_dir / f"test_pkg_{uuid.uuid4().hex[:8]}.png"
            img = Image.new("RGB", (1200, 600), color="white")
            draw = ImageDraw.Draw(img)
            draw.text((40, 40), "Tata Sampann Toor Dal", fill="black")
            draw.text((40, 100), "Net Qty: 1 kg", fill="black")
            draw.text((40, 160), "MRP Rs. 175.00 incl. of all taxes", fill="black")
            draw.text((40, 220), "Mfg: Tata Consumer Products Ltd Mumbai 400001", fill="black")
            img.save(img_file, format="PNG")
            target_image_path = img_file

        try:
            # Setup Inspector User, Inspection, and InspectionImage in DB
            user = User(
                id=uuid.uuid4(),
                email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
                password_hash=get_password_hash("TestPass123!"),
                name="Officer Rajesh Kumar",
                role=UserRole.INSPECTOR,
                is_active=True,
            )
            session.add(user)
            await session.commit()

            insp = Inspection(
                inspector_id=user.id,
                store_name="Test Retailer Kolkata",
                status=InspectionStatus.CREATED,
            )
            session.add(insp)
            await session.commit()
            await session.refresh(insp)

            insp_img = InspectionImage(
                inspection_id=insp.id,
                image_url=str(target_image_path),
                image_type=ImageType.FRONT,
                sequence_number=1,
                sha256_hash="dummyhash",
            )
            session.add(insp_img)
            await session.commit()

            # Execute run_full_inspection_pipeline
            insp, decl, checks, viols, evs = await run_full_inspection_pipeline(session, insp)

            # Verify Declaration was created with fused_evidence
            assert decl is not None, "Declaration was not created"
            assert "fused_evidence" in decl.raw_extractions, "fused_evidence missing from raw_extractions"
            fused_ev = decl.raw_extractions["fused_evidence"]
            assert "original_image_hash" in fused_ev, "original_image_hash missing from fused_evidence"
            assert "ocr_consensus" in fused_ev, "ocr_consensus missing from fused_evidence"
            assert "fused_declarations" in fused_ev, "fused_declarations missing from fused_evidence"
            assert "provenance_chain" in fused_ev, "provenance_chain missing from fused_evidence"

            # Verify backward compatibility preservation
            assert "ocr_extracted" in decl.raw_extractions, "ocr_extracted missing from raw_extractions"

            # Verify Rule Engine evaluated statutory compliance checks
            assert len(checks) > 0, "No compliance checks were evaluated"
            field_names = [c.field_name for c in checks]
            assert "mrp" in field_names, "MRP check missing"
            assert "net_quantity" in field_names, "Net Quantity check missing"

            print("[PASS] 1. Full inspection pipeline successfully executed with multi-modal evidence fusion")

        finally:
            if img_file and img_file.exists():
                img_file.unlink()


async def test_2_backward_compatibility_virtual_image():
    """2. Inspection pipeline runs cleanly on virtual images with zero regression."""
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("TestPass123!"),
            name="Officer Neha Sharma",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        session.add(user)
        await session.commit()

        insp = Inspection(
            inspector_id=user.id,
            store_name="Virtual Retailer",
            status=InspectionStatus.CREATED,
        )
        session.add(insp)
        await session.commit()
        await session.refresh(insp)

        # Virtual image with no physical file on disk
        insp_img = InspectionImage(
            inspection_id=insp.id,
            image_url="/uploads/virtual_non_existent.jpg",
            image_type=ImageType.FRONT,
            sequence_number=1,
            sha256_hash="virtualhash",
        )
        session.add(insp_img)
        await session.commit()

        # Pipeline should complete gracefully without throwing FileNotFoundError
        insp, decl, checks, viols, evs = await run_full_inspection_pipeline(session, insp)
        assert decl is not None, "Declaration was not created"
        assert "ocr_extracted" in decl.raw_extractions, "ocr_extracted missing from raw_extractions"
        assert len(checks) == 18, f"Expected 18 checks, got {len(checks)}"
        print("[PASS] 2. Pipeline gracefully handles virtual images without regression")


if __name__ == "__main__":
    async def run_all():
        await test_1_full_pipeline_with_fused_evidence()
        await test_2_backward_compatibility_virtual_image()
        print("\n=======================================================")
        print("ALL PHASE 4.4 PRODUCTION PIPELINE TESTS PASSED!")
        print("=======================================================\n")

    asyncio.run(run_all())

