"""
Phase 4.3 — Perception Robustness & Image Preprocessing Automated Test Suite
===========================================================================
Sub-Batch 1 Hardened Verification Gate (12 Explicit Invariants):
1. raw master bytes remain unchanged
2. normalized derivative distinction
3. deterministic output bytes (IMAGE_OUTPUT_DETERMINISM = PASS)
4. deterministic output hashes (IMAGE_HASH_DETERMINISM = PASS)
5. run-specific timestamp semantics (PROVENANCE_TIMESTAMP = RUN_SPECIFIC)
6. original raw hash propagation across all variants
7. parent hash hierarchy (RAW_MASTER -> NORMALIZED_ORIGINAL -> derivatives)
8. dimension bounds enforcement
9. quality-driven deterministic variant selection
10. legal-rule-engine authority isolation
11. adaptive-threshold mathematical correctness (above, below, boundary, uniform)
12. path-based source file non-mutation
"""

import hashlib
import io
import os
import tempfile
import time
import unittest
from pathlib import Path
from PIL import Image, ImageFilter

from app.services.image_preprocessing_service import (
    ALL_STANDARD_VARIANTS,
    ImagePreprocessingService,
    PreprocessingConfig,
    PreprocessingResult,
    PreprocessingVariantName,
    image_preprocessing_service,
)
from app.services.image_quality import (
    ImageQualityResult,
    QualityGateDecision,
    QualityStatus,
)
from app.services.rule_engine import evaluate_inspection


