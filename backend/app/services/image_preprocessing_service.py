"""
Phase 4.3 — Deterministic Adaptive Image Preprocessing Service
============================================================
Provides multi-stage, evidence-preserving, and non-destructive image preprocessing
for packaged-commodity photographs under Legal Metrology compliance inspection.

Architectural Principles & Boundaries:
1. Raw Master Immutability: Original photographic bytes and SHA-256 digests remain untouched.
   RAW_MASTER is a reference/semantic token representing the immutable raw ingress evidence;
   it is never returned as a processed derivative.
2. Normalized Derivative Clarity: NORMALIZED_ORIGINAL is a normalized derivative (EXIF-transposed,
   color-mode normalized to RGB, clamped if outside bounds) and is NOT the untouched raw byte stream.
   The six generated standard derivatives are:
     1. NORMALIZED_ORIGINAL
     2. GRAYSCALE
     3. CONTRAST_NORMALIZED
     4. SHARPENED
     5. UPSCALED
     6. ADAPTIVE_THRESHOLD
3. Cryptographic Provenance Linkage: Tracks original_image_hash (raw master anchor),
   parent_variant_hash (immediate derivation source), and processed_image_hash.
   This establishes in-memory technical provenance linkage for execution auditability;
   it does not establish persistent database hash chains or statutory certification.
4. Determinism Boundaries: Image output bytes and image hashes are 100% deterministic
   (IMAGE_OUTPUT_DETERMINISM = PASS, IMAGE_HASH_DETERMINISM = PASS). Provenance timestamps
   reflect execution time for auditability (PROVENANCE_TIMESTAMP = RUN_SPECIFIC).
5. Adaptive Threshold Mathematical Rule:
   Implements output(x,y) = 255 if gray(x,y) >= local_mean(x,y) - C else 0.
   Limitation: Adaptive thresholding aids local illumination gradients and uneven backgrounds,
   but cannot recover text pixels physically saturated or obliterated by specular glare.
6. Statutory Authority Boundary: Preprocessing produces visual evidence derivatives only.
   The deterministic versioned legal rule engine remains the sole statutory authority.
7. Non-Judicial Notice: This service supports technical reproducibility and evidence provenance;
   it does not determine legal admissibility or judicial acceptance under the Legal Metrology Act, 2009.
"""

import datetime
import enum
import hashlib
import io
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


class PreprocessingVariantName(str, enum.Enum):
    RAW_MASTER = "RAW_MASTER"  # Reference/semantic token for immutable raw input evidence (not a generated variant)
    NORMALIZED_ORIGINAL = "NORMALIZED_ORIGINAL"  # Normalized derivative (EXIF, RGB, bounds clamped)
    ORIGINAL = "ORIGINAL"  # Backward-compatible alias for NORMALIZED_ORIGINAL
    GRAYSCALE = "GRAYSCALE"
    CONTRAST_NORMALIZED = "CONTRAST_NORMALIZED"
    SHARPENED = "SHARPENED"
    UPSCALED = "UPSCALED"
    ADAPTIVE_THRESHOLD = "ADAPTIVE_THRESHOLD"
    LOCAL_CONTRAST_ENHANCED = "LOCAL_CONTRAST_ENHANCED"


# Exactly standard generated derivatives (RAW_MASTER is a reference token, not a generated variant)
ALL_STANDARD_VARIANTS = [
    PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
    PreprocessingVariantName.GRAYSCALE.value,
    PreprocessingVariantName.CONTRAST_NORMALIZED.value,
    PreprocessingVariantName.LOCAL_CONTRAST_ENHANCED.value,
    PreprocessingVariantName.SHARPENED.value,
    PreprocessingVariantName.UPSCALED.value,
    PreprocessingVariantName.ADAPTIVE_THRESHOLD.value,
]


@dataclass
class PreprocessingConfig:
    max_dimension_px: int = 3000
    min_dimension_px: int = 100
    contrast_factor: float = 1.25
    contrast_cutoff: float = 0.5
    unsharp_radius: float = 1.0
    unsharp_percent: int = 150
    unsharp_threshold: int = 3
    adaptive_block_size: int = 25
    adaptive_c: int = 10
    upscale_factor: float = 1.5
    enabled_variants: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PreprocessingResult:
    variant_name: str
    original_image_hash: str  # SHA-256 digest of immutable raw master evidence
    parent_variant_hash: str  # SHA-256 digest of immediate parent derivative or master
    processed_image_hash: str  # SHA-256 digest of this variant's image bytes
    width: int
    height: int
    mode: str
    parameters_used: Dict[str, Any]
    provenance_metadata: Dict[str, Any]
    image: Image.Image = field(repr=False)
    image_bytes: bytes = field(repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_name": self.variant_name,
            "original_image_hash": self.original_image_hash,
            "parent_variant_hash": self.parent_variant_hash,
            "processed_image_hash": self.processed_image_hash,
            "width": self.width,
            "height": self.height,
            "mode": self.mode,
            "parameters_used": self.parameters_used,
            "provenance_metadata": self.provenance_metadata,
            "byte_size": len(self.image_bytes),
        }


