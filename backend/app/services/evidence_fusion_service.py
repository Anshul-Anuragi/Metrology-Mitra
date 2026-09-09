"""
Phase 4.3 Sub-Batch 4 — Unified Evidence Fusion Service
======================================================
Synthesizes all multi-modal perception streams:
  1. Optical Quality Assessment (blur, glare, resolution gating)
  2. Multi-Stage Deterministic Preprocessing Derivatives
  3. Multi-Variant OCR Token Stability & Consensus
  4. Multi-Variant Barcode Quorum Decoding & Master Catalog Lookup
  5. Statutory Declaration Fusion & Conflict Resolution
  6. Physical Scale Weight Verification (when scale data is present)

Architectural Invariants:
1. Zero Autonomous Adjudication: The legal rule engine remains the sole authority
   for statutory verdicts (COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW). The evidence
   fusion layer produces verified, structured perception evidence with uncertainty.
2. Non-Judicial & Non-Certified: Serves technical repeatability and auditability;
   does not constitute statutory certification under the Legal Metrology Act, 2009.
3. Explicit Review Escalation: Any optical failure, OCR instability, declaration
   divergence, or physical weight anomaly raises requires_human_review = True with
   human_review_reasons.
"""

import datetime
import hashlib
import io
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from app.services.barcode_service import (
    BarcodeQuorumResult,
    decode_barcodes_multi_variant,
    lookup_master_catalog,
)
from app.services.image_preprocessing_service import (
    ALL_STANDARD_VARIANTS,
    PreprocessingConfig,
    PreprocessingResult,
    image_preprocessing_service,
)
from app.services.ocr.declaration_fusion import (
    FieldEvidenceState,
    FusedDeclarationSummary,
    declaration_fusion_service,
)
from app.services.ocr.multi_variant_ocr import (
    MultiVariantOCRResponse,
    multi_variant_ocr_orchestrator,
)


