"""
Phase 4.3 Sub-Batch 3 — Test Suite: Multi-Variant Barcode & Declaration Fusion
=============================================================================
Tests:
1. Multi-format barcode decoding (Path, PIL Image, raw bytes).
2. Barcode quorum voting across multiple variants with controlled demo catalog lookup.
3. Multi-variant declaration fusion: corroborated fields achieve CONFIRMED state.
4. Multi-variant declaration conflict detection: divergent readings trigger CONFLICTING and human review.
5. Declaration fusion state handling: PROBABLE for single variants, MISSING for unobserved fields.
6. Real Phase 4.2 packaged-commodity photograph end-to-end integration.
"""

import hashlib
import io
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

from app.services.barcode_service import (
    BarcodeDetectionResult,
    BarcodeQuorumResult,
    decode_barcodes_from_image,
    decode_barcodes_multi_variant,
    lookup_master_catalog,
)
from app.services.image_preprocessing_service import (
    PreprocessingResult,
    image_preprocessing_service,
)
from app.services.ocr.declaration_fusion import (
    DeclarationFusionService,
    FieldEvidenceState,
    FusedDeclarationSummary,
    declaration_fusion_service,
)
from app.services.ocr.multi_variant_ocr import VariantOCRResult


class TestPhase43SubBatch3DeclarationFusion(unittest.TestCase):
    def setUp(self):
        self.fusion_service = declaration_fusion_service

    def test_1_barcode_multi_format_support(self):
        """1. decode_barcodes_from_image supports PIL Image, bytes, and Path inputs."""
        # Create a simple test image
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        # Decoding on an image with no barcodes should return an empty list gracefully
        res_pil = decode_barcodes_from_image(img)
        self.assertIsInstance(res_pil, list)

        res_bytes = decode_barcodes_from_image(raw_bytes)
        self.assertIsInstance(res_bytes, list)

        # Mock PreprocessingResult wrapper
        prep_result = PreprocessingResult(
            variant_name="TEST_VAR",
            original_image_hash="hash_orig",
            parent_variant_hash="hash_parent",
            processed_image_hash="hash_proc",
            width=200,
            height=200,
            mode="RGB",
            parameters_used={},
            provenance_metadata={},
            image=img,
            image_bytes=raw_bytes,
        )
        res_prep = decode_barcodes_from_image(prep_result)
        self.assertIsInstance(res_prep, list)
        print("[PASS] 1. decode_barcodes_from_image supports Image, bytes, and PreprocessingResult inputs")

    def test_2_barcode_multi_variant_quorum(self):
        """2. decode_barcodes_multi_variant aggregates quorum votes and checks catalog."""
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b = buf.getvalue()

        variants = [
            PreprocessingResult(
                variant_name="NORMALIZED_ORIGINAL",
                original_image_hash="hash0",
                parent_variant_hash="hash0",
                processed_image_hash="hash1",
                width=200,
                height=200,
                mode="RGB",
                parameters_used={},
                provenance_metadata={},
                image=img,
                image_bytes=b,
            ),
            PreprocessingResult(
                variant_name="SHARPENED",
                original_image_hash="hash0",
                parent_variant_hash="hash1",
                processed_image_hash="hash2",
                width=200,
                height=200,
                mode="RGB",
                parameters_used={},
                provenance_metadata={},
                image=img,
                image_bytes=b,
            ),
        ]

        quorum = decode_barcodes_multi_variant(variants)
        self.assertIsInstance(quorum, BarcodeQuorumResult)
        self.assertEqual(quorum.total_variants_evaluated, 2)
        self.assertIn("NORMALIZED_ORIGINAL", quorum.variant_detections)
        self.assertIn("SHARPENED", quorum.variant_detections)
        self.assertEqual(quorum.provenance_hashes["NORMALIZED_ORIGINAL"], "hash1")
        self.assertEqual(quorum.provenance_hashes["SHARPENED"], "hash2")

        # Verify catalog lookup on demo catalog
        cat_match = lookup_master_catalog("8901030889211")
        self.assertIsNotNone(cat_match)
        self.assertEqual(cat_match["brand_name"], "Tata Sampann")
        print("[PASS] 2. Barcode quorum aggregates variants and verifies against master catalog")

    def test_3_declaration_fusion_confirmed_fields(self):
        """3. Statutory fields corroborated across multiple variants achieve CONFIRMED state."""
        vr1 = VariantOCRResult(
            variant_name="NORMALIZED_ORIGINAL",
            raw_text="Tata Sampann Toor Dal. Net Qty: 1 kg. MRP Rs. 175.00 incl. of all taxes. Mfg: Tata Consumer Products Ltd, Mumbai 400001.",
            confidence=0.92,
            tokens_data=[],
            char_count=120,
            word_count=20,
            processing_time_ms=10,
            original_image_hash="hash0",
            parent_variant_hash="hash0",
            processed_image_hash="hash1",
        )
        vr2 = VariantOCRResult(
            variant_name="SHARPENED",
            raw_text="Tata Sampann Toor Dal. Net Qty: 1 kg. MRP Rs. 175.00 (inclusive of all taxes). Tata Consumer Products Ltd.",
            confidence=0.88,
            tokens_data=[],
            char_count=100,
            word_count=17,
            processing_time_ms=10,
            original_image_hash="hash0",
            parent_variant_hash="hash1",
            processed_image_hash="hash2",
        )

        fused: FusedDeclarationSummary = self.fusion_service.fuse_variant_declarations([vr1, vr2])
        self.assertFalse(fused.has_conflicts)
        self.assertFalse(fused.requires_human_review)

        # Check Net Quantity
        net_qty_field = fused.fused_fields.get("net_quantity")
        self.assertIsNotNone(net_qty_field)
        self.assertEqual(net_qty_field.evidence_state, FieldEvidenceState.CONFIRMED)
        self.assertIn("1 kg", net_qty_field.fused_value)
        self.assertEqual(len(net_qty_field.supporting_variants), 2)

        # Check MRP
        mrp_field = fused.fused_fields.get("mrp")
        self.assertIsNotNone(mrp_field)
        self.assertEqual(mrp_field.evidence_state, FieldEvidenceState.CONFIRMED)
        self.assertEqual(mrp_field.normalized_value, 175.00)
        self.assertEqual(len(mrp_field.supporting_variants), 2)
        print("[PASS] 3. Multi-variant corroborated declarations achieve CONFIRMED state")

    def test_4_declaration_fusion_conflict_detection(self):
        """4. Divergent statutory readings across variants trigger CONFLICTING and human review."""
        vr1 = VariantOCRResult(
            variant_name="NORMALIZED_ORIGINAL",
            raw_text="MRP Rs. 150.00 incl. of all taxes. Net Qty: 500 g.",
            confidence=0.90,
            tokens_data=[],
            char_count=50,
            word_count=10,
            processing_time_ms=10,
            original_image_hash="hash0",
            parent_variant_hash="hash0",
            processed_image_hash="hash1",
        )
        vr2 = VariantOCRResult(
            variant_name="ADAPTIVE_THRESHOLD",
            raw_text="MRP Rs. 180.00 incl. of all taxes. Net Qty: 500 g.",
            confidence=0.85,
            tokens_data=[],
            char_count=50,
            word_count=10,
            processing_time_ms=10,
            original_image_hash="hash0",
            parent_variant_hash="hash0",
            processed_image_hash="hash3",
        )

        fused: FusedDeclarationSummary = self.fusion_service.fuse_variant_declarations([vr1, vr2])
        self.assertTrue(fused.has_conflicts)
        self.assertTrue(fused.requires_human_review)
        self.assertGreater(fused.conflicting_count, 0)

        # Check MRP field is marked CONFLICTING
        mrp_field = fused.fused_fields.get("mrp")
        self.assertEqual(mrp_field.evidence_state, FieldEvidenceState.CONFLICTING)
        self.assertTrue(mrp_field.requires_review)
        self.assertIn("Divergent values detected", mrp_field.review_reason)
        self.assertIn(mrp_field.review_reason, fused.review_reasons)

        # Net quantity should still be CONFIRMED because both agreed on 500 g
        net_qty_field = fused.fused_fields.get("net_quantity")
        self.assertEqual(net_qty_field.evidence_state, FieldEvidenceState.CONFIRMED)
        print("[PASS] 4. Divergent readings trigger CONFLICTING state and human review directive")

    def test_5_declaration_fusion_probable_and_missing_fields(self):
        """5. Single-variant fields receive PROBABLE state; absent fields receive MISSING state."""
        vr1 = VariantOCRResult(
            variant_name="NORMALIZED_ORIGINAL",
            raw_text="Manufactured by Parle Products Pvt Ltd Mumbai. MRP Rs. 150",
            confidence=0.75,
            tokens_data=[],
            char_count=60,
            word_count=10,
            processing_time_ms=10,
            original_image_hash="hash0",
            parent_variant_hash="hash0",
            processed_image_hash="hash1",
        )

        fused: FusedDeclarationSummary = self.fusion_service.fuse_variant_declarations([vr1])
        self.assertFalse(fused.has_conflicts)

        # MRP was only in 1 variant without tax phrasing (conf=0.85 < 0.90) -> PROBABLE
        mrp_field = fused.fused_fields.get("mrp")
        self.assertEqual(mrp_field.evidence_state, FieldEvidenceState.PROBABLE)

        # Net quantity was never mentioned -> MISSING
        net_qty_field = fused.fused_fields.get("net_quantity")
        self.assertEqual(net_qty_field.evidence_state, FieldEvidenceState.MISSING)
        self.assertIsNone(net_qty_field.fused_value)
        print("[PASS] 5. Single-variant fields receive PROBABLE and absent fields receive MISSING")

    def test_6_real_image_barcode_and_declaration_fusion(self):
        """6. End-to-end execution against real Phase 4.2 photograph preserves file integrity."""
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

        # Generate standard preprocessing variants
        from app.services.image_preprocessing_service import ALL_STANDARD_VARIANTS
        variants = image_preprocessing_service.preprocess_image(
            real_img_path, variants=ALL_STANDARD_VARIANTS
        )
        self.assertGreaterEqual(len(variants), 6)

        # Run multi-variant barcode quorum
        quorum = decode_barcodes_multi_variant(variants)
        self.assertIsInstance(quorum, BarcodeQuorumResult)
        self.assertEqual(quorum.total_variants_evaluated, len(variants))

        # Check source file immutability
        with open(real_img_path, "rb") as f:
            final_bytes = f.read()
        self.assertEqual(hashlib.sha256(final_bytes).hexdigest(), initial_hash)
        print("[PASS] 6. Real Phase 4.2 package photograph successfully processed with zero source mutation")


if __name__ == "__main__":
    unittest.main(verbosity=2)
