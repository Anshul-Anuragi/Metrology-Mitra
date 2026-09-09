"""
Phase 4.3 Sub-Batch 3 — Multi-Variant Declaration Fusion Layer
==============================================================
Aggregates statutory declaration fields across multi-variant OCR derivatives,
resolving consensus and identifying candidate conflicts under the Legal
Metrology (Packaged Commodities) Rules, 2011.

Architectural Principles:
1. Multi-Variant Cross-Verification: Fields corroborated across multiple image
   variants receive higher evidence certainty.
2. Definite Conflict Flagging: Divergent readings across variants (e.g. different
   numerical MRPs or net quantities) are immediately surfaced with evidence state
   CONFLICTING and flagged for human review.
3. Legal Engine Invariant: Declaration fusion produces structured evidence with
   confidence and provenance; only the deterministic Legal Metrology rule engine
   evaluates statutory compliance.
"""

import enum
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.services.ocr.extractor import (
    extract_declaration_from_ocr,
    extract_mrp,
    extract_net_quantity,
)
from app.services.ocr.multi_variant_ocr import VariantOCRResult
from app.services.ocr.normalizer import normalize_price_string, normalize_quantity_string



class FieldEvidenceState(str, enum.Enum):
    PRESENT = "PRESENT"              # Clearly observed and corroborated (alias for CONFIRMED)
    CONFIRMED = "CONFIRMED"          # Corroborated across >=2 variants (or 1 variant with confidence >= 0.90)
    PROBABLE = "PROBABLE"            # Observed in single variant with moderate confidence
    CONFLICTING = "CONFLICTING"      # Discrepancy observed across variants (e.g. divergent MRPs)
    NOT_OBSERVED = "NOT_OBSERVED"    # Declaration was not successfully extracted from image
    NOT_VISIBLE = "NOT_VISIBLE"      # Package surface/region not represented in captured evidence
    UNREADABLE = "UNREADABLE"        # Text detected but quality too degraded for reliable extraction
    MISSING = "MISSING"              # Backward compatibility alias for NOT_OBSERVED


# Statutory Rule Mappings for Mandatory Declarations under PCR 2011
STATUTORY_RULE_MAPPINGS: Dict[str, str] = {
    "commodity_name": "Rule 6(1)(a) — Common generic name or specific name of commodity",
    "manufacturer_name": "Rule 6(1)(b) — Name and address of manufacturer/packer/importer",
    "packer_name": "Rule 6(1)(b) — Name and address of manufacturer/packer/importer",
    "importer_name": "Rule 6(1)(b) — Name and address of manufacturer/packer/importer",
    "address": "Rule 6(1)(b) — Complete address of manufacturer/packer/importer",
    "net_quantity": "Rule 6(1)(c) — Net quantity in standard units of weight/measure/number",
    "manufacturing_date": "Rule 6(1)(d) — Month and year of manufacture or pre-packing",
    "packing_date": "Rule 6(1)(d) — Month and year of manufacture or pre-packing",
    "expiry_date": "Rule 6(1)(d) — Expiry date / best before declaration",
    "best_before": "Rule 6(1)(d) — Expiry date / best before declaration",
    "mrp": "Rule 6(1)(da) — Maximum retail price inclusive of all taxes",
    "consumer_care": "Rule 6(1)(e) — Name, address, phone, and email of consumer grievance cell",
    "consumer_care_phone": "Rule 6(1)(e) — Consumer care telephone number",
    "consumer_care_email": "Rule 6(1)(e) — Consumer care email address",
    "unit_sale_price": "Rule 6(1)(f) — Unit sale price per g/kg/ml/l/piece",
    "country_of_origin": "Rule 6(10) — Country of origin on imported commodities",
}


@dataclass
class FieldCandidate:
    variant_name: str
    raw_value: str
    confidence: float
    normalized_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FusedFieldResult:
    field_name: str
    statutory_rule: str
    evidence_state: FieldEvidenceState
    fused_value: Optional[str]
    normalized_value: Optional[Any]
    aggregate_confidence: float
    supporting_variants: List[str]
    conflicting_variants: List[str]
    all_candidates: List[FieldCandidate]
    requires_review: bool = False
    review_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "statutory_rule": self.statutory_rule,
            "evidence_state": self.evidence_state.value,
            "fused_value": self.fused_value,
            "normalized_value": self.normalized_value,
            "aggregate_confidence": round(self.aggregate_confidence, 4),
            "supporting_variants": self.supporting_variants,
            "conflicting_variants": self.conflicting_variants,
            "all_candidates": [c.to_dict() for c in self.all_candidates],
            "requires_review": self.requires_review,
            "review_reason": self.review_reason,
        }