@dataclass
class PhysicalScaleCheckResult:
    declared_net_quantity_str: Optional[str]
    declared_quantity_numeric: Optional[float]
    declared_unit: Optional[str]
    observed_weight_grams: Optional[float]
    tare_weight_grams: Optional[float]
    net_observed_grams: Optional[float]
    discrepancy_grams: Optional[float]
    percentage_error: Optional[float]
    is_shortfall: bool
    scale_device_id: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedEvidencePacket:
    """
    Comprehensive multi-modal evidence packet delivered to the Legal Metrology rule engine.
    """
    original_image_hash: str
    optical_quality: Dict[str, Any]
    preprocessing_summary: Dict[str, Any]
    ocr_consensus: Dict[str, Any]
    barcode_quorum: Dict[str, Any]
    fused_declarations: Dict[str, Any]
    physical_scale_verification: Optional[Dict[str, Any]]
    overall_evidence_quality: str  # HIGH, MODERATE, DEGRADED, INSUFFICIENT
    requires_human_review: bool
    human_review_reasons: List[str]
    provenance_chain: Dict[str, Any]
    created_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceFusionService:
    """
    Unified coordinator synthesizing optical quality, preprocessing derivatives,
    multi-variant OCR, barcode quorum, and declaration fusion into an immutable
    evidence packet.
    """

    def __init__(
        self,
        preprocessor=None,
        ocr_orchestrator=None,
        fusion_service=None,
    ):
        self.preprocessor = preprocessor or image_preprocessing_service
        self.ocr_orchestrator = ocr_orchestrator or multi_variant_ocr_orchestrator
        self.fusion_service = fusion_service or declaration_fusion_service

    def _compute_raw_hash(self, image_input: Union[bytes, Path, str, Image.Image]) -> Tuple[str, bytes]:
        """Extracts raw bytes and SHA-256 master hash."""
        if isinstance(image_input, (bytes, bytearray)):
            raw_bytes = bytes(image_input)
            return hashlib.sha256(raw_bytes).hexdigest(), raw_bytes
        elif isinstance(image_input, (Path, str)):
            p = Path(image_input)
            if p.exists():
                with open(p, "rb") as f:
                    raw_bytes = f.read()
                return hashlib.sha256(raw_bytes).hexdigest(), raw_bytes
            raise FileNotFoundError(f"Image path not found: {image_input}")
        elif isinstance(image_input, Image.Image):
            buf = io.BytesIO()
            image_input.save(buf, format="PNG")
            raw_bytes = buf.getvalue()
            return hashlib.sha256(raw_bytes).hexdigest(), raw_bytes
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

    def _cross_check_physical_scale(
        self,
        declared_net_qty_str: Optional[str],
        physical_scale_data: Optional[Dict[str, Any]],
    ) -> Optional[PhysicalScaleCheckResult]:
        """
        Cross-checks declared net quantity against physical weighing scale telemetry.
        """
        if not physical_scale_data or not declared_net_qty_str:
            return None

        observed_gross = physical_scale_data.get("gross_weight_grams")
        tare = physical_scale_data.get("tare_weight_grams", 0.0)
        device_id = physical_scale_data.get("scale_device_id")

        if observed_gross is None:
            return None

        net_observed = max(0.0, float(observed_gross) - float(tare))

        # Parse declared quantity in grams
        declared_num = None
        declared_unit = None
        import re
        m = re.search(r"(\d+(?:\.\d+)?)\s*(g|kg|gm|grams)", declared_net_qty_str, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            declared_unit = "g" if "g" in unit and "k" not in unit else "kg"
            declared_num = val * 1000.0 if declared_unit == "kg" else val

        if declared_num is None or declared_num <= 0:
            return PhysicalScaleCheckResult(
                declared_net_quantity_str=declared_net_qty_str,
                declared_quantity_numeric=None,
                declared_unit=None,
                observed_weight_grams=observed_gross,
                tare_weight_grams=tare,
                net_observed_grams=net_observed,
                discrepancy_grams=None,
                percentage_error=None,
                is_shortfall=False,
                scale_device_id=device_id,
                notes="Declared quantity unit not directly comparable in weight grams",
            )

        discrepancy = net_observed - declared_num
        pct_err = (discrepancy / declared_num) * 100.0
        is_shortfall = discrepancy < 0.0

        return PhysicalScaleCheckResult(
            declared_net_quantity_str=declared_net_qty_str,
            declared_quantity_numeric=declared_num,
            declared_unit="g",
            observed_weight_grams=observed_gross,
            tare_weight_grams=tare,
            net_observed_grams=net_observed,
            discrepancy_grams=round(discrepancy, 2),
            percentage_error=round(pct_err, 2),
            is_shortfall=is_shortfall,
            scale_device_id=device_id,
            notes="Physical scale verification completed under Second Schedule net quantity tolerances",
        )

    async def fuse_evidence(
        self,
        image_input: Union[bytes, Path, str, Image.Image],
        quality_assessment: Optional[Any] = None,
        physical_scale_data: Optional[Dict[str, Any]] = None,
        variant_names: Optional[List[str]] = None,
    ) -> UnifiedEvidencePacket:
        """
        Executes end-to-end multi-modal evidence fusion.
        """
        master_hash, raw_bytes = self._compute_raw_hash(image_input)
        review_reasons: List[str] = []

        # 1. Quality Assessment Synthesis
        quality_summary: Dict[str, Any] = {}
        if quality_assessment is not None:
            if hasattr(quality_assessment, "to_dict"):
                quality_summary = quality_assessment.to_dict()
            elif isinstance(quality_assessment, dict):
                quality_summary = quality_assessment
            else:
                quality_summary = {
                    "is_acceptable": getattr(quality_assessment, "is_acceptable", True),
                    "blur_score": getattr(quality_assessment, "blur_score", None),
                    "glare_ratio": getattr(quality_assessment, "glare_ratio", None),
                    "gate_decision": str(getattr(quality_assessment, "gate_decision", "REVIEW")),
                    "overall_status": str(getattr(quality_assessment, "overall_status", "WARNING")),
                    "actionable_reasons": getattr(quality_assessment, "actionable_reasons", []),
                }

            if not quality_summary.get("is_acceptable", True):
                gate_dec = quality_summary.get("gate_decision") or quality_summary.get("overall_status") or "REVIEW"
                action_reasons = quality_summary.get("actionable_reasons") or []
                reasons_str = f" ({'; '.join(action_reasons)})" if action_reasons else ""
                review_reasons.append(
                    f"Optical quality gating flagged image: gate_decision={gate_dec}{reasons_str}"
                )

        # 2. Multi-Variant Preprocessing
        selected_variants = variant_names or self.preprocessor.select_adaptive_variants(quality_assessment)
        variants = self.preprocessor.preprocess_image(raw_bytes, variants=selected_variants)

        provenance_chain: Dict[str, Any] = {
            "raw_master_hash": master_hash,
            "variants_hashes": {v.variant_name: v.processed_image_hash for v in variants},
            "variants_parentage": {v.variant_name: v.parent_variant_hash for v in variants},
        }

        preprocessing_summary = {
            "total_variants_generated": len(variants),
            "variant_names": [v.variant_name for v in variants],
            "selection_strategy": "adaptive" if not variant_names else "manual",
        }

        # 3. Multi-Variant Barcode Quorum
        barcode_quorum: BarcodeQuorumResult = decode_barcodes_multi_variant(variants)
        if barcode_quorum.has_conflict:
            review_reasons.append("Conflicting barcode symbologies detected across image derivatives")

        # 4. Multi-Variant OCR Consensus
        ocr_response: MultiVariantOCRResponse = await self.ocr_orchestrator.execute_multi_variant_ocr(variants)
        ocr_has_conflicts = bool(ocr_response.consensus.detected_conflicts)
        if ocr_has_conflicts:
            for c in ocr_response.consensus.detected_conflicts:
                desc = c.get("description", "OCR conflict detected across variants")
                if desc not in review_reasons:
                    review_reasons.append(desc)

        # 5. Multi-Variant Declaration Fusion
        declaration_summary: FusedDeclarationSummary = self.fusion_service.fuse_variant_declarations(
            ocr_response.variants_results
        )
        if declaration_summary.requires_human_review:
            for r in declaration_summary.review_reasons:
                if r not in review_reasons:
                    review_reasons.append(r)

        # 6. Physical Scale Verification
        net_qty_field = declaration_summary.fused_fields.get("net_quantity")
        declared_qty_val = net_qty_field.fused_value if net_qty_field else None
        scale_result = self._cross_check_physical_scale(declared_qty_val, physical_scale_data)

        if scale_result and scale_result.is_shortfall:
            if scale_result.percentage_error and scale_result.percentage_error < -2.0:
                review_reasons.append(
                    f"Physical scale shortfall detected: {scale_result.percentage_error:.1f}% below declared net quantity"
                )

        # Overall Evidence Quality Rating
        if len(review_reasons) == 0 and declaration_summary.confirmed_count >= 3:
            overall_quality = "HIGH"
        elif declaration_summary.confirmed_count >= 2:
            overall_quality = "MODERATE"
        elif declaration_summary.total_fields_extracted >= 1:
            overall_quality = "DEGRADED"
        else:
            overall_quality = "INSUFFICIENT"

        requires_human_review = (
            len(review_reasons) > 0
            or declaration_summary.has_conflicts
            or ocr_has_conflicts
            or overall_quality == "INSUFFICIENT"
        )

        return UnifiedEvidencePacket(
            original_image_hash=master_hash,
            optical_quality=quality_summary,
            preprocessing_summary=preprocessing_summary,
            ocr_consensus=ocr_response.to_dict(),
            barcode_quorum=barcode_quorum.to_dict(),
            fused_declarations=declaration_summary.to_dict(),
            physical_scale_verification=scale_result.to_dict() if scale_result else None,
            overall_evidence_quality=overall_quality,
            requires_human_review=requires_human_review,
            human_review_reasons=review_reasons,
            provenance_chain=provenance_chain,
            created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )


# Global singleton instance
evidence_fusion_service = EvidenceFusionService()
