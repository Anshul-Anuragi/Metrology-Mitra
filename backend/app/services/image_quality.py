import enum
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageFilter, ImageStat


class QualityStatus(str, enum.Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class QualityGateDecision(str, enum.Enum):
    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
    RETAKE_RECOMMENDED = "RETAKE_RECOMMENDED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


# Defined constants and thresholds
MIN_WIDTH_PX = 300
MIN_HEIGHT_PX = 300
RECOMMENDED_MIN_WIDTH_PX = 600
RECOMMENDED_MIN_HEIGHT_PX = 600

# Laplacian variance thresholds for blur (higher = sharper, lower = blurry)
BLUR_THRESHOLD_FAIL = 350.0
BLUR_THRESHOLD_WARNING = 600.0

# Glare specular saturation thresholds (% of pixels with luminance >= 250)
GLARE_RATIO_WARNING = 0.08  # 8% overexposed pixels
GLARE_RATIO_FAIL = 0.18     # 18% overexposed pixels

# Exposure thresholds (mean luminance out of 255)
EXPOSURE_UNDEREXPOSED = 45.0
EXPOSURE_OVEREXPOSED = 215.0


@dataclass
class ImageQualityResult:
    width: int
    height: int
    blur_score: float
    blur_status: QualityStatus
    glare_ratio: float
    glare_status: QualityStatus
    glare_detected: bool
    exposure_mean: float
    exposure_status: QualityStatus
    resolution_status: QualityStatus
    gate_decision: QualityGateDecision
    overall_status: QualityStatus
    is_acceptable: bool
    guidance_message: str
    actionable_reasons: List[str]
    root_cause_categories: List[str] = field(default_factory=list)
    recoverability: str = "PROCESSING_RECOVERABLE"
    actionable_inspector_directives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "blur_score": round(self.blur_score, 2),
            "blur_status": self.blur_status.value,
            "glare_ratio": round(self.glare_ratio, 4),
            "glare_status": self.glare_status.value,
            "glare_detected": self.glare_detected,
            "exposure_mean": round(self.exposure_mean, 2),
            "exposure_status": self.exposure_status.value,
            "resolution_status": self.resolution_status.value,
            "gate_decision": self.gate_decision.value,
            "overall_status": self.overall_status.value,
            "is_acceptable": self.is_acceptable,
            "guidance_message": self.guidance_message,
            "actionable_reasons": self.actionable_reasons,
            "root_cause_categories": self.root_cause_categories,
            "recoverability": self.recoverability,
            "actionable_inspector_directives": self.actionable_inspector_directives,
        }


def _compute_laplacian_variance(gray_img: Image.Image) -> float:
    """
    Computes the variance of the Laplacian filter over the grayscale image.
    Deterministic measure of focus/sharpness.
    """
    laplacian_kernel = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[
            0,  1,  0,
            1, -4,  1,
            0,  1,  0,
        ],
        scale=1,
        offset=0,
    )
    edges = gray_img.filter(laplacian_kernel)
    stat = ImageStat.Stat(edges)
    std_dev = stat.stddev[0] if stat.stddev else 0.0
    return float(std_dev ** 2)


def _compute_glare_ratio(gray_img: Image.Image) -> float:
    """
    Computes the percentage of specularly saturated pixels (luminance >= 250 / 255).
    """
    hist = gray_img.histogram()
    total_pixels = sum(hist)
    if total_pixels == 0:
        return 0.0
    saturated_pixels = sum(hist[250:256])
    return float(saturated_pixels / total_pixels)


def _compute_exposure_mean(gray_img: Image.Image) -> float:
    """
    Computes the average luminance across the image.
    """
    stat = ImageStat.Stat(gray_img)
    return float(stat.mean[0]) if stat.mean else 128.0


