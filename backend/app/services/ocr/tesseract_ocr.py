import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image
import pytesseract
from app.services.ocr.base import OCRProvider, OCRResponseData
from app.services.ocr.preprocessor import preprocess_image_for_ocr


class TesseractOCRProvider(OCRProvider):
    """
    Concrete local OCR provider utilizing Tesseract OCR 5 with detailed token analysis.
    Architected for English and Indic language script extensions.
    """
    def __init__(self, lang: str = "eng", psm: int = 3, oem: int = 3):
        self._lang = lang
    def __init__(self, lang: Optional[str] = None, psm: int = 3, oem: int = 3):
        if lang is not None:
            self._lang = lang
        else:
            try:
                available = pytesseract.get_languages()
                if "hin" in available:
                    self._lang = "eng+hin"
                else:
                    self._lang = "eng"
            except Exception:
                self._lang = "eng"
        self.config = f"--oem {oem} --psm {psm}"

    @property
    def name(self) -> str:
        return "tesseract-ocr-5"

    @property
    def language(self) -> str:
        return self._lang

    @property
    def supported_languages(self) -> List[str]:
        return ["eng", "hin", "tam", "tel", "kan", "mar", "ben", "guj"]

    def _sync_ocr(self, img: Image.Image) -> OCRResponseData:
        start_time = time.perf_counter()
        
        # Run Tesseract detailed token analysis
        data = pytesseract.image_to_data(
            img,
            lang=self._lang,
            config=self.config,
            output_type=pytesseract.Output.DICT,
        )
        
        tokens_data: List[Dict[str, Any]] = []
        confidences: List[float] = []
        full_text_lines: List[str] = []
        current_line: List[str] = []
        last_line_num = -1

        num_boxes = len(data["text"])
        for i in range(num_boxes):
            word = data["text"][i].strip()
            conf = float(data["conf"][i])
            line_num = data["line_num"][i]

            if line_num != last_line_num and current_line:
                full_text_lines.append(" ".join(current_line))
                current_line = []
            last_line_num = line_num

            if word:
                current_line.append(word)
                if conf >= 0:
                    normalized_conf = round(conf / 100.0, 4)
                    confidences.append(normalized_conf)
                else:
                    normalized_conf = None

                tokens_data.append({
                    "text": word,
                    "conf": normalized_conf,
                    "bbox": [
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    ],
                    "line_num": line_num,
                    "block_num": data["block_num"][i],
                })

        if current_line:
            full_text_lines.append(" ".join(current_line))

        raw_text = "\n".join(full_text_lines).strip()
        
        # If image_to_data extracted empty text, fallback to image_to_string
        if not raw_text:
            raw_text = pytesseract.image_to_string(img, lang=self._lang, config=self.config).strip()

        mean_confidence = (
            round(sum(confidences) / len(confidences), 4) if confidences else None
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return OCRResponseData(
            raw_text=raw_text,
            confidence=mean_confidence,
            engine=self.name,
            processing_time_ms=duration_ms,
            tokens_data=tokens_data,
        )

    async def extract_text(
        self, image_input: Union[bytes, Path, str, Image.Image]
    ) -> OCRResponseData:
        preprocessed_img = preprocess_image_for_ocr(image_input)
        return await asyncio.to_thread(self._sync_ocr, preprocessed_img)


# Backward compatibility class alias
LocalOCRService = TesseractOCRProvider

# Global default OCR provider instance
ocr_service: OCRProvider = TesseractOCRProvider()
