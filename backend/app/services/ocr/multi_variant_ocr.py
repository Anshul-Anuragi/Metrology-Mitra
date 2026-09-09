"""
Phase 4.3 Sub-Batch 2 — Multi-Variant OCR Orchestrator & Consensus Engine
========================================================================
Orchestrates multi-variant image preprocessing with local Tesseract OCR 5.
Executes OCR across deterministic derivative variants, extracts token confidences,
tracks cryptographic parent/source hashes, and builds deterministic evidence consensus.

Key Architectural Invariants:
1. Master Raw Preservation: Ingress raw image bytes and SHA-256 remain immutable.
2. Independent Derivative Execution: Each variant is processed independently;
   no OCR result overwrites another.
3. Provenance Retention: Every variant OCR result retains its variant identity,
   processed image hash, parent hash, and original raw master hash.
4. Deterministic Consensus: Consensus aggregation identifies stable tokens across
   variants, computes stability ratios, and detects token/numeric divergences.
5. Non-Judicial Notice: OCR consensus produces perception evidence and confidence metrics only.
   Deterministic legal rule engine remains the sole statutory authority.
"""

import asyncio
import datetime
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from PIL import Image

from app.services.image_preprocessing_service import (
    ALL_STANDARD_VARIANTS,
    ImagePreprocessingService,
    PreprocessingConfig,
    PreprocessingResult,
    PreprocessingVariantName,
    image_preprocessing_service,
)
from app.services.ocr.base import OCRResponseData
from app.services.ocr.tesseract_ocr import TesseractOCRProvider, ocr_service


@dataclass
class VariantOCRResult:
    """Individual OCR result for a specific preprocessing derivative variant."""
    variant_name: str
    raw_text: str
    confidence: Optional[float]
    tokens_data: List[Dict[str, Any]]
    char_count: int
    word_count: int
    processing_time_ms: int
    original_image_hash: str
    parent_variant_hash: str
    processed_image_hash: str
    created_at_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_name": self.variant_name,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "tokens_count": len(self.tokens_data),
            "char_count": self.char_count,
            "word_count": self.word_count,
            "processing_time_ms": self.processing_time_ms,
            "original_image_hash": self.original_image_hash,
            "parent_variant_hash": self.parent_variant_hash,
            "processed_image_hash": self.processed_image_hash,
            "created_at_utc": self.created_at_utc,
        }


@dataclass
class TokenStability:
    """Consensus stability assessment for an individual token/word across variants."""
    token: str
    normalized_token: str
    frequency: int
    total_variants: int
    variant_sources: List[str]
    mean_confidence: float
    is_stable: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OCRConsensusSummary:
    """Consensus aggregation summary over all executed variants."""
    primary_variant: str
    consensus_text: str
    mean_confidence_across_variants: float
    stable_token_count: int
    unstable_token_count: int
    stability_ratio: float
    variants_executed: List[str]
    detected_conflicts: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiVariantOCRResponse:
    """Unified response containing all variant OCR results and consensus analysis."""
    original_image_hash: str
    variants_results: Dict[str, VariantOCRResult]
    consensus: OCRConsensusSummary
    stable_tokens: List[TokenStability]
    total_duration_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_image_hash": self.original_image_hash,
            "variants_results": {k: v.to_dict() for k, v in self.variants_results.items()},
            "consensus": self.consensus.to_dict(),
            "stable_tokens_sample": [t.to_dict() for t in self.stable_tokens[:20]],
            "total_duration_ms": self.total_duration_ms,
        }


