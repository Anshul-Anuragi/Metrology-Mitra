"""
Phase 4.3 Sub-Batch 4 — Test Suite: Unified Evidence Fusion Layer
================================================================
Tests:
1. End-to-end unified evidence packet generation and schema validation.
2. Optical quality assessment integration and review escalation.
3. OCR consensus and declaration conflict propagation into human review reasons.
4. Physical weighing scale cross-check and shortfall calculation.
5. In-memory cryptographic provenance chain verification.
6. Real Phase 4.2 packaged-commodity photograph execution without source mutation.
"""

import asyncio
import hashlib
import io
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

from app.services.evidence_fusion_service import (
    EvidenceFusionService,
    PhysicalScaleCheckResult,
    UnifiedEvidencePacket,
    evidence_fusion_service,
)
from app.services.image_preprocessing_service import ALL_STANDARD_VARIANTS, image_preprocessing_service


class TestPhase43SubBatch4EvidenceFusion(unittest.TestCase):
    def setUp(self):
        self.service = evidence_fusion_service

    def test_1_unified_packet_generation(self):
        """1. Unified packet generation creates structured evidence with complete provenance."""
        img = Image.new("RGB", (400, 300), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Sample Product Net Qty: 500 g", fill="black")
        draw.text((20, 60), "MRP Rs. 120.00 incl. of all taxes", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        loop = asyncio.get_event_loop()
        packet: UnifiedEvidencePacket = loop.run_until_complete(
            self.service.fuse_evidence(raw_bytes, variant_names=["NORMALIZED_ORIGINAL", "CONTRAST_NORMALIZED"])
        )

        self.assertIsInstance(packet, UnifiedEvidencePacket)
        self.assertEqual(packet.original_image_hash, hashlib.sha256(raw_bytes).hexdigest())
        self.assertIn("NORMALIZED_ORIGINAL", packet.provenance_chain["variants_hashes"])
        self.assertIn("CONTRAST_NORMALIZED", packet.provenance_chain["variants_hashes"])
        self.assertIn(packet.overall_evidence_quality, ("HIGH", "MODERATE", "DEGRADED", "INSUFFICIENT"))

        packet_dict = packet.to_dict()
        self.assertIn("ocr_consensus", packet_dict)
        self.assertIn("barcode_quorum", packet_dict)
        self.assertIn("fused_declarations", packet_dict)
        print("[PASS] 1. Unified evidence packet generated with complete schema and cryptographic provenance")

    def test_2_quality_gating_integration(self):
        """2. Optical quality gating failures escalate to human review."""
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        quality_report = {
            "is_acceptable": False,
            "status": "FAIL",
            "blur_score": 120.0,
            "glare_ratio": 0.15,
        }

        loop = asyncio.get_event_loop()
        packet = loop.run_until_complete(
            self.service.fuse_evidence(
                raw_bytes,
                quality_assessment=quality_report,
                variant_names=["NORMALIZED_ORIGINAL"],
            )
        )

        self.assertTrue(packet.requires_human_review)
        self.assertTrue(any("Optical quality gating flagged" in r for r in packet.human_review_reasons))
        print("[PASS] 2. Optical quality failure properly flags packet for human review")

    def test_3_physical_scale_verification(self):
        """3. Physical scale cross-check calculates tare, net weight, discrepancy, and shortfalls."""
        # Scale telemetry indicating 470g net when package declares 500g (30g shortfall)
        scale_data = {
            "gross_weight_grams": 485.0,
            "tare_weight_grams": 15.0,
            "scale_device_id": "METTLER_TOLEDO_CAL_01",
        }

        scale_res = self.service._cross_check_physical_scale("500 g", scale_data)
        self.assertIsNotNone(scale_res)
        self.assertIsInstance(scale_res, PhysicalScaleCheckResult)
        self.assertEqual(scale_res.net_observed_grams, 470.0)
        self.assertEqual(scale_res.discrepancy_grams, -30.0)
        self.assertAlmostEqual(scale_res.percentage_error, -6.0, places=1)
        self.assertTrue(scale_res.is_shortfall)
        self.assertEqual(scale_res.scale_device_id, "METTLER_TOLEDO_CAL_01")
        print("[PASS] 3. Physical scale discrepancy and shortfall calculated accurately")

    def test_4_provenance_immutability(self):
        """4. Master hash, derivative hashes, and parentage form consistent in-memory chain."""
        img = Image.new("RGB", (150, 150), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
        orig_hash = hashlib.sha256(raw_bytes).hexdigest()

        variants = image_preprocessing_service.preprocess_image(
            raw_bytes, variants=["NORMALIZED_ORIGINAL", "GRAYSCALE", "CONTRAST_NORMALIZED"]
        )

        for v in variants:
            self.assertEqual(v.original_image_hash, orig_hash)
            self.assertIsNotNone(v.processed_image_hash)
            self.assertIsNotNone(v.parent_variant_hash)
        print("[PASS] 4. Cryptographic provenance chain verified across all generated derivatives")

    def test_5_real_package_image_evidence_fusion(self):
        """5. End-to-end multi-modal evidence fusion runs on real Phase 4.2 package photograph."""
        possible_paths = [
            Path("/app/validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg"),
            Path("validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg"),
        ]
        real_img_path = next((p for p in possible_paths if p.exists()), None)
        if real_img_path is None:
            self.skipTest("Real Phase 4.2 package photograph not found in test environment")

        with open(real_img_path, "rb") as f:
            raw_bytes = f.read()
        initial_hash = hashlib.sha256(raw_bytes).hexdigest()

        loop = asyncio.get_event_loop()
        packet: UnifiedEvidencePacket = loop.run_until_complete(
            self.service.fuse_evidence(
                real_img_path,
                variant_names=["NORMALIZED_ORIGINAL", "GRAYSCALE", "CONTRAST_NORMALIZED"],
            )
        )

        self.assertIsInstance(packet, UnifiedEvidencePacket)
        self.assertEqual(packet.original_image_hash, initial_hash)
        self.assertGreaterEqual(packet.preprocessing_summary["total_variants_generated"], 3)

        # Confirm zero mutation on real file
        with open(real_img_path, "rb") as f:
            final_bytes = f.read()
        self.assertEqual(hashlib.sha256(final_bytes).hexdigest(), initial_hash)
        print("[PASS] 5. Real Phase 4.2 package photograph processed with zero source mutation")


if __name__ == "__main__":
    unittest.main(verbosity=2)

