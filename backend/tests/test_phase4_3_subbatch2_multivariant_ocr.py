"""
Phase 4.3 Sub-Batch 2 — Multi-Variant OCR Automated Test Suite
=============================================================
Validates:
1. Multi-Variant OCR Execution: Runs OCR independently across selected variants.
2. Provenance Chain Preservation: Retains raw master hash, parent hash, and variant hash.
3. Non-Overwriting Isolation: Variant results do not clobber each other.
4. Token Stability Analysis: Correctly computes frequencies and stability flags.
5. Conflict Detection: Correctly flags divergent price and quantity candidates.
6. Consensus Synthesis: Accurately selects primary variant and computes stability ratio.
7. Real Packaging Photograph Integration: Validated against physical commodity photo.
"""

import asyncio
import hashlib
import io
import os
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from app.services.image_preprocessing_service import (
    ALL_STANDARD_VARIANTS,
    PreprocessingConfig,
    PreprocessingVariantName,
)
from app.services.ocr.multi_variant_ocr import (
    MultiVariantOCROrchestrator,
    MultiVariantOCRResponse,
    OCRConsensusSummary,
    TokenStability,
    VariantOCRResult,
    multi_variant_ocr_orchestrator,
)


class TestPhase43SubBatch2MultiVariantOCR(unittest.TestCase):
    def setUp(self):
        self.orchestrator = multi_variant_ocr_orchestrator

        # Create a synthetic label image with known text
        self.img = Image.new("RGB", (400, 200), color=(240, 240, 240))
        draw = ImageDraw.Draw(self.img)
        # Draw simulated declarations
        draw.text((20, 20), "TATA TEA PREMIUM", fill=(0, 0, 0))
        draw.text((20, 60), "Net Qty: 500 g", fill=(0, 0, 0))
        draw.text((20, 100), "MRP Rs. 150.00 incl. of all taxes", fill=(0, 0, 0))
        draw.text((20, 140), "Mfg Date: 05/2024", fill=(0, 0, 0))

        buf = io.BytesIO()
        self.img.save(buf, format="PNG")
        self.raw_bytes = buf.getvalue()
        self.raw_hash = hashlib.sha256(self.raw_bytes).hexdigest()

    def test_1_multi_variant_ocr_execution_and_isolation(self):
        """1. OCR executes on multiple variants without cross-contamination or overwriting."""
        target_variants = [
            PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
            PreprocessingVariantName.GRAYSCALE.value,
            PreprocessingVariantName.CONTRAST_NORMALIZED.value,
        ]

        response: MultiVariantOCRResponse = asyncio.run(
            self.orchestrator.process_multi_variant_ocr(
                self.raw_bytes,
                target_variants=target_variants,
            )
        )

        self.assertEqual(response.original_image_hash, self.raw_hash)
        self.assertEqual(len(response.variants_results), 3)

        for v_name in target_variants:
            self.assertIn(v_name, response.variants_results)
            vr = response.variants_results[v_name]
            self.assertEqual(vr.variant_name, v_name)
            self.assertEqual(vr.original_image_hash, self.raw_hash)
            self.assertGreater(len(vr.raw_text), 0)
            self.assertGreater(vr.word_count, 0)
            self.assertIsInstance(vr.tokens_data, list)
        print("[PASS] 1. Multi-variant OCR executes with complete result isolation")

    def test_2_provenance_retention_across_variants(self):
        """2. Each variant OCR result accurately retains cryptographic parentage."""
        target_variants = [
            PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
            PreprocessingVariantName.GRAYSCALE.value,
            PreprocessingVariantName.CONTRAST_NORMALIZED.value,
        ]

        response = asyncio.run(
            self.orchestrator.process_multi_variant_ocr(
                self.raw_bytes,
                target_variants=target_variants,
            )
        )

        norm_orig = response.variants_results[PreprocessingVariantName.NORMALIZED_ORIGINAL.value]
        # NORMALIZED_ORIGINAL parent is raw master
        self.assertEqual(norm_orig.parent_variant_hash, self.raw_hash)

        # Downstream variants have normalized base as their parent
        for v_name in [
            PreprocessingVariantName.GRAYSCALE.value,
            PreprocessingVariantName.CONTRAST_NORMALIZED.value,
        ]:
            vr = response.variants_results[v_name]
            self.assertEqual(vr.parent_variant_hash, norm_orig.processed_image_hash)
        print("[PASS] 2. Cryptographic provenance linkage verified across OCR results")

    def test_3_token_stability_analysis(self):
        """3. Token stability algorithm correctly scores multi-variant token frequencies."""
        # Create synthetic variant results with controlled token presence
        vr1 = VariantOCRResult(
            variant_name="V1",
            raw_text="MRP Rs. 150.00",
            confidence=0.90,
            tokens_data=[
                {"text": "MRP", "conf": 0.90},
                {"text": "Rs.", "conf": 0.90},
                {"text": "150.00", "conf": 0.90},
            ],
            char_count=14,
            word_count=3,
            processing_time_ms=10,
            original_image_hash="hash_orig",
            parent_variant_hash="hash_parent",
            processed_image_hash="hash_p1",
        )
        vr2 = VariantOCRResult(
            variant_name="V2",
            raw_text="MRP Rs. 150.00",
            confidence=0.88,
            tokens_data=[
                {"text": "MRP", "conf": 0.88},
                {"text": "Rs.", "conf": 0.88},
                {"text": "150.00", "conf": 0.88},
            ],
            char_count=14,
            word_count=3,
            processing_time_ms=10,
            original_image_hash="hash_orig",
            parent_variant_hash="hash_parent",
            processed_image_hash="hash_p2",
        )
        vr3 = VariantOCRResult(
            variant_name="V3",
            raw_text="MRP Rs. noise_word",
            confidence=0.70,
            tokens_data=[
                {"text": "MRP", "conf": 0.70},
                {"text": "Rs.", "conf": 0.70},
                {"text": "noise_word", "conf": 0.60},
            ],
            char_count=18,
            word_count=3,
            processing_time_ms=10,
            original_image_hash="hash_orig",
            parent_variant_hash="hash_parent",
            processed_image_hash="hash_p3",
        )

        stabilities = self.orchestrator.analyze_token_stability([vr1, vr2, vr3])
        mrp_tok = next((t for t in stabilities if t.normalized_token == "mrp"), None)
        self.assertIsNotNone(mrp_tok)
        self.assertEqual(mrp_tok.frequency, 3)
        self.assertTrue(mrp_tok.is_stable)
        self.assertEqual(sorted(mrp_tok.variant_sources), ["V1", "V2", "V3"])

        noise_tok = next((t for t in stabilities if t.normalized_token == "noiseword"), None)
        self.assertIsNotNone(noise_tok)
        self.assertEqual(noise_tok.frequency, 1)
        self.assertFalse(noise_tok.is_stable)
        print("[PASS] 3. Token stability accurately distinguishes multi-variant consensus from noise")

    def test_4_conflict_detection_divergent_declarations(self):
        """4. Divergent price or quantity readings across variants are flagged as conflicts."""
        vr1 = VariantOCRResult(
            variant_name="V_NORMAL",
            raw_text="MRP Rs. 150.00 Net Qty: 500 g",
            confidence=0.90,
            tokens_data=[],
            char_count=30,
            word_count=6,
            processing_time_ms=10,
            original_image_hash="h1",
            parent_variant_hash="h2",
            processed_image_hash="h3",
        )
        vr2 = VariantOCRResult(
            variant_name="V_ADAPTIVE",
            raw_text="MRP Rs. 180.00 Net Qty: 500 g",
            confidence=0.85,
            tokens_data=[],
            char_count=30,
            word_count=6,
            processing_time_ms=10,
            original_image_hash="h1",
            parent_variant_hash="h2",
            processed_image_hash="h4",
        )

        conflicts = self.orchestrator.detect_conflicts([vr1, vr2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["field_hint"], "MRP")
        self.assertEqual(conflicts[0]["severity"], "HIGH")
        self.assertTrue(conflicts[0]["requires_human_review"])
        self.assertIn("150.00", conflicts[0]["candidate_values"])
        self.assertIn("180.00", conflicts[0]["candidate_values"])
        print("[PASS] 4. Divergent declaration readings flagged with high-severity review directives")

    def test_5_consensus_synthesis_and_metrics(self):
        """5. Consensus summary correctly selects primary variant and computes stability metrics."""
        response = asyncio.run(
            self.orchestrator.process_multi_variant_ocr(
                self.raw_bytes,
                target_variants=[
                    PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
                    PreprocessingVariantName.GRAYSCALE.value,
                ],
            )
        )

        consensus: OCRConsensusSummary = response.consensus
        self.assertIn(consensus.primary_variant, [
            PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
            PreprocessingVariantName.GRAYSCALE.value,
        ])
        self.assertGreater(consensus.stability_ratio, 0.0)
        self.assertGreater(consensus.stable_token_count, 0)
        self.assertGreater(consensus.mean_confidence_across_variants, 0.0)
        print("[PASS] 5. Consensus synthesis computes valid stability ratios and primary variant")

    def test_6_real_package_image_multi_variant_ocr(self):
        """6. Multi-variant OCR executes against real Phase 4.2 package photograph."""
        candidate_paths = [
            Path("/app/validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg"),
            Path("validation_data/phase4_2_real_packages/compliant/IMG_20260904_230429.jpg"),
            Path(__file__).resolve().parent.parent.parent / "validation_data" / "phase4_2_real_packages" / "compliant" / "IMG_20260904_230429.jpg",
        ]
        real_img_path = None
        for cp in candidate_paths:
            if cp.exists() and cp.is_file():
                real_img_path = cp
                break

        self.assertIsNotNone(real_img_path, f"Real photograph must exist; checked: {[str(p) for p in candidate_paths]}")

        target_variants = [
            PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
            PreprocessingVariantName.CONTRAST_NORMALIZED.value,
        ]

        response = asyncio.run(
            self.orchestrator.process_multi_variant_ocr(
                real_img_path,
                target_variants=target_variants,
            )
        )

        self.assertEqual(len(response.variants_results), 2)
        for v_name in target_variants:
            self.assertIn(v_name, response.variants_results)
            self.assertGreater(len(response.variants_results[v_name].raw_text), 0)

        self.assertGreater(response.consensus.stable_token_count, 0)
        print("[PASS] 6. Real Phase 4.2 packaged-commodity photo successfully processed via multi-variant OCR")


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase43SubBatch2MultiVariantOCR)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        exit(1)


if __name__ == "__main__":
    run_tests()