def compute_resolution_aware_blur_thresholds(
    width: int, height: int
) -> Tuple[float, float]:
    """
    Computes resolution-scaled Laplacian variance blur thresholds.
    NOTE: These thresholds are engineering heuristics to accommodate high-resolution
    smartphone captures (where pixel-level Laplacian variance scales inversely with
    increasing sensor resolution / lens roll-off), and do NOT constitute statutory requirements.
    """
    megapixels = (width * height) / 1_000_000.0
    if megapixels <= 2.0:
        return BLUR_THRESHOLD_FAIL, BLUR_THRESHOLD_WARNING

    scale_factor = (2.0 / megapixels) ** 0.5
    fail_threshold = max(140.0, round(BLUR_THRESHOLD_FAIL * scale_factor, 1))
    warning_threshold = BLUR_THRESHOLD_WARNING
    return fail_threshold, warning_threshold


def assess_image_quality(image_path: Path) -> ImageQualityResult:
    """
    Deterministic pre-flight optical diagnostic assessment & Quality Gate for packaging photographs:
    1. Laplacian variance blur metric
    2. Specular reflection / glare ratio
    3. Exposure & contrast analysis
    4. Spatial resolution adequacy
    5. Actionable advisory synthesis
    """
    with Image.open(image_path) as img:
        width, height = img.size
        gray = img.convert("L")

        blur_score = _compute_laplacian_variance(gray)
        glare_ratio = _compute_glare_ratio(gray)
        exposure_mean = _compute_exposure_mean(gray)

        # 1. Resolution Check
        if width < MIN_WIDTH_PX or height < MIN_HEIGHT_PX:
            res_status = QualityStatus.FAIL
        elif width < RECOMMENDED_MIN_WIDTH_PX or height < RECOMMENDED_MIN_HEIGHT_PX:
            res_status = QualityStatus.WARNING
        else:
            res_status = QualityStatus.PASS

        # 2. Blur Check (resolution-aware heuristic)
        effective_blur_fail, effective_blur_warning = compute_resolution_aware_blur_thresholds(width, height)
        if blur_score < effective_blur_fail:
            blur_status = QualityStatus.FAIL
        elif blur_score < effective_blur_warning:
            blur_status = QualityStatus.WARNING
        else:
            blur_status = QualityStatus.PASS

        # 3. Glare Check
        glare_detected = glare_ratio > 0.04
        if glare_ratio >= GLARE_RATIO_FAIL:
            glare_status = QualityStatus.FAIL
        elif glare_ratio >= GLARE_RATIO_WARNING:
            glare_status = QualityStatus.WARNING
        else:
            glare_status = QualityStatus.PASS

        # 4. Exposure Check
        if exposure_mean < EXPOSURE_UNDEREXPOSED or exposure_mean > EXPOSURE_OVEREXPOSED:
            exposure_status = QualityStatus.WARNING
        else:
            exposure_status = QualityStatus.PASS

        # Synthesize Actionable Feedback & Quality Gate Decision
        reasons: List[str] = []

        if blur_status == QualityStatus.FAIL:
            reasons.append(
                f"Image is significantly blurred (Sharpness Score: {blur_score:.1f} < {effective_blur_fail:.0f}). Small statutory text and dates may be unreadable."
            )
        elif blur_status == QualityStatus.WARNING:
            reasons.append(
                f"Moderate blur detected (Sharpness Score: {blur_score:.1f} < {effective_blur_warning:.0f}). Hold camera steady under good lighting."
            )

        if glare_status == QualityStatus.FAIL:
            reasons.append(
                f"Severe specular glare detected ({glare_ratio * 100:.1f}% of image is overexposed). Shiny packaging reflection obscures declarations."
            )
        elif glare_status == QualityStatus.WARNING:
            reasons.append(
                f"Specular reflection detected ({glare_ratio * 100:.1f}%). Adjust capture angle to avoid direct flash or light reflection."
            )

        if res_status == QualityStatus.FAIL:
            reasons.append(
                f"Image resolution ({width}x{height}px) is below minimum required {MIN_WIDTH_PX}x{MIN_HEIGHT_PX}px."
            )

        if exposure_status == QualityStatus.WARNING:
            if exposure_mean < EXPOSURE_UNDEREXPOSED:
                reasons.append(f"Image is underexposed/dark (Mean luminance: {exposure_mean:.1f}/255). Increase ambient illumination.")
            else:
                reasons.append(f"Image is overly bright/washed out (Mean luminance: {exposure_mean:.1f}/255).")

        # Root Cause Disaggregation & Recoverability
        root_causes: List[str] = []
        directives: List[str] = []

        if glare_status == QualityStatus.FAIL:
            root_causes.append("SPECULAR_GLARE")
            directives.append("Tilt package 15-20° away from direct light/flash to eliminate specular reflection across declarations.")
        elif glare_status == QualityStatus.WARNING or glare_detected:
            root_causes.append("SPECULAR_REFLECTION")
            directives.append("Adjust capture angle slightly to shift glare spot away from statutory declaration text.")

        if blur_score < 100.0:
            root_causes.append("SEVERE_DEFOCUS")
            directives.append("Severe defocus detected. Tap camera screen to focus lens directly on statutory text before capturing.")
        elif blur_status == QualityStatus.FAIL:
            root_causes.append("MOTION_BLUR")
            directives.append("Hold camera steady or rest hands on a flat surface to eliminate motion blur on fine statutory print.")
        elif blur_status == QualityStatus.WARNING:
            root_causes.append("MODERATE_BLUR")
            directives.append("Hold camera steady and ensure package is well-lit.")

        if exposure_status == QualityStatus.WARNING:
            if exposure_mean < EXPOSURE_UNDEREXPOSED:
                root_causes.append("LOW_CONTRAST")
                directives.append("Increase ambient illumination or reposition light source to heighten text contrast.")
            else:
                root_causes.append("OVEREXPOSURE")
                directives.append("Reduce ambient brightness or turn off flash to prevent washed-out text.")

        if res_status == QualityStatus.FAIL:
            root_causes.append("INSUFFICIENT_RESOLUTION")
            directives.append(f"Move camera closer to package to capture at least {MIN_WIDTH_PX}x{MIN_HEIGHT_PX}px.")

        if len(root_causes) > 1:
            root_causes.append("MULTIPLE_DEFECTS")
        elif not root_causes:
            root_causes.append("NONE")

        # Quality Gate Classification
        if blur_status == QualityStatus.FAIL or glare_status == QualityStatus.FAIL or res_status == QualityStatus.FAIL:
            gate_decision = QualityGateDecision.RETAKE_RECOMMENDED
            overall_status = QualityStatus.FAIL
            is_acceptable = False
            guidance_msg = "Retake recommended: " + " ".join(reasons)
        elif blur_status == QualityStatus.WARNING or glare_status == QualityStatus.WARNING or exposure_status == QualityStatus.WARNING:
            gate_decision = QualityGateDecision.MANUAL_REVIEW
            overall_status = QualityStatus.WARNING
            is_acceptable = True
            guidance_msg = "Manual review advised: " + (" ".join(reasons) if reasons else "Borderline image clarity; verify extracted fields.")
        else:
            gate_decision = QualityGateDecision.READY_FOR_ANALYSIS
            overall_status = QualityStatus.PASS
            is_acceptable = True
            guidance_msg = f"Optimal photograph quality (Sharpness: {blur_score:.1f}, Glare: {glare_ratio * 100:.1f}%, Resolution: {width}x{height}px). Ready for automated analysis."

        if blur_score < 100.0 or res_status == QualityStatus.FAIL or glare_ratio >= GLARE_RATIO_FAIL:
            recoverability = "CAPTURE_RETAKE_REQUIRED"
        elif not is_acceptable:
            recoverability = "PROCESSING_RECOVERABLE"
        else:
            recoverability = "READY"

        return ImageQualityResult(
            width=width,
            height=height,
            blur_score=blur_score,
            blur_status=blur_status,
            glare_ratio=glare_ratio,
            glare_status=glare_status,
            glare_detected=glare_detected,
            exposure_mean=exposure_mean,
            exposure_status=exposure_status,
            resolution_status=res_status,
            gate_decision=gate_decision,
            overall_status=overall_status,
            is_acceptable=is_acceptable,
            guidance_message=guidance_msg,
            actionable_reasons=reasons,
            root_cause_categories=root_causes,
            recoverability=recoverability,
            actionable_inspector_directives=directives,
        )
