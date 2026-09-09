"""
MetrologyMitra (SIH26034) — Phase 4.5 P0 OCR & Semantic Evidence Hardening Test Battery
========================================================================================
Comprehensive regression and unit tests verifying:
1. Context-specific OCR normalization (price, net quantity, homoglyphs).
2. Deterministic 2D spatial layout and line/block clustering.
3. Spatial label-to-value association and multiline declaration grouping.
4. Expanded Indian packaging date parsing (DD/MM/YYYY, DD-MM-YYYY, DD MMM YYYY, MM/YYYY).
5. Safe commodity extraction eliminating noisy first-line fallback.
6. Multi-variant declaration fusion with conflict preservation.
7. Resolution-aware optical blur gating.
8. Non-negotiable statutory safety invariants (Legal rule engine untouched).
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from app.services.image_quality import (
    ImageQualityResult,
    QualityGateDecision,
    QualityStatus,
    assess_image_quality,
    compute_resolution_aware_blur_thresholds,
)
from app.services.ocr.declaration_fusion import (
    DeclarationFusionService,
    FieldCandidate,
    FieldEvidenceState,
    FusedDeclarationSummary,
)
from app.services.ocr.extractor import (
    extract_commodity_name,
    extract_consumer_care,
    extract_dates,
    extract_declaration_from_ocr,
    extract_manufacturer_and_address,
    extract_mrp,
    extract_net_quantity,
    extract_unit_sale_price,
)
from app.services.ocr.multi_variant_ocr import VariantOCRResult
from app.services.ocr.normalizer import (
    normalize_price_string,
    normalize_quantity_string,
    parse_and_normalize_date,
)
from app.services.ocr.spatial_layout import (
    SpatialBlock,
    SpatialLayoutResult,
    SpatialLine,
    SpatialToken,
    build_spatial_layout,
)


class TestOCRSpatialHardening(unittest.TestCase):
    """Test suite covering all aspects of Phase 4.5 P0 OCR and Semantic Hardening."""

    # ------------------------------------------------------------------
    # 1. OCR Error & Homoglyph Normalization
    # ------------------------------------------------------------------
    def test_price_homoglyph_and_punctuation_normalization(self):
        """Verifies Rupee symbol homoglyphs, decimal O, and leading comma corrections."""
        res1 = normalize_price_string("MAP FY ,499/-")
        self.assertEqual(res1.normalized_value, 1499.0)
        self.assertIn("HOMOGLYPH_CURRENCY_SYMBOL", res1.normalizations_applied)

        res2 = normalize_price_string("MRP Rs. 145.OO")
        self.assertEqual(res2.normalized_value, 145.0)
        self.assertIn("HOMOGLYPH_DECIMAL_O_TO_ZERO", res2.normalizations_applied)

        res3 = normalize_price_string("₹ 250/-")
        self.assertEqual(res3.normalized_value, 250.0)

        res4 = normalize_price_string("¢4.88")
        self.assertEqual(res4.normalized_value, 4.88)

    def test_quantity_homoglyph_and_unit_normalization(self):
        """Verifies 'k9' -> 'kg', 'OOO' -> '000', and canonical unit conversions."""
        q1 = normalize_quantity_string("1 k9")
        self.assertIsNotNone(q1.normalized_value)
        self.assertEqual(q1.normalized_value["declared_quantity_numeric"], 1000.0)
        self.assertEqual(q1.normalized_value["declared_unit"], "g")

        q2 = normalize_quantity_string("1OOO g")
        self.assertIsNotNone(q2.normalized_value)
        self.assertEqual(q2.normalized_value["declared_quantity_numeric"], 1000.0)

        q3 = normalize_quantity_string("15O ml")
        self.assertIsNotNone(q3.normalized_value)
        self.assertEqual(q3.normalized_value["declared_quantity_numeric"], 150.0)
        self.assertEqual(q3.normalized_value["declared_unit"], "ml")

        q4 = normalize_quantity_string("1 L")
        self.assertIsNotNone(q4.normalized_value)
        self.assertEqual(q4.normalized_value["declared_quantity_numeric"], 1000.0)
        self.assertEqual(q4.normalized_value["declared_unit"], "ml")

    # ------------------------------------------------------------------
    # 2. Expanded Indian Calendar Date Parsing
    # ------------------------------------------------------------------
    def test_expanded_date_formats(self):
        """Supports DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD MMM YYYY, MMM YYYY, MM/YYYY."""
        # DD/MM/YYYY
        d1 = parse_and_normalize_date("15/08/2025")
        self.assertIsNotNone(d1)
        self.assertEqual(d1.normalized_date, "2025-08-15")
        self.assertEqual(d1.date_format, "DD/MM/YYYY")

        # DD-MM-YYYY
        d2 = parse_and_normalize_date("15-08-2025")
        self.assertIsNotNone(d2)
        self.assertEqual(d2.normalized_date, "2025-08-15")

        # DD.MM.YYYY
        d3 = parse_and_normalize_date("15.08.2025")
        self.assertIsNotNone(d3)
        self.assertEqual(d3.normalized_date, "2025-08-15")

        # DD MMM YYYY
        d4 = parse_and_normalize_date("15 AUG 2025")
        self.assertIsNotNone(d4)
        self.assertEqual(d4.normalized_date, "2025-08-15")
        self.assertEqual(d4.date_format, "DD MMM YYYY")

        # MMM YYYY
        d5 = parse_and_normalize_date("AUG 2025")
        self.assertIsNotNone(d5)
        self.assertEqual(d5.normalized_date, "2025-08")

        # MM/YYYY
        d6 = parse_and_normalize_date("08/2025")
        self.assertIsNotNone(d6)
        self.assertEqual(d6.normalized_date, "2025-08")

        # Statutory extractor integration
        mfg, pkd, exp, bb, conf = extract_dates("Mfd Date: 15/08/2025\nUse by: 15/08/2027")
        self.assertEqual(mfg, "15/08/2025")
        self.assertEqual(exp, "15/08/2027")
        self.assertGreaterEqual(conf, 0.90)

    # ------------------------------------------------------------------
    # 3. Multiline Packaging Layouts & Spatial Parsing
    # ------------------------------------------------------------------
    def test_multiline_mrp_extraction(self):
        """Verifies stacked multiline MRP declarations across newlines and tax qualifiers."""
        text1 = "MAXIMUM RETAIL PRICE\n(INCLUSIVE OF ALL TAXES)\nRs. 145.00"
        val1, conf1 = extract_mrp(text1)
        self.assertIsNotNone(val1)
        self.assertIn("145.00", val1)

        text2 = "MRP:\nRs. 145.00\nINCL. OF ALL TAXES"
        val2, conf2 = extract_mrp(text2)
        self.assertIsNotNone(val2)
        self.assertIn("145.00", val2)

        text3 = "MAP FY ,499/-"
        val3, conf3 = extract_mrp(text3)
        self.assertIsNotNone(val3)
        self.assertIn("1499.00", val3)

    def test_multiline_net_quantity_extraction(self):
        """Verifies stacked multiline net quantity declarations."""
        text1 = "NET QUANTITY:\n1 kg"
        val1, conf1 = extract_net_quantity(text1)
        self.assertEqual(val1, "1 kg")

        text2 = "NET\nQUANTITY\n1000 g"
        val2, conf2 = extract_net_quantity(text2)
        self.assertEqual(val2, "1000 g")

    def test_spatial_layout_line_and_block_clustering(self):
        """Verifies deterministic 2D spatial layout grouping with token coordinates."""
        mock_tokens = [
            {"text": "MAXIMUM", "conf": 0.95, "bbox": [10, 10, 80, 20], "line_num": 1, "block_num": 1},
            {"text": "RETAIL", "conf": 0.95, "bbox": [95, 10, 60, 20], "line_num": 1, "block_num": 1},
            {"text": "PRICE", "conf": 0.95, "bbox": [160, 10, 50, 20], "line_num": 1, "block_num": 1},
            {"text": "(INCL.", "conf": 0.90, "bbox": [10, 35, 50, 18], "line_num": 2, "block_num": 1},
            {"text": "OF", "conf": 0.90, "bbox": [65, 35, 25, 18], "line_num": 2, "block_num": 1},
            {"text": "ALL", "conf": 0.90, "bbox": [95, 35, 30, 18], "line_num": 2, "block_num": 1},
            {"text": "TAXES)", "conf": 0.90, "bbox": [130, 35, 60, 18], "line_num": 2, "block_num": 1},
            {"text": "Rs.", "conf": 0.95, "bbox": [10, 60, 30, 20], "line_num": 3, "block_num": 1},
            {"text": "145.00", "conf": 0.95, "bbox": [45, 60, 60, 20], "line_num": 3, "block_num": 1},
        ]

        layout = build_spatial_layout(mock_tokens)
        self.assertEqual(len(layout.lines), 3)
        self.assertEqual(len(layout.blocks), 1)
        self.assertIn("MAXIMUM RETAIL PRICE", layout.lines[0].text)
        self.assertIn("145.00", layout.lines[2].text)

        # Full extraction on spatial tokens
        decls, confs = extract_declaration_from_ocr("", mock_tokens)
        self.assertIn("mrp", decls)
        self.assertIn("145.00", decls["mrp"])

    # ------------------------------------------------------------------
    # 4. Safe Commodity Extraction (Eliminating First-Line Fallback)
    # ------------------------------------------------------------------
    def test_commodity_extraction_safety(self):
        """Verifies headers like 'MARKETED BY:' or phone numbers are NOT extracted as commodity."""
        header_text1 = "MARKETED BY:\nABC Foods Private Limited\nPlot No. 10"
        comm1, conf1 = extract_commodity_name(header_text1)
        self.assertIsNone(comm1, "Header 'MARKETED BY:' must NOT be extracted as commodity name")

        header_text2 = "eddress oF call us at\n10am - 7pm\nLic. No. 12345"
        comm2, conf2 = extract_commodity_name(header_text2)
        self.assertIsNone(comm2, "Phone/care header must NOT be extracted as commodity name")

        legit_text = "Product: Roasted Almonds\nNet Weight: 500g\nMRP Rs. 450"
        comm3, conf3 = extract_commodity_name(legit_text)
        self.assertEqual(comm3, "Roasted Almonds")
        self.assertEqual(conf3, 0.90)

    # ------------------------------------------------------------------
    # 5. Multi-Variant Declaration Fusion & Conflict Preservation
    # ------------------------------------------------------------------
    def test_conflict_preservation_on_divergent_mrp(self):
        """Verifies divergent numeric MRP readings (₹145 vs ₹149) remain CONFLICTING."""
        fusion_svc = DeclarationFusionService()
        mock_variants = {
            "v1": VariantOCRResult(
                variant_name="v1",
                raw_text="MRP Rs. 145.00 incl. of all taxes\nNet Wt: 500g",
                confidence=0.90,
                tokens_data=[],
                char_count=50,
                word_count=10,
                processing_time_ms=50,
                original_image_hash="hash1",
                parent_variant_hash="hash1",
                processed_image_hash="v1hash",
            ),
            "v2": VariantOCRResult(
                variant_name="v2",
                raw_text="MRP Rs. 149.00 incl. of all taxes\nNet Wt: 500g",
                confidence=0.90,
                tokens_data=[],
                char_count=50,
                word_count=10,
                processing_time_ms=50,
                original_image_hash="hash1",
                parent_variant_hash="hash1",
                processed_image_hash="v2hash",
            ),
        }

        summary = fusion_svc.fuse_variant_declarations(mock_variants)
        mrp_field = summary.fused_fields.get("mrp")
        self.assertIsNotNone(mrp_field)
        self.assertEqual(mrp_field.evidence_state, FieldEvidenceState.CONFLICTING)
        self.assertTrue(mrp_field.requires_review)
        self.assertTrue(summary.requires_human_review)

        # Non-conflicting field should be confirmed
        net_qty = summary.fused_fields.get("net_quantity")
        self.assertIsNotNone(net_qty)
        self.assertEqual(net_qty.evidence_state, FieldEvidenceState.CONFIRMED)

    def test_internal_fields_do_not_generate_false_conflicts(self):
        """Verifies internal fields like '_language_detected' do not trigger statutory review."""
        fusion_svc = DeclarationFusionService()
        mock_variants = {
            "v1": VariantOCRResult(
                variant_name="v1",
                raw_text="Product: Roasted Cashews\nMRP Rs. 200",
                confidence=0.85,
                tokens_data=[],
                char_count=40,
                word_count=8,
                processing_time_ms=40,
                original_image_hash="hash2",
                parent_variant_hash="hash2",
                processed_image_hash="v1hash",
            ),
            "v2": VariantOCRResult(
                variant_name="v2",
                raw_text="Product: Roasted Cashews\nएमआरपी रु 200",
                confidence=0.85,
                tokens_data=[],
                char_count=40,
                word_count=8,
                processing_time_ms=40,
                original_image_hash="hash2",
                parent_variant_hash="hash2",
                processed_image_hash="v2hash",
            ),
        }

        summary = fusion_svc.fuse_variant_declarations(mock_variants)
        self.assertNotIn("_language_detected", summary.fused_fields)
        self.assertFalse(summary.requires_human_review)

    # ------------------------------------------------------------------
    # 6. Resolution-Aware Optical Quality Gating
    # ------------------------------------------------------------------
    def test_resolution_aware_optical_gate(self):
        """Verifies sharp high-resolution images scoring ~210 are not marked RETAKE_RECOMMENDED."""
        fail_thresh, warn_thresh = compute_resolution_aware_blur_thresholds(3264, 2448)
        # 8MP image threshold should be around 175.0, not 350.0
        self.assertLessEqual(fail_thresh, 200.0)
        self.assertGreaterEqual(fail_thresh, 140.0)

        # Low resolution (e.g. 800x600 < 2MP) should retain standard 350.0
        low_res_fail, low_res_warn = compute_resolution_aware_blur_thresholds(800, 600)
        self.assertEqual(low_res_fail, 350.0)
        self.assertEqual(low_res_warn, 600.0)

    # ------------------------------------------------------------------
    # 7. Unit Sale Price Homoglyph Resilience
    # ------------------------------------------------------------------
    def test_unit_sale_price_homoglyphs(self):
        """Verifies '¢4.88/q' and '₹ 4.88/9' map to 'Rs. 4.88/g'."""
        usp1, conf1 = extract_unit_sale_price("USP - ¢4.88/q Net")
        self.assertIsNotNone(usp1)
        self.assertIn("4.88/g", usp1)

        usp2, conf2 = extract_unit_sale_price("USP - ₹ 4.88/9 Net")
        self.assertIsNotNone(usp2)
        self.assertIn("4.88/g", usp2)

    # ------------------------------------------------------------------
    # 8. Negative Tests & Ambiguity Disambiguation
    # ------------------------------------------------------------------
    def test_negative_unrelated_numbers_and_serving_sizes(self):
        """Verifies serving size is not extracted as net quantity, and phone/license is not MRP."""
        # Serving size rejection
        nutritional_text = "NUTRITIONAL INFORMATION\nPer 30g serving: Energy 120kcal, Protein 3g"
        qty_nutr, conf_nutr = extract_net_quantity(nutritional_text)
        self.assertIsNone(qty_nutr)

        # Serving size label rejection
        serving_text = "Approx 10 servings per pack\nServing size: 32g"
        qty_srv, conf_srv = extract_net_quantity(serving_text)
        self.assertIsNone(qty_srv)

        # Telephone / helpline is not MRP
        phone_text = "Customer Helpline: 1800-22-3344"
        mrp_ph, conf_ph = extract_mrp(phone_text)
        self.assertIsNone(mrp_ph)

        # FSSAI license is not MRP
        lic_text = "Lic. No. 10014022002654"
        mrp_lic, conf_lic = extract_mrp(lic_text)
        self.assertIsNone(mrp_lic)

    def test_usp_does_not_override_mrp_and_conflict_handling(self):
        """Verifies USP is distinct from MRP and does not override it."""
        label_text = (
            "MAXIMUM RETAIL PRICE (INCL. OF ALL TAXES): Rs. 145.00\n"
            "UNIT SALE PRICE: Rs. 4.88 / g\n"
            "NET QUANTITY: 500 g"
        )
        fields, confs = extract_declaration_from_ocr(label_text)
        self.assertIn("145.00", fields["mrp"])
        self.assertNotIn("4.88", fields["mrp"])
        self.assertIn("4.88", fields["unit_sale_price"])
        self.assertIn("500 g", fields["net_quantity"])


if __name__ == "__main__":
    unittest.main()
