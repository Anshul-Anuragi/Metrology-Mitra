import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.declaration import DeclarationResponse


class OCRResultBase(BaseModel):
    raw_text: str
    confidence: Optional[float] = None
    engine: Optional[str] = None
    tokens_data: Optional[List[Dict[str, Any]]] = None
    processing_time_ms: Optional[int] = None


class OCRResultResponse(OCRResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class OCRExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: uuid.UUID
    image_id: uuid.UUID
    ocr_result: OCRResultResponse
    extracted_fields: Dict[str, Any]
    field_confidences: Dict[str, float]
    declaration: DeclarationResponse

