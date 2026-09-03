from app.services.ocr.base import BaseOCRService, OCRResponseData
from app.services.ocr.extractor import extract_declaration_from_ocr
from app.services.ocr.preprocessor import preprocess_image_for_ocr, validate_and_open_image
from app.services.ocr.tesseract_ocr import LocalOCRService, ocr_service

__all__ = [
    "BaseOCRService",
    "OCRResponseData",
    "LocalOCRService",
    "ocr_service",
    "preprocess_image_for_ocr",
    "validate_and_open_image",
    "extract_declaration_from_ocr",
]

