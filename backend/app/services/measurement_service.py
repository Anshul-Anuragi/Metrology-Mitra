from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from app.core.enums import CheckResult


def get_schedule_ii_min_height(pdp_area_cm2: Optional[float], is_blown_or_moulded: bool = False) -> float:
    """
    Returns the statutory minimum numeral/letter height in millimetres under
    Rule 7 and Schedule II (Table 1) of LMPC Rules, 2011:
    - Area <= 50 cm²: 1.0 mm (1.5 mm for blown/moulded)
    - 50 < Area <= 100 cm²: 1.5 mm (2.0 mm for blown/moulded)
    - 100 < Area <= 500 cm²: 2.0 mm (3.0 mm for blown/moulded)
    - 500 < Area <= 2500 cm²: 4.0 mm (6.0 mm for blown/moulded)
    - Area > 2500 cm²: 6.0 mm (6.0 mm for blown/moulded)
    """
    if pdp_area_cm2 is None or pdp_area_cm2 <= 0:
        return 2.0  # Default standard assumption for typical medium package

    if pdp_area_cm2 <= 50.0:
        return 1.5 if is_blown_or_moulded else 1.0
    elif pdp_area_cm2 <= 100.0:
        return 2.0 if is_blown_or_moulded else 1.5
    elif pdp_area_cm2 <= 500.0:
        return 3.0 if is_blown_or_moulded else 2.0
    elif pdp_area_cm2 <= 2500.0:
        return 6.0 if is_blown_or_moulded else 4.0
    else:
        return 6.0


@dataclass
class MeasurementEvidence:
    pixel_height: Optional[float]
    physical_height_mm: Optional[float]
    scale_source: str  # "REFERENCE_OBJECT", "INSPECTOR_CALIBRATED", "UNAVAILABLE"
    scale_confidence: float
    measurement_confidence: float
    threshold_mm: float
    pdp_area_cm2: Optional[float]
    result: CheckResult
    reason: str
    is_prototype: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pixel_height": round(self.pixel_height, 2) if self.pixel_height is not None else None,
            "physical_height_mm": round(self.physical_height_mm, 2) if self.physical_height_mm is not None else None,
            "scale_source": self.scale_source,
            "scale_confidence": round(self.scale_confidence, 2),
            "measurement_confidence": round(self.measurement_confidence, 2),
            "threshold_mm": self.threshold_mm,
            "pdp_area_cm2": self.pdp_area_cm2,
            "result": self.result.value,
            "reason": self.reason,
            "is_prototype": self.is_prototype,
            "methodology": "Reference-assisted image measurement (Decision-support prototype)",
        }


def evaluate_reference_assisted_measurement(
    pdp_area_cm2: Optional[float],
    pixel_height: Optional[float] = None,
    pixel_scale_mm_per_px: Optional[float] = None,
    scale_source: str = "UNAVAILABLE",
    scale_confidence: float = 0.0,
    is_human_verified: bool = False,
    is_blown_or_moulded: bool = False,
) -> MeasurementEvidence:
    """
    Evaluates numeral/font height against statutory Schedule II Table 1 thresholds.
    Strict Guardrail: If physical scale cannot be reliably established, result is strictly REVIEW.
    Never invents millimetre values.
    """
    threshold_mm = get_schedule_ii_min_height(pdp_area_cm2, is_blown_or_moulded)

    # 1. Human verification override
    if is_human_verified:
        return MeasurementEvidence(
            pixel_height=pixel_height,
            physical_height_mm=threshold_mm,
            scale_source="INSPECTOR_VERIFIED",
            scale_confidence=1.0,
            measurement_confidence=1.0,
            threshold_mm=threshold_mm,
            pdp_area_cm2=pdp_area_cm2,
            result=CheckResult.PASS,
            reason=f"Numeral height verified by field officer as meeting Schedule II threshold ({threshold_mm} mm) for PDP area {pdp_area_cm2 or 'N/A'} cm².",
        )

    # 2. Check if scale and pixel height are available
    if not pixel_height or not pixel_scale_mm_per_px or scale_source == "UNAVAILABLE" or scale_confidence < 0.5:
        pdp_desc = f"PDP Area: {pdp_area_cm2} cm² (Min threshold: {threshold_mm} mm)" if pdp_area_cm2 else f"Statutory threshold: {threshold_mm} mm"
        return MeasurementEvidence(
            pixel_height=pixel_height,
            physical_height_mm=None,
            scale_source="UNAVAILABLE",
            scale_confidence=0.0,
            measurement_confidence=0.0,
            threshold_mm=threshold_mm,
            pdp_area_cm2=pdp_area_cm2,
            result=CheckResult.REVIEW,
            reason=f"Physical scale or calibrated reference unavailable ({pdp_desc}); ocular verification or reference object required under Rule 7.",
        )

    # 3. Calculate physical height
    physical_h_mm = pixel_height * pixel_scale_mm_per_px
    combined_conf = min(0.95, scale_confidence * 0.9)

    if physical_h_mm >= threshold_mm:
        return MeasurementEvidence(
            pixel_height=pixel_height,
            physical_height_mm=physical_h_mm,
            scale_source=scale_source,
            scale_confidence=scale_confidence,
            measurement_confidence=combined_conf,
            threshold_mm=threshold_mm,
            pdp_area_cm2=pdp_area_cm2,
            result=CheckResult.PASS,
            reason=f"Reference-assisted measurement ({physical_h_mm:.2f} mm) meets Schedule II minimum threshold ({threshold_mm} mm) for PDP area {pdp_area_cm2 or 'N/A'} cm².",
        )
    else:
        return MeasurementEvidence(
            pixel_height=pixel_height,
            physical_height_mm=physical_h_mm,
            scale_source=scale_source,
            scale_confidence=scale_confidence,
            measurement_confidence=combined_conf,
            threshold_mm=threshold_mm,
            pdp_area_cm2=pdp_area_cm2,
            result=CheckResult.REVIEW,
            reason=f"Reference-assisted measurement ({physical_h_mm:.2f} mm) is below Schedule II minimum threshold ({threshold_mm} mm). Field officer physical verification required.",
        )

