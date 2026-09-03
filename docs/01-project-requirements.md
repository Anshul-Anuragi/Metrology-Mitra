# Functional & System Requirements — SIH26034

## 1. Statutory Context & Legal Authority
- **Problem Statement ID:** SIH26034
- **Title:** Development of a Software Application for Compliance Inspection of Packaged Commodities
- **Regulator:** Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Government of India
- **Primary Legislation:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules)

---

## 2. Core Functional Requirements (FRs)

- **FR-01 (Image Ingestion & Storage):** Capture/upload multi-angle package photographs (Front, Back, Side, Label) and securely store them.
- **FR-02 (Optical Character Recognition):** Extract printed text and token bounding boxes with local OCR (Tesseract 5).
- **FR-03 (Structured Declaration Extraction):** Deterministically extract mandatory Rule 6 declarations (MRP, Net Qty, Dates, Manufacturer, Consumer Care, Origin, USP).
- **FR-04 (Deterministic Legal Rule Engine):** Evaluate declarations against 12 statutory LMPC 2011 rules without LLM hallucination.
- **FR-05 (Violation & Evidence Generation):** Automatically generate structured violations linked to statutory citations and map visual bounding box evidence.
- **FR-06 (Human Verification & Overrides):** Allow inspectors to review and override declarations, ensuring human authority is strictly preserved.
- **FR-07 (Role-Based Access Control):** Enforce strict scoping across `INSPECTOR`, `SUPERVISOR`, and `ADMIN` roles.
- **FR-08 (Automated Inspection Pipeline):** Execute end-to-end processing from image upload to compliance checks, violations, and evidence linking.