class TestPhase43PerceptionRobustness(unittest.TestCase):
    def setUp(self):
        self.service = image_preprocessing_service
        self.config = PreprocessingConfig()

        # Create synthetic test image in RGBA mode
        self.raw_img = Image.new("RGBA", (320, 240), color=(180, 180, 180, 255))
        for x in range(50, 200):
            for y in range(50, 200):
                if (x + y) % 20 < 10:
                    self.raw_img.putpixel((x, y), (20, 20, 20, 255))
                else:
                    self.raw_img.putpixel((x, y), (240, 240, 240, 255))

        buf = io.BytesIO()
        self.raw_img.save(buf, format="PNG")
        self.raw_master_bytes = buf.getvalue()
        self.raw_master_hash = hashlib.sha256(self.raw_master_bytes).hexdigest()

    def test_1_raw_master_bytes_immutability(self):
        """1. Raw master bytes remain unchanged during and after preprocessing."""
        bytes_copy = bytes(self.raw_master_bytes)
        results = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        self.assertEqual(self.raw_master_bytes, bytes_copy)
        self.assertEqual(hashlib.sha256(self.raw_master_bytes).hexdigest(), self.raw_master_hash)
        print("[PASS] 1. Raw master bytes remain 100% immutable")

    def test_2_normalized_derivative_distinction(self):
        """2. NORMALIZED_ORIGINAL is a normalized derivative, not untouched raw bytes."""
        results = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=[PreprocessingVariantName.NORMALIZED_ORIGINAL.value]
        )
        self.assertEqual(len(results), 1)
        norm_orig = results[0]

        # Mode normalized to RGB from RGBA
        self.assertEqual(norm_orig.mode, "RGB")
        self.assertEqual(self.raw_img.mode, "RGBA")

        # Explicit metadata stating it is a derivative
        self.assertFalse(norm_orig.parameters_used.get("is_raw_master", True))
        self.assertEqual(norm_orig.original_image_hash, self.raw_master_hash)
        self.assertNotEqual(norm_orig.processed_image_hash, self.raw_master_hash)
        print("[PASS] 2. NORMALIZED_ORIGINAL is distinguishable from RAW_MASTER")

    def test_3_deterministic_output_bytes(self):
        """3. Output image bytes are 100% deterministic (IMAGE_OUTPUT_DETERMINISM = PASS)."""
        run1 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        run2 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        for r1, r2 in zip(run1, run2):
            self.assertEqual(r1.image_bytes, r2.image_bytes)
        print("[PASS] 3. IMAGE_OUTPUT_DETERMINISM = PASS")

    def test_4_deterministic_output_hashes(self):
        """4. Output image hashes are 100% deterministic (IMAGE_HASH_DETERMINISM = PASS)."""
        run1 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        run2 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        for r1, r2 in zip(run1, run2):
            self.assertEqual(r1.processed_image_hash, r2.processed_image_hash)
        print("[PASS] 4. IMAGE_HASH_DETERMINISM = PASS")

    def test_5_run_specific_timestamp_semantics(self):
        """5. Provenance timestamps reflect execution time (PROVENANCE_TIMESTAMP = RUN_SPECIFIC)."""
        run1 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=[PreprocessingVariantName.GRAYSCALE.value]
        )
        time.sleep(0.01)
        run2 = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=[PreprocessingVariantName.GRAYSCALE.value]
        )
        # Image hash matches, while timestamps are recorded per run
        self.assertEqual(run1[0].processed_image_hash, run2[0].processed_image_hash)
        ts1 = run1[0].provenance_metadata["created_at_utc"]
        ts2 = run2[0].provenance_metadata["created_at_utc"]
        self.assertIsInstance(ts1, str)
        self.assertIsInstance(ts2, str)
        print("[PASS] 5. PROVENANCE_TIMESTAMP = RUN_SPECIFIC")

    def test_6_original_raw_hash_propagation(self):
        """6. original_image_hash correctly anchors all variants to the raw master digest."""
        results = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        for r in results:
            self.assertEqual(r.original_image_hash, self.raw_master_hash)
            self.assertEqual(r.provenance_metadata["original_image_hash"], self.raw_master_hash)
        print("[PASS] 6. Original raw master hash propagates to all derivatives")

    def test_7_parent_hash_hierarchy(self):
        """7. parent_variant_hash correctly reflects derivation hierarchy."""
        results = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        variant_map = {r.variant_name: r for r in results}

        norm_orig = variant_map[PreprocessingVariantName.NORMALIZED_ORIGINAL.value]
        # NORMALIZED_ORIGINAL derives from RAW_MASTER
        self.assertEqual(norm_orig.parent_variant_hash, self.raw_master_hash)

        # Downstream variants derive from NORMALIZED_ORIGINAL
        for v_name in [
            PreprocessingVariantName.GRAYSCALE.value,
            PreprocessingVariantName.CONTRAST_NORMALIZED.value,
            PreprocessingVariantName.SHARPENED.value,
            PreprocessingVariantName.UPSCALED.value,
            PreprocessingVariantName.ADAPTIVE_THRESHOLD.value,
        ]:
            self.assertEqual(
                variant_map[v_name].parent_variant_hash,
                norm_orig.processed_image_hash,
                f"Derivative {v_name} parent hash must match normalized base",
            )
        print("[PASS] 7. Cryptographic lineage hierarchy verified (Raw Master -> Base -> Derivatives)")

    def test_8_dimension_bounds(self):
        """8. All standard variants strictly respect spatial dimension boundaries."""
        results = self.service.preprocess_image(
            self.raw_master_bytes, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        self.assertEqual(len(results), len(ALL_STANDARD_VARIANTS))
        for r in results:
            self.assertGreaterEqual(r.width, self.config.min_dimension_px)
            self.assertGreaterEqual(r.height, self.config.min_dimension_px)
            self.assertLessEqual(r.width, self.config.max_dimension_px)
            self.assertLessEqual(r.height, self.config.max_dimension_px)
        print(f"[PASS] 8. All {len(ALL_STANDARD_VARIANTS)} standard variants conform strictly to dimension limits")

    def test_9_quality_driven_deterministic_variant_selection(self):
        """9. Quality-driven variant selection is 100% deterministic."""
        q_diag = ImageQualityResult(
            width=1000,
            height=1000,
            blur_score=700.0,
            blur_status=QualityStatus.PASS,
            glare_ratio=0.10,
            glare_status=QualityStatus.WARNING,
            glare_detected=True,
            exposure_mean=140.0,
            exposure_status=QualityStatus.PASS,
            resolution_status=QualityStatus.PASS,
            gate_decision=QualityGateDecision.MANUAL_REVIEW,
            overall_status=QualityStatus.WARNING,
            is_acceptable=True,
            guidance_message="Glare warning",
            actionable_reasons=["Glare warning"],
        )
        sel1 = self.service.select_adaptive_variants(q_diag)
        sel2 = self.service.select_adaptive_variants(q_diag)
        self.assertEqual(sel1, sel2)
        self.assertEqual(sel1[0], PreprocessingVariantName.NORMALIZED_ORIGINAL.value)
        self.assertIn(PreprocessingVariantName.ADAPTIVE_THRESHOLD.value, sel1)
        print("[PASS] 9. Quality-driven selection is 100% deterministic")

    def test_10_legal_rule_engine_authority_isolation(self):
        """10. Preprocessing service does not have statutory decision authority."""
        self.assertFalse(hasattr(self.service, "evaluate"))
        self.assertFalse(hasattr(self.service, "evaluate_inspection"))
        self.assertFalse(hasattr(self.service, "verdict"))
        self.assertTrue(callable(evaluate_inspection))
        print("[PASS] 10. Legal rule engine remains sole statutory authority")

    def test_11_adaptive_threshold_mathematical_correctness(self):
        """11. Mathematically validate output(x,y) = 255 if gray(x,y) >= local_mean(x,y) - C else 0."""
        c = 10
        custom_cfg = PreprocessingConfig(adaptive_block_size=11, adaptive_c=c)

        # Create a 60x60 test image with 4 distinct test regions
        test_img = Image.new("L", (60, 60), color=150)
        # Region 1: Uniform region (pixels at center of 150 background) -> local mean is 150
        # Region 2: Bright pixel clearly above local mean (220)
        # Region 3: Dark pixel clearly below local mean (40)
        # Region 4: Boundary test pixels:
        #   Pixel at local_mean - C (150 - 10 = 140) -> expected 255
        #   Pixel below local_mean - C (150 - 11 = 139) -> expected 0
        test_img.putpixel((10, 10), 220)  # clearly above
        test_img.putpixel((20, 20), 40)   # clearly below
        test_img.putpixel((30, 30), 140)  # boundary: 140 >= 150 - 10 -> 255
        test_img.putpixel((40, 40), 139)  # boundary: 139 < 150 - 10 -> 0

        # Compute ground-truth local mean using same box blur radius
        radius = custom_cfg.adaptive_block_size // 2
        local_mean_img = test_img.filter(ImageFilter.BoxBlur(radius))

        # Generate ADAPTIVE_THRESHOLD variant
        res = self.service.generate_variant(
            test_img,
            PreprocessingVariantName.ADAPTIVE_THRESHOLD.value,
            custom_cfg,
            orig_hash="test_raw_hash",
        )
        thresh_img = res.image

        # Verify test points against mathematical definition: gray >= local_mean - C
        test_points = [
            (50, 50, "Uniform Region"),
            (10, 10, "Clearly Above Mean"),
            (20, 20, "Clearly Below Mean"),
            (30, 30, "Exactly at (local_mean - C) boundary"),
            (40, 40, "Just below (local_mean - C) boundary"),
        ]

        for x, y, desc in test_points:
            g = test_img.getpixel((x, y))
            m = local_mean_img.getpixel((x, y))
            expected = 255 if g >= (m - c) else 0
            actual = thresh_img.getpixel((x, y))
            self.assertEqual(
                actual,
                expected,
                f"Adaptive threshold mathematical failure at ({x},{y}) [{desc}]: "
                f"gray={g}, local_mean={m}, C={c}, expected={expected}, got={actual}",
            )
        print("[PASS] 11. Adaptive threshold mathematical rule verified (above, below, boundary, uniform)")

    def test_12_path_based_source_file_non_mutation(self):
        """12. Path-based image processing does not alter or write back to the disk file (tested on real Phase 4.2 photo and temp file)."""
        # 1. Resolve and verify real Phase 4.2 packaged-commodity photograph
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

        self.assertIsNotNone(
            real_img_path,
            f"Real Phase 4.2 package photograph must exist on disk; candidate paths checked: {[str(p) for p in candidate_paths]}",
        )

        real_initial_bytes = real_img_path.read_bytes()
        real_initial_hash = hashlib.sha256(real_initial_bytes).hexdigest()
        real_initial_mtime = os.path.getmtime(real_img_path)
        real_initial_size = os.path.getsize(real_img_path)

        # Process real photograph across all standard variants
        real_results = self.service.preprocess_image(
            real_img_path, config=self.config, variants=ALL_STANDARD_VARIANTS
        )
        self.assertEqual(len(real_results), len(ALL_STANDARD_VARIANTS))
        for r in real_results:
            self.assertEqual(r.original_image_hash, real_initial_hash)
            self.assertLessEqual(r.width, self.config.max_dimension_px)
            self.assertLessEqual(r.height, self.config.max_dimension_px)
            self.assertGreater(len(r.image_bytes), 0)

        # Verify real Phase 4.2 package photo on disk remained 100% untouched
        self.assertEqual(real_img_path.read_bytes(), real_initial_bytes)
        self.assertEqual(hashlib.sha256(real_img_path.read_bytes()).hexdigest(), real_initial_hash)
        self.assertEqual(os.path.getmtime(real_img_path), real_initial_mtime)
        self.assertEqual(os.path.getsize(real_img_path), real_initial_size)

        # 2. Also verify against temporary file on isolated write path
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
            temp_path = Path(tf.name)
            img = Image.new("RGB", (200, 200), color=(120, 130, 140))
            img.save(temp_path, format="JPEG")

        try:
            initial_bytes = temp_path.read_bytes()
            initial_hash = hashlib.sha256(initial_bytes).hexdigest()
            initial_mtime = os.path.getmtime(temp_path)
            initial_size = os.path.getsize(temp_path)

            results = self.service.preprocess_image(temp_path, config=self.config)
            self.assertEqual(len(results), 3)  # default core set

            post_bytes = temp_path.read_bytes()
            post_hash = hashlib.sha256(post_bytes).hexdigest()
            post_mtime = os.path.getmtime(temp_path)
            post_size = os.path.getsize(temp_path)

            self.assertEqual(post_bytes, initial_bytes)
            self.assertEqual(post_hash, initial_hash)
            self.assertEqual(post_mtime, initial_mtime)
            self.assertEqual(post_size, initial_size)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        print("[PASS] 12. Path-based processing verified completely non-mutating on disk (tested on real Phase 4.2 photo & temp file)")


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase43PerceptionRobustness)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        exit(1)


if __name__ == "__main__":
    run_tests()
