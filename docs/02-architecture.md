# Architecture Overview — Legal Metrology Compliance System

## 1. System Pipeline

```text
[ Inspection Images Uploaded (FRONT, BACK, LABEL) ]
                        │
                        ▼
            [ Image Preprocessing ]
   (Validation, EXIF transpose, RGB normalisation, contrast)
                        │
                        ▼
               [ OCR Service Layer ]
      (BaseOCRService / LocalOCRService / Tesseract 5)
                        │
                        ▼
             [ Raw OCR Storage ]
            (Table: ocr_results)
                        │
                        ▼
    [ Structured Declaration Extractor ]
    (LMPC 2011 Pattern Matching & Confidences)
                        │
                        ▼
           [ Stored Declaration ]
           (Table: declarations)
   (Preserves human verification: is_human_verified)
                        │
                        ▼
     [ Deterministic Legal Rule Engine ]
     (Tables: legal_rules, compliance_checks)
                        │
                        ▼
   [ Overall Aggregation: COMPLIANT / NON_COMPLIANT / NEEDS_REVIEW ]
```

---

## 2. Core Service Layers

### A. Storage Service Layer (`app.services.storage`)
- **`BaseStorageService`**: Abstract interface for saving/deleting image blobs.
- **`LocalStorageService`**: Concrete implementation saving images to `uploads/inspections/{inspection_id}/` (swappable for S3 or MinIO).

### B. OCR & Perception Layer (`app.services.ocr`)
- **`BaseOCRService`**: Pluggable OCR interface producing `OCRResponseData` (raw text, word tokens with bounding boxes, confidence score, processing latency).
- **`LocalOCRService`**: Concrete implementation utilizing Tesseract OCR 5 with detailed token analysis and fallback recovery.
- **`Preprocessor`**: Validates file size, formats (`JPEG`, `PNG`, `WEBP`), corrects EXIF rotation, scales within bounds `[100px, 3000px]`, and enhances optical contrast.
- **`DeclarationExtractor`**: Deterministically parses LMPC Rule 6 statutory declarations (`commodity_name`, `manufacturer_name`, `address`, `net_quantity`, `mrp`, `unit_sale_price`, dates, `consumer_care`, `country_of_origin`).

### C. Legal Rules Knowledge Base & Rule Engine (`app.services.rule_engine`)
- Grounded strictly in the **Legal Metrology (Packaged Commodities) Rules, 2011**.
- Evaluates 12 active statutory rule codes (`LMPC-R6-*`, `LMPC-R7-*`, `LMPC-R8-*`, `LMPC-R9-*`).
- Produces explicit `PASS`, `FAIL`, or `REVIEW` decisions with statutory citations and reasons.
- **Strict Separation:** The OCR layer produces raw evidence and candidate declarations; the Rule Engine independently determines legal compliance without LLMs.

---

## 3. Human-in-the-Loop & Data Integrity Guardrails

- **Human Verification Preservation:** When an inspector manually verifies or edits declaration fields (`is_human_verified = True`), subsequent OCR operations **never overwrite** non-null human-verified values.
- **Safety Fallback:** If optical evidence is incomplete or scale data is missing, the engine yields `REVIEW` (`InspectionStatus.REVIEW_REQUIRED`) rather than guessing compliance.

