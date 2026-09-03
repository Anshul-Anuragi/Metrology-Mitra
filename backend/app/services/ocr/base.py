from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class OCRResponseData:
    raw_text: str
    confidence: Optional[float]
    engine: str
    processing_time_ms: int
    tokens_data: List[Dict[str, Any]]


class OCRProvider(ABC):
    """
    Abstract Base Class for OCR providers.
    Supports pluggable local and multilingual OCR engines (Tesseract 5, Indic-OCR ready).
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the OCR provider engine."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """List of supported language codes (e.g. ['eng', 'hin', 'tam'])."""
        pass

    @abstractmethod
    async def extract_text(self, image_input: bytes | Path | str | Image.Image) -> OCRResponseData:
        """Extracts raw text and spatial token bounding boxes with confidence scores."""
        pass


# Backward compatibility alias
BaseOCRService = OCRProvider