class MultiVariantOCROrchestrator:
    """
    Orchestrates multi-variant preprocessing and OCR execution with consensus aggregation.
    """

    def __init__(
        self,
        ocr_provider: Optional[TesseractOCRProvider] = None,
        preprocessor: Optional[ImagePreprocessingService] = None,
    ):
        self.ocr_provider = ocr_provider or (ocr_service if isinstance(ocr_service, TesseractOCRProvider) else TesseractOCRProvider())
        self.preprocessor = preprocessor or image_preprocessing_service

    def _normalize_token_text(self, text: str) -> str:
        """Normalizes token text for consensus matching (lowercase, stripped punctuation)."""
        clean = re.sub(r"[^a-zA-Z0-9\s\u0900-\u097F]", "", text).strip().lower()
        return clean

    def analyze_token_stability(
        self, variant_results: List[VariantOCRResult]
    ) -> List[TokenStability]:
        """
        Analyzes stability of tokens across all executed variants.
        Tokens appearing in >= 2 variants or having high confidence (>0.85) are considered stable.
        """
        total_variants = len(variant_results)
        if total_variants == 0:
            return []

        # Token map: norm_token -> {tokens: Counter, confs: List, variants: Set}
        token_stats: Dict[str, Dict[str, Any]] = {}

        for vr in variant_results:
            for td in vr.tokens_data:
                raw_tok = td.get("text", "").strip()
                if not raw_tok or len(raw_tok) < 2:
                    continue
                norm_tok = self._normalize_token_text(raw_tok)
                if not norm_tok:
                    continue

                conf = td.get("conf")
                conf_val = float(conf) if conf is not None else 0.50

                if norm_tok not in token_stats:
                    token_stats[norm_tok] = {
                        "raw_forms": {},
                        "confidences": [],
                        "variants": set(),
                    }

                entry = token_stats[norm_tok]
                entry["raw_forms"][raw_tok] = entry["raw_forms"].get(raw_tok, 0) + 1
                entry["confidences"].append(conf_val)
                entry["variants"].add(vr.variant_name)

        stability_list: List[TokenStability] = []
        for norm_tok, data in token_stats.items():
            freq = len(data["variants"])
            # Best raw form is the most frequent
            best_raw = max(data["raw_forms"].items(), key=lambda x: x[1])[0]
            confs = data["confidences"]
            mean_conf = round(sum(confs) / len(confs), 4) if confs else 0.0

            # Stability heuristic:
            # Multi-variant agreement (freq >= 2) OR single variant with >= 0.85 confidence
            is_stable = (freq >= 2) or (mean_conf >= 0.85 and total_variants == 1)

            stability_list.append(
                TokenStability(
                    token=best_raw,
                    normalized_token=norm_tok,
                    frequency=freq,
                    total_variants=total_variants,
                    variant_sources=sorted(list(data["variants"])),
                    mean_confidence=mean_conf,
                    is_stable=is_stable,
                )
            )

        # Sort stable first, then by frequency desc, then confidence desc
        stability_list.sort(key=lambda t: (t.is_stable, t.frequency, t.mean_confidence), reverse=True)
        return stability_list

    def detect_conflicts(
        self, variant_results: List[VariantOCRResult]
    ) -> List[Dict[str, Any]]:
        """
        Detects conflicting readings across variants (especially price, quantity, and date patterns).
        """
        conflicts: List[Dict[str, Any]] = []

        # 1. Price / MRP conflicts
        price_patterns = [
            r"(?i)\b(?:MRP|M\.R\.P\.?)\s*[:.-]?\s*(?:Rs\.?|₹|INR)?\s*(\d+(?:\.\d{1,2})?)",
            r"(?i)\b(?:Rs\.?|₹)\s*(\d+(?:\.\d{1,2})?)",
        ]
        prices_found: Dict[str, Set[str]] = {}  # price_val -> set of variants
        for vr in variant_results:
            for pat in price_patterns:
                matches = re.findall(pat, vr.raw_text)
                for m in matches:
                    val = str(m).strip()
                    prices_found.setdefault(val, set()).add(vr.variant_name)

        if len(prices_found) > 1:
            # Multiple differing price candidates detected
            conflicts.append({
                "field_hint": "MRP",
                "severity": "HIGH",
                "description": "Divergent MRP readings detected across preprocessing variants.",
                "candidate_values": {val: sorted(list(vars_)) for val, vars_ in prices_found.items()},
                "requires_human_review": True,
            })

        # 2. Net Quantity numeric conflicts
        qty_pattern = r"(?i)\b(\d+(?:\.\d+)?)\s*(?:g|kg|ml|l|gm|grams)\b"
        qtys_found: Dict[str, Set[str]] = {}
        for vr in variant_results:
            matches = re.findall(qty_pattern, vr.raw_text)
            for m in matches:
                val = str(m).strip()
                qtys_found.setdefault(val, set()).add(vr.variant_name)

        if len(qtys_found) > 1:
            conflicts.append({
                "field_hint": "NET_QUANTITY",
                "severity": "HIGH",
                "description": "Divergent Net Quantity numeric readings detected across variants.",
                "candidate_values": {val: sorted(list(vars_)) for val, vars_ in qtys_found.items()},
                "requires_human_review": True,
            })

        return conflicts

    def build_consensus(
        self,
        variant_results: List[VariantOCRResult],
        original_hash: str,
    ) -> Tuple[OCRConsensusSummary, List[TokenStability]]:
        """
        Builds deterministic consensus summary across all variant OCR results.
        Selects primary variant based on composite score (word count * mean confidence).
        """
        if not variant_results:
            return (
                OCRConsensusSummary(
                    primary_variant="NONE",
                    consensus_text="",
                    mean_confidence_across_variants=0.0,
                    stable_token_count=0,
                    unstable_token_count=0,
                    stability_ratio=0.0,
                    variants_executed=[],
                    detected_conflicts=[],
                ),
                [],
            )

        # 1. Rank variants to select primary representative
        def variant_score(vr: VariantOCRResult) -> float:
            conf = vr.confidence or 0.1
            words = max(1, vr.word_count)
            # Give slight priority to NORMALIZED_ORIGINAL as baseline if words are comparable
            bonus = 1.1 if vr.variant_name in (
                PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
                PreprocessingVariantName.ORIGINAL.value,
            ) else 1.0
            return words * conf * bonus

        best_variant = max(variant_results, key=variant_score)

        # 2. Compute aggregate mean confidence across all variants
        confs = [vr.confidence for vr in variant_results if vr.confidence is not None]
        overall_conf = round(sum(confs) / len(confs), 4) if confs else 0.0

        # 3. Analyze token stability
        tokens_stability = self.analyze_token_stability(variant_results)
        stable_count = sum(1 for t in tokens_stability if t.is_stable)
        unstable_count = len(tokens_stability) - stable_count
        stability_ratio = round(stable_count / max(1, len(tokens_stability)), 4)

        # 4. Detect conflicts
        conflicts = self.detect_conflicts(variant_results)

        consensus_summary = OCRConsensusSummary(
            primary_variant=best_variant.variant_name,
            consensus_text=best_variant.raw_text,
            mean_confidence_across_variants=overall_conf,
            stable_token_count=stable_count,
            unstable_token_count=unstable_count,
            stability_ratio=stability_ratio,
            variants_executed=[vr.variant_name for vr in variant_results],
            detected_conflicts=conflicts,
        )

        return consensus_summary, tokens_stability

    def _sync_process_variant(
        self,
        prep_res: PreprocessingResult,
    ) -> VariantOCRResult:
        """Synchronously executes Tesseract OCR on a single preprocessing variant."""
        start_time = time.perf_counter()
        ocr_res: OCRResponseData = self.ocr_provider._sync_ocr(prep_res.image)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        words = [w for w in ocr_res.raw_text.split() if w.strip()]
        return VariantOCRResult(
            variant_name=prep_res.variant_name,
            raw_text=ocr_res.raw_text,
            confidence=ocr_res.confidence,
            tokens_data=ocr_res.tokens_data,
            char_count=len(ocr_res.raw_text),
            word_count=len(words),
            processing_time_ms=duration_ms,
            original_image_hash=prep_res.original_image_hash,
            parent_variant_hash=prep_res.parent_variant_hash,
            processed_image_hash=prep_res.processed_image_hash,
        )

    async def process_multi_variant_ocr(
        self,
        image_input: Union[bytes, Path, str, Image.Image],
        config: Optional[PreprocessingConfig] = None,
        quality_result: Optional[Any] = None,
        target_variants: Optional[List[str]] = None,
    ) -> MultiVariantOCRResponse:
        """
        Executes multi-variant preprocessing followed by multi-variant OCR and consensus analysis.
        All variants execute without mutating the source or overwriting sister results.
        """
        total_start = time.perf_counter()
        cfg = config or PreprocessingConfig()

        # 1. Preprocess into requested or quality-adaptive variants
        prep_results: List[PreprocessingResult] = await asyncio.to_thread(
            self.preprocessor.preprocess_image,
            image_input,
            cfg,
            target_variants,
            quality_result,
        )

        if not prep_results:
            raise ValueError("No preprocessing variants generated for input image.")

        original_hash = prep_results[0].original_image_hash

        # 2. Execute OCR on each variant in worker thread
        variant_ocr_results: List[VariantOCRResult] = []
        for pr in prep_results:
            v_res = await asyncio.to_thread(self._sync_process_variant, pr)
            variant_ocr_results.append(v_res)

        # 3. Build consensus aggregation
        consensus, stable_tokens = self.build_consensus(variant_ocr_results, original_hash)

        total_duration_ms = int((time.perf_counter() - total_start) * 1000)
        results_map = {vr.variant_name: vr for vr in variant_ocr_results}

        return MultiVariantOCRResponse(
            original_image_hash=original_hash,
            variants_results=results_map,
            consensus=consensus,
            stable_tokens=stable_tokens,
            total_duration_ms=total_duration_ms,
        )

    async def execute_multi_variant_ocr(
        self,
        variants: List[PreprocessingResult],
    ) -> MultiVariantOCRResponse:
        """
        Executes OCR directly across already generated preprocessing variants.
        """
        total_start = time.perf_counter()
        if not variants:
            raise ValueError("No variants provided for OCR execution.")

        original_hash = variants[0].original_image_hash
        variant_ocr_results: List[VariantOCRResult] = []
        for pr in variants:
            v_res = await asyncio.to_thread(self._sync_process_variant, pr)
            variant_ocr_results.append(v_res)

        consensus, stable_tokens = self.build_consensus(variant_ocr_results, original_hash)
        total_duration_ms = int((time.perf_counter() - total_start) * 1000)
        results_map = {vr.variant_name: vr for vr in variant_ocr_results}

        return MultiVariantOCRResponse(
            original_image_hash=original_hash,
            variants_results=results_map,
            consensus=consensus,
            stable_tokens=stable_tokens,
            total_duration_ms=total_duration_ms,
        )


# Global singleton instance for multi-variant OCR orchestration
multi_variant_ocr_orchestrator = MultiVariantOCROrchestrator()
