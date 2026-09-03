import io
from pathlib import Path
from typing import Union
from PIL import Image, ImageEnhance, ImageOps


SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "TIFF", "BMP"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MAX_DIMENSION_PX = 3000
MIN_DIMENSION_PX = 100


def validate_and_open_image(image_input: Union[bytes, Path, str, Image.Image]) -> Image.Image:
    """Validates and opens image input into a PIL Image instance."""
    if isinstance(image_input, Image.Image):
        return image_input

    if isinstance(image_input, bytes):
        if len(image_input) == 0:
            raise ValueError("Image data is empty (0 bytes).")
        if len(image_input) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"Image size exceeds maximum limit of {MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB.")
        try:
            img = Image.open(io.BytesIO(image_input))
            img.load()  # Verify image integrity
            return img
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image format: {e}")

    path = Path(image_input)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found at path: {path}")

    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Image file exceeds maximum limit of {MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB.")

    try:
        img = Image.open(path)
        img.load()
        return img
    except Exception as e:
        raise ValueError(f"Failed to decode image from path: {e}")


def preprocess_image_for_ocr(image_input: Union[bytes, Path, str, Image.Image]) -> Image.Image:
    """
    Standard preprocessing pipeline for package label OCR:
    1. Validate format and open image
    2. Auto-transpose orientation using EXIF tags
    3. Convert RGBA / Palette to RGB
    4. Constrain dimensions to optimal OCR range
    5. Enhance contrast slightly for text clarity
    """
    img = validate_and_open_image(image_input)

    # 1. Orientation correction
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # 2. Color mode normalization
    if img.mode in ("RGBA", "LA", "P"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            rgb_img.paste(img, mask=img.split()[3])
        else:
            rgb_img.paste(img.convert("RGB"))
        img = rgb_img
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # 3. Dimension bounds
    w, h = img.size
    if w < MIN_DIMENSION_PX or h < MIN_DIMENSION_PX:
        scale = max(MIN_DIMENSION_PX / max(w, 1), MIN_DIMENSION_PX / max(h, 1))
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    elif w > MAX_DIMENSION_PX or h > MAX_DIMENSION_PX:
        scale = min(MAX_DIMENSION_PX / w, MAX_DIMENSION_PX / h)
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # 4. Light contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)

    return img