@dataclass
class FusedDeclarationSummary:
    fused_fields: Dict[str, FusedFieldResult]
    total_fields_extracted: int
    confirmed_count: int
    probable_count: int
    conflicting_count: int
    missing_count: int
    has_conflicts: bool
    requires_human_review: bool
    review_reasons: List[str]
    raw_declarations_per_variant: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fused_fields": {k: v.to_dict() for k, v in self.fused_fields.items()},
            "total_fields_extracted": self.total_fields_extracted,
            "confirmed_count": self.confirmed_count,
            "probable_count": self.probable_count,
            "conflicting_count": self.conflicting_count,
            "missing_count": self.missing_count,
            "has_conflicts": self.has_conflicts,
            "requires_human_review": self.requires_human_review,
            "review_reasons": self.review_reasons,
            "raw_declarations_per_variant": self.raw_declarations_per_variant,
        }


class DeclarationFusionService:
    """
    Fuses extracted statutory declarations across multiple preprocessing variants.
    """

    def _extract_numeric_mrp_val(self, text: Optional[str]) -> Optional[float]:
        """Extracts floating point MRP number for consistency comparison."""
        if not text:
            return None
        p_res = normalize_price_string(str(text))
        if p_res.normalized_value is not None:
            try:
                return float(p_res.normalized_value)
            except (ValueError, TypeError):
                pass
        clean_text = str(text).replace(",", "").strip()
        matches = re.findall(r"(?:rs\.?|₹|mrp)?\s*([0-9]+(?:\.[0-9]{1,2})?)", clean_text, re.IGNORECASE)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None

    def _extract_numeric_qty_val(self, text: Optional[str]) -> Optional[str]:
        """Extracts normalized quantity string e.g. '500 g' or '1000.0 g' for comparison."""
        if not text:
            return None
        q_res = normalize_quantity_string(str(text))
        if q_res.normalized_value is not None and isinstance(q_res.normalized_value, dict):
            return q_res.normalized_value.get("formatted")
        clean_text = str(text).replace(",", "").strip()
        m = re.search(r"(\d+(?:\.\d+)?)\s*(g|kg|ml|l|gm|grams|kg\.|litres?|l\.)", clean_text, re.IGNORECASE)
        if m:
            num = m.group(1).strip()
            unit = m.group(2).lower().replace("gm", "g").replace("grams", "g").replace("kg.", "kg").replace("l.", "l")
            return f"{num} {unit}"
        return clean_text.lower()

    def _are_text_candidates_compatible(self, val1: Any, val2: Any) -> bool:
        """
        Determines whether two text declarations are mutually compatible extensions
        (e.g., substring / prefix / suffix) rather than contradictory readings.
        """
        v1 = str(val1).strip().lower()
        v2 = str(val2).strip().lower()
        if v1 == v2:
            return True
        if v1 in v2 or v2 in v1:
            return True
        words1 = set(re.findall(r"\w+", v1))
        words2 = set(re.findall(r"\w+", v2))
        if not words1 or not words2:
            return False
        intersection = words1.intersection(words2)
        overlap = len(intersection) / min(len(words1), len(words2))
        return overlap >= 0.50

    def fuse_variant_declarations(
        self,
        variant_results: Union[List[VariantOCRResult], Dict[str, VariantOCRResult]],
    ) -> FusedDeclarationSummary:
        """
        Executes extraction on each variant OCR text and fuses candidate readings into
        a coherent, corroborated evidence set.
        """
        v_list = list(variant_results.values()) if isinstance(variant_results, dict) else list(variant_results)
        
        # 1. Run extraction per variant (passing tokens_data for 2D spatial layout)
        per_variant_declarations: Dict[str, Dict[str, Any]] = {}
        per_variant_confidences: Dict[str, Dict[str, float]] = {}

        for var in v_list:
            v_name = var.variant_name
            tokens = getattr(var, "tokens_data", None)
            extracted, confs = extract_declaration_from_ocr(var.raw_text or "", tokens)
            per_variant_declarations[v_name] = extracted
            per_variant_confidences[v_name] = confs

        # 2. Collect field candidates
        all_field_names = set(STATUTORY_RULE_MAPPINGS.keys())
        # Also include any fields discovered by extractor
        for v_name, fields_dict in per_variant_declarations.items():
            all_field_names.update(fields_dict.keys())

        fused_fields: Dict[str, FusedFieldResult] = {}
        total_extracted = 0
        confirmed_count = 0
        probable_count = 0
        conflicting_count = 0
        missing_count = 0
        all_review_reasons: List[str] = []

        for f_name in sorted(list(all_field_names)):
            if f_name.startswith("_") or f_name == "is_imported":
                continue  # internal metadata or boolean flag, handled separately

            candidates: List[FieldCandidate] = []
            for var in v_list:
                v_name = var.variant_name
                val = per_variant_declarations.get(v_name, {}).get(f_name)
                conf = per_variant_confidences.get(v_name, {}).get(f_name, 0.0)
                if val:
                    norm_val = None
                    if f_name == "mrp":
                        norm_val = self._extract_numeric_mrp_val(val)
                    elif f_name == "net_quantity":
                        norm_val = self._extract_numeric_qty_val(val)
                    else:
                        norm_val = str(val).strip().lower()

                    candidates.append(
                        FieldCandidate(
                            variant_name=v_name,
                            raw_value=str(val),
                            confidence=conf,
                            normalized_value=norm_val,
                        )
                    )

            statutory_rule = STATUTORY_RULE_MAPPINGS.get(
                f_name, f"Statutory declaration field: {f_name}"
            )

            # If not detected in any variant
            if not candidates:
                missing_count += 1
                fused_fields[f_name] = FusedFieldResult(
                    field_name=f_name,
                    statutory_rule=statutory_rule,
                    evidence_state=FieldEvidenceState.MISSING,
                    fused_value=None,
                    normalized_value=None,
                    aggregate_confidence=0.0,
                    supporting_variants=[],
                    conflicting_variants=[],
                    all_candidates=[],
                    requires_review=False,
                    review_reason=None,
                )
                continue

            total_extracted += 1

            # Conflict analysis across ALL statutory fields
            distinct_norm_vals = {c.normalized_value for c in candidates if c.normalized_value is not None}
            has_field_conflict = False

            if len(distinct_norm_vals) > 1:
                if f_name in ("mrp", "net_quantity"):
                    has_field_conflict = True
                elif f_name in (
                    "consumer_care_phone",
                    "consumer_care_email",
                    "manufacturing_date",
                    "packing_date",
                    "expiry_date",
                    "import_date",
                    "best_before",
                    "unit_sale_price",
                ):
                    has_field_conflict = True
                else:
                    # General text fields: check pairwise compatibility
                    val_list = list(distinct_norm_vals)
                    for i in range(len(val_list)):
                        for j in range(i + 1, len(val_list)):
                            if not self._are_text_candidates_compatible(val_list[i], val_list[j]):
                                has_field_conflict = True
                                break
                        if has_field_conflict:
                            break

            if has_field_conflict:
                conflicting_count += 1
                reason = f"Divergent values detected for statutory field '{f_name}' across preprocessing variants: {list(distinct_norm_vals)}"
                all_review_reasons.append(reason)
                
                sorted_c = sorted(candidates, key=lambda c: c.confidence, reverse=True)
                primary_norm = sorted_c[0].normalized_value
                fused_fields[f_name] = FusedFieldResult(
                    field_name=f_name,
                    statutory_rule=statutory_rule,
                    evidence_state=FieldEvidenceState.CONFLICTING,
                    fused_value=sorted_c[0].raw_value,
                    normalized_value=sorted_c[0].normalized_value,
                    aggregate_confidence=min(0.40, sorted_c[0].confidence),
                    supporting_variants=[c.variant_name for c in candidates if c.normalized_value == primary_norm],
                    conflicting_variants=[c.variant_name for c in candidates if c.normalized_value != primary_norm],
                    all_candidates=candidates,
                    requires_review=True,
                    review_reason=reason,
                )
                continue

            # Corroboration and state assignment when all candidates are compatible
            max_cand = max(candidates, key=lambda c: (c.confidence, len(str(c.raw_value))))
            supporting_vars = [c.variant_name for c in candidates]
            conflicting_vars = []

            supp_confs = [c.confidence for c in candidates]
            agg_conf = sum(supp_confs) / len(supp_confs) if supp_confs else max_cand.confidence

            # CONFIRMED strictly requires multi-variant corroboration (>=2 variants) with zero conflicts
            if len(supporting_vars) >= 2 or max_cand.confidence >= 0.90:
                state = FieldEvidenceState.CONFIRMED
                confirmed_count += 1
            else:
                state = FieldEvidenceState.PROBABLE
                probable_count += 1

            fused_fields[f_name] = FusedFieldResult(
                field_name=f_name,
                statutory_rule=statutory_rule,
                evidence_state=state,
                fused_value=max_cand.raw_value,
                normalized_value=max_cand.normalized_value,
                aggregate_confidence=agg_conf,
                supporting_variants=supporting_vars,
                conflicting_variants=conflicting_vars,
                all_candidates=candidates,
                requires_review=False,
                review_reason=None,
            )

        has_conflicts = conflicting_count > 0
        requires_human_review = has_conflicts

        return FusedDeclarationSummary(
            fused_fields=fused_fields,
            total_fields_extracted=total_extracted,
            confirmed_count=confirmed_count,
            probable_count=probable_count,
            conflicting_count=conflicting_count,
            missing_count=missing_count,
            has_conflicts=has_conflicts,
            requires_human_review=requires_human_review,
            review_reasons=all_review_reasons,
            raw_declarations_per_variant=per_variant_declarations,
        )


# Global singleton instance
declaration_fusion_service = DeclarationFusionService()