class ImagePreprocessingService:
    """
    Evidence-preserving adaptive image preprocessing service for packaging label OCR.
    Generates bounded deterministic derivatives with in-memory cryptographic provenance linkage.
    """

    SERVICE_VERSION = "4.3.0"

    @staticmethod
    def compute_bytes_hash(raw_bytes: bytes) -> str:
        """Computes deterministic SHA-256 hexadecimal digest of raw bytes."""
        return hashlib.sha256(raw_bytes).hexdigest()

    def load_image_with_hash(
        self, image_input: Union[bytes, Path, str, Image.Image]
    ) -> Tuple[Image.Image, bytes, str]:
        """
        Loads an image input into PIL Image, preserves raw bytes, and computes SHA-256.
        Path/bytes inputs preserve and hash the actual supplied byte stream.
        PIL.Image inputs are deterministically serialized for in-memory/test provenance
        and therefore do not represent an original capture container byte stream.
        """
        if isinstance(image_input, bytes):
            raw_bytes = bytes(image_input)  # immutable copy
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            sha256_hash = self.compute_bytes_hash(raw_bytes)
            return img, raw_bytes, sha256_hash

        if isinstance(image_input, (Path, str)):
            p = Path(image_input)
            if not p.exists():
                raise FileNotFoundError(f"Image path not found: {p}")
            raw_bytes = p.read_bytes()
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            sha256_hash = self.compute_bytes_hash(raw_bytes)
            return img, raw_bytes, sha256_hash

        if isinstance(image_input, Image.Image):
            # Deterministic serialization for in-memory / testing usage only
            buf = io.BytesIO()
            image_input.save(buf, format="PNG")
            raw_bytes = buf.getvalue()
            sha256_hash = self.compute_bytes_hash(raw_bytes)
            return image_input.copy(), raw_bytes, sha256_hash

        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    def normalize_base_image(self, img: Image.Image, config: PreprocessingConfig) -> Image.Image:
        """
        Normalizes orientation, color mode, and dimensions without destructive filtering:
        1. EXIF orientation correction.
        2. Color mode normalization: Alpha flattened over white; converted to RGB.
        3. Dimension bounds clamping via Lanczos interpolation.
        Note: The returned image is a normalized derivative, NOT the untouched raw master.
        """
        # 1. Orientation
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # 2. Color mode
        if img.mode in ("RGBA", "LA", "P"):
            rgb = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                rgb.paste(img, mask=img.split()[3])
            elif img.mode == "LA":
                rgb.paste(img.convert("RGB"), mask=img.split()[1])
            else:
                rgb.paste(img.convert("RGB"))
            img = rgb
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Dimension bounds
        w, h = img.size
        if w < config.min_dimension_px or h < config.min_dimension_px:
            scale = max(config.min_dimension_px / max(w, 1), config.min_dimension_px / max(h, 1))
            new_size = (max(int(w * scale), 1), max(int(h * scale), 1))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        elif w > config.max_dimension_px or h > config.max_dimension_px:
            scale = min(config.max_dimension_px / w, config.max_dimension_px / h)
            new_size = (max(int(w * scale), 1), max(int(h * scale), 1))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        return img

    def generate_variant(
        self,
        base_img: Image.Image,
        variant_name: str,
        config: PreprocessingConfig,
        orig_hash: str,
        parent_hash: Optional[str] = None,
    ) -> PreprocessingResult:
        """
        Generates a specific bounded deterministic derivative with in-memory cryptographic provenance linkage.
        """
        params_used: Dict[str, Any] = {}
        # Default parent hash to orig_hash if not explicitly provided
        effective_parent_hash = parent_hash or orig_hash

        # Canonicalize variant name
        is_orig_alias = variant_name in (
            PreprocessingVariantName.ORIGINAL.value,
            PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
        )

        if is_orig_alias:
            variant_img = base_img.copy()
            params_used = {
                "action": "normalized_derivative",
                "derivation": "EXIF transposed, RGB mode normalized, dimension bounds clamped",
                "is_raw_master": False,
            }
            # For normalized original, parent is the raw master
            effective_parent_hash = orig_hash

        elif variant_name == PreprocessingVariantName.GRAYSCALE.value:
            variant_img = base_img.convert("L")
            params_used = {"color_mode": "L"}

        elif variant_name == PreprocessingVariantName.CONTRAST_NORMALIZED.value:
            gray = base_img.convert("L")
            norm = ImageOps.autocontrast(gray, cutoff=config.contrast_cutoff)
            enhancer = ImageEnhance.Contrast(norm)
            variant_img = enhancer.enhance(config.contrast_factor)
            params_used = {
                "color_mode": "L",
                "contrast_cutoff": config.contrast_cutoff,
                "contrast_factor": config.contrast_factor,
            }

        elif variant_name == PreprocessingVariantName.LOCAL_CONTRAST_ENHANCED.value:
            # Multi-scale local edge and contrast preservation for curved / reflective packaging
            gray = base_img.convert("L")
            bg_radius = max(5, min(gray.width, gray.height) // 40)
            bg_map = gray.filter(ImageFilter.BoxBlur(bg_radius))
            detail = ImageChops.subtract(gray, bg_map, scale=1.0, offset=128)
            enhanced_detail = ImageOps.autocontrast(detail, cutoff=1.0)
            variant_img = Image.blend(gray, enhanced_detail, alpha=0.7)
            params_used = {
                "color_mode": "L",
                "bg_radius": bg_radius,
                "detail_cutoff": 1.0,
                "blend_alpha": 0.7,
                "mathematical_rule": "blend(gray, autocontrast(gray - local_bg + 128), 0.7)",
                "purpose": "Normalizes localized lighting and cylinder fall-off without obliterating text strokes.",
            }

        elif variant_name == PreprocessingVariantName.SHARPENED.value:
            unsharp = ImageFilter.UnsharpMask(
                radius=config.unsharp_radius,
                percent=config.unsharp_percent,
                threshold=config.unsharp_threshold,
            )
            variant_img = base_img.filter(unsharp)
            params_used = {
                "unsharp_radius": config.unsharp_radius,
                "unsharp_percent": config.unsharp_percent,
                "unsharp_threshold": config.unsharp_threshold,
            }

        elif variant_name == PreprocessingVariantName.UPSCALED.value:
            w, h = base_img.size
            scale = config.upscale_factor
            target_w = int(w * scale)
            target_h = int(h * scale)
            # Bound upscale so it does not exceed max_dimension_px
            if target_w > config.max_dimension_px or target_h > config.max_dimension_px:
                max_scale = min(config.max_dimension_px / w, config.max_dimension_px / h)
                target_w = int(w * max_scale)
                target_h = int(h * max_scale)
            variant_img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            params_used = {
                "requested_upscale_factor": config.upscale_factor,
                "resulting_size": [target_w, target_h],
                "resampling": "LANCZOS",
            }

        elif variant_name == PreprocessingVariantName.ADAPTIVE_THRESHOLD.value:
            # Deterministic BoxBlur-based local adaptive thresholding
            # Mathematical Rule: output(x,y) = 255 if gray(x,y) >= local_mean(x,y) - C else 0
            # Limitation: Aids local illumination gradients; cannot recover text physically saturated by specular glare.
            gray = base_img.convert("L")
            radius = max(1, config.adaptive_block_size // 2)
            local_mean = gray.filter(ImageFilter.BoxBlur(radius))
            # Subtract local mean with offset 128: result = (gray - local_mean) + 128 clamped to [0, 255]
            diff = ImageChops.subtract(gray, local_mean, scale=1.0, offset=128)
            # Threshold: gray >= local_mean - C  <=>  (gray - local_mean) + 128 >= 128 - C
            thresh = max(0, min(255, 128 - config.adaptive_c))
            lut = [255 if i >= thresh else 0 for i in range(256)]
            variant_img = diff.point(lut, mode="L")
            params_used = {
                "color_mode": "L",
                "block_size": config.adaptive_block_size,
                "blur_radius": radius,
                "adaptive_c": config.adaptive_c,
                "threshold_offset": thresh,
                "mathematical_rule": "gray >= local_mean - C",
                "glare_limitation": "Aids illumination gradients; cannot recover physically saturated specular text.",
            }

        else:
            raise ValueError(f"Unknown preprocessing variant: {variant_name}")

        # Deterministic byte serialization (PNG is lossless and reproducible)
        buf = io.BytesIO()
        variant_img.save(buf, format="PNG")
        processed_bytes = buf.getvalue()
        processed_hash = self.compute_bytes_hash(processed_bytes)

        provenance_metadata = {
            "variant_name": variant_name,
            "original_image_hash": orig_hash,
            "parent_variant_hash": effective_parent_hash,
            "processed_image_hash": processed_hash,
            "dimensions": [variant_img.width, variant_img.height],
            "mode": variant_img.mode,
            "parameters_used": params_used,
            "service_version": self.SERVICE_VERSION,
            "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "provenance_notes": "In-memory cryptographic provenance linkage tracking derivation from immutable raw master.",
        }

        return PreprocessingResult(
            variant_name=variant_name,
            original_image_hash=orig_hash,
            parent_variant_hash=effective_parent_hash,
            processed_image_hash=processed_hash,
            width=variant_img.width,
            height=variant_img.height,
            mode=variant_img.mode,
            parameters_used=params_used,
            provenance_metadata=provenance_metadata,
            image=variant_img,
            image_bytes=processed_bytes,
        )

    def select_adaptive_variants(
        self,
        quality_result: Optional[Any] = None,
    ) -> List[str]:
        """
        Determines the optimal set of preprocessing variants based on pre-flight optical metrics.
        Guarantees that NORMALIZED_ORIGINAL is always first, followed by adaptive recommendations.
        """
        variants: List[str] = [PreprocessingVariantName.NORMALIZED_ORIGINAL.value]

        if quality_result is None:
            # Default core set if no pre-flight optical result is available
            variants.extend([
                PreprocessingVariantName.CONTRAST_NORMALIZED.value,
                PreprocessingVariantName.ADAPTIVE_THRESHOLD.value,
            ])
            return variants

        # Extract attributes safely whether dataclass or dict
        glare_detected = getattr(quality_result, "glare_detected", False)
        glare_ratio = getattr(quality_result, "glare_ratio", 0.0)
        glare_status = getattr(quality_result, "glare_status", None)
        blur_score = getattr(quality_result, "blur_score", 1000.0)
        blur_status = getattr(quality_result, "blur_status", None)
        width = getattr(quality_result, "width", 1000)
        height = getattr(quality_result, "height", 1000)

        # 1. Glare condition -> Add adaptive thresholding (engineering diagnostic heuristic)
        has_glare = (
            glare_detected
            or glare_ratio >= 0.04
            or (glare_status and str(glare_status) in ("WARNING", "FAIL", "QualityStatus.WARNING", "QualityStatus.FAIL"))
        )
        if has_glare:
            variants.append(PreprocessingVariantName.ADAPTIVE_THRESHOLD.value)

        # 2. General contrast enhancement
        variants.append(PreprocessingVariantName.CONTRAST_NORMALIZED.value)

        # 2b. Local contrast enhancement for dark, unevenly illuminated, or curved packaging
        exposure_mean = getattr(quality_result, "exposure_mean", 128.0)
        if exposure_mean < 115.0 or blur_score < 400.0:
            variants.append(PreprocessingVariantName.LOCAL_CONTRAST_ENHANCED.value)

        # 3. Blur condition -> Add sharpening (engineering diagnostic heuristic)
        has_blur = (
            blur_score < 600.0
            or (blur_status and str(blur_status) in ("WARNING", "FAIL", "QualityStatus.WARNING", "QualityStatus.FAIL"))
        )
        if has_blur:
            variants.append(PreprocessingVariantName.SHARPENED.value)

        # 4. Small resolution / fine-font condition -> Add bounded upscaling
        if width < 800 or height < 800:
            variants.append(PreprocessingVariantName.UPSCALED.value)

        # Deduplicate while preserving insertion order
        seen = set()
        deduped: List[str] = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                deduped.append(v)

        return deduped

    def preprocess_image(
        self,
        image_input: Union[bytes, Path, str, Image.Image],
        config: Optional[PreprocessingConfig] = None,
        variants: Optional[List[str]] = None,
        quality_result: Optional[Any] = None,
    ) -> List[PreprocessingResult]:
        """
        Executes deterministic multi-variant preprocessing pipeline.
        Returns ordered list of PreprocessingResult instances with provenance linkage.
        """
        cfg = config or PreprocessingConfig()
        raw_img, raw_bytes, orig_hash = self.load_image_with_hash(image_input)

        # Normalize base image without modifying raw bytes
        base_img = self.normalize_base_image(raw_img, cfg)

        # Compute hash of the normalized base image to serve as parent_variant_hash for sub-derivatives
        buf = io.BytesIO()
        base_img.save(buf, format="PNG")
        normalized_base_hash = self.compute_bytes_hash(buf.getvalue())

        target_variants = variants or cfg.enabled_variants
        if target_variants is None:
            target_variants = self.select_adaptive_variants(quality_result)

        results: List[PreprocessingResult] = []
        for v_name in target_variants:
            is_orig = v_name in (
                PreprocessingVariantName.ORIGINAL.value,
                PreprocessingVariantName.NORMALIZED_ORIGINAL.value,
            )
            # Normalized original's parent is the raw master; downstream derivatives' parent is normalized base
            parent_h = orig_hash if is_orig else normalized_base_hash
            res = self.generate_variant(base_img, v_name, cfg, orig_hash, parent_h)
            results.append(res)

        return results


# Global singleton instance for production use
image_preprocessing_service = ImagePreprocessingService()
