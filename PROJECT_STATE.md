# Project State — MetrologyMitra (SIH26034)

> **Single Source of Truth** for maintaining, resuming, and verifying the **MetrologyMitra** codebase across development sessions.

---

## 1. Current Status
- **Official Project Name:** **MetrologyMitra**
- **Problem Statement ID:** SIH26034 — Development of a Software Application for Compliance Inspection of Packaged Commodities
- **Regulatory Authority:** Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Government of India
- **Primary Legislation:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules, 2011)
- **Current Completion Milestone:** Phases 0.1 through 2.5 Completed, Hardened, and Verified (All 5 Automated Test Suites PASS; Next.js 11/11 Routes Build PASS).

---

## 2. Architecture
- **Perception Layer:** Local Tesseract OCR 5 (`pytesseract`) + local ZXing-C++ barcode/QR decoding with bilingual English/Hindi Devanagari numeral translation (०-९ $\to$ 0-9) and script detection (`ENG`, `HIN`, `MIXED`).
- **Rule Engine Layer:** Deterministic statutory evaluation engine executing 18 encoded compliance checks based on selected provisions of the Legal Metrology (Packaged Commodities) Rules, 2011, Rule 26 statutory exemptions, and Rules 21–22 special packaging.
- **Service Layer (`backend/app/services`):** Segregated services for Image Quality Pre-Flight Gating, OCR Text & Coordinate Extraction, Schedule II Numeral Height Measurement, E-Commerce Listing Cross-Check, Schedule IV Batch Statistical Sampling & ZIP Bundle Exporter, Rule 24 Gravimetric Net-Quantity & MPE Verification Engine, Rule 26 Statutory Exemptions Evaluator, Field Geofence & Provenance Chaining, Section 48 Statutory Compounding Assessment, Violation Synthesis, Evidence Linking, ReportLab PDF Generation, and Supervisor Analytics.
- **API Layer (`backend/app/api/v1`):** FastAPI async routers enforcing JWT Authentication, Role-Based Access Control (RBAC), Object-level Inspector isolation, and Permanent Finalization Mutation Locks (`HTTP 409 Conflict`).
- **Data Layer:** PostgreSQL 16 managed via SQLAlchemy 2.0 AsyncIO and Alembic migrations (Head: `0005_gravimetric_and_exemptions`).
- **Frontend Layer (`frontend/src`):** Responsive Web Application built with Next.js 14 App Router, React 18, TypeScript, and Tailwind CSS.

---

## 3. Implementation Status Matrix

| Component / Subsystem | Status | Details |
|---|---|---|
| Multi-angle Image Ingestion & Storage | `IMPLEMENTED` | Local image storage with subfolder isolation per inspection session. |
| Pre-Flight Image Quality Gate | `IMPLEMENTED` | Optical blur variance, specular glare %, exposure, resolution $\to$ `READY_FOR_ANALYSIS` / `RETAKE_RECOMMENDED` / `MANUAL_REVIEW`. |
| Byte-Level Evidence Integrity (SHA-256) | `IMPLEMENTED` | Byte-level digital hash computed upon upload and tracked through to reports. |
| Local Perception & Barcode Decoding | `IMPLEMENTED` | Tesseract OCR 5 + ZXing-C++ extraction with token bounding box overlays. |
| Indic Multilingual & Devanagari OCR (Phase 2.0) | `IMPLEMENTED` | Devanagari numerals translation (०-९ $\to$ 0-9), script language detection, and Hindi keyword recognition under Rule 6(1). |
| 18 Statutory Rule Intelligence | `IMPLEMENTED` | 18 statutory checks with temporal versioning (`effective_from`/`to`) and channel filtering. |
| Rule 7 Numeral Height Assistant | `IMPLEMENTED` | Schedule II Table 1 PDP Area tiers ($1.0\text{--}6.0\text{ mm}$). Uncalibrated images strictly output `REVIEW` under prototype disclaimer. |
| E-Commerce Cross-Check (Rule 6(10)) | `IMPLEMENTED` | Cross-verifies physical declarations vs digital listings for origin/price/qty contradictions. |
| Neutral Reference MRP Discrepancy | `IMPLEMENTED` | Controlled catalog differences yield neutral finding (`"MRP discrepancy detected against reference data"` $\to$ `REVIEW`). |
| Registration Registry Check (Rule 27) | `IMPLEMENTED` | Unverified registry status yields `REVIEW` (never automatic `FAIL`). |
| Human-in-the-Loop Review Workspace | `IMPLEMENTED` | Adjudication actions (`CONFIRM`, `CORRECT`, `REQUEST_RETAKE`, `MARK_UNRESOLVED`) with manual override fields. |
| Permanent Finalization Mutation Lock | `IMPLEMENTED` | `POST /finalize` seals case to `COMPLETED`; mutations rejected with `HTTP 409 Conflict`. |
| Chronological Audit Trail | `IMPLEMENTED` | Immutable recording of all automated passes and manual adjudication decisions in `audit_logs`. |
| Batch / Lot Inspections & Schedule IV (Phase 2.1) | `IMPLEMENTED` | Multi-sample lot inspection management with Schedule IV statistical sampling assessment, physical metrology separation (Rule 24 disclaimer), and offline ZIP evidence export. |
| Section 36 Notices & Compounding (Phase 2.2) | `IMPLEMENTED` | Statutory Section 48 compounding assessment (1st, 2nd, recurring offence tiers with statutory ceilings and Section 48(2) bar) and draft compounding memo PDFs. |
| Gravimetric Net-Weight & MPE Testing (Phase 2.3) | `IMPLEMENTED` | Rule 24 & Schedule IV Table 2 MPE verification, sample mean deficit checks, double-MPE rejections, and printable PDF memos. |
| Rule 26 Statutory Exemptions (Phase 2.4) | `IMPLEMENTED` | Small pack $\le 10\text{g/ml}$ (Rule 26(a)), bulk $> 50\text{kg}$ (Rule 26(b)), institutional consumer (Rule 26(c)/2(p)), and multi-piece/combination packaging (Rules 21-22). |
| Geofence & Offline Sync Queue (Phase 2.5) | `IMPLEMENTED` | GPS boundary validation, Next.js offline sync client with localStorage queue, and SHA-256 provenance hash chaining. |
| Statutory PDF & Section 36 Notice Reports | `IMPLEMENTED` | ReportLab generator producing branded MetrologyMitra memorandums with SHA-256 fingerprints. |
| Supervisor Analytics & Heatmaps | `IMPLEMENTED` | Regional KPIs, state/district violation clusters, and repeat-offender intelligence. |
| 7 Controlled Demo Presets | `IMPLEMENTED` | Seeded idempotently via `POST /api/v1/inspections/demo-seed` and one-click UI button. |

---

## 4. Database Architecture
- **Alembic Head:** `0005_gravimetric_and_exemptions` (Revises: `0004_batch_and_enforcement` $\to$ `0003_regulatory_intelligence` $\to$ `0002_audit_logs` $\to$ `0001_initial_schema`).
- **Domain Tables (15):**
  - `users`: Authentication, bcrypt password hashes, roles (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).
  - `products`: Product reference records.
  - `gravimetric_tests`: Physical tare/gross sample scale measurements, Schedule IV MPE statistics, and lot verdicts.
  - `inspection_batches`: Batch lot containers, lot size, sample size, location, status, and summary stats.
  - `inspections`: Central inspection session, `batch_id`, `language_detected`, location, status, overall result, `geo_verified`, `offline_client_id`, `synced_at`.
  - `inspection_images`: Uploaded photographs, sequence numbers, image types, `sha256_hash`, `quality_gate_result`.
  - `ocr_results`: Tesseract raw text, confidence score, token bounding boxes, processing time.
  - `declarations`: Extracted/human-verified statutory fields, `digital_listing_data`, `measurement_data`.
  - `legal_rules`: 18 seeded statutory rules, parameters, version, `effective_from`, `effective_to`, `channel` (`PHYSICAL_PACKAGE`, `ECOMMERCE`, `BOTH`), `source_version`.
  - `compliance_checks`: Evaluated checks per rule, observed value, result (`PASS`, `FAIL`, `REVIEW`), confidence, reason.
  - `violations`: Structured legal infractions with severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and rule citations.
  - `evidence`: Spatial bounding box and textual proof snippets linking checks and violations.
  - `reports`: Generated PDF, Section 36 draft notice, and JSON export file records.
  - `enforcement_notices`: Section 36 and Section 48 compounding notices, offence count, fee, challan reference, and status.
  - `audit_logs`: Chronological audit trail events linking actor user ID, action type, entity, and JSON metadata.
  - `alembic_version`: Database migration tracking table.

---

## 5. Verified Test Suite Results
- **Phase 2.0, 2.1, 2.2 Test Suite (`test_phase2_0_2_1_2_2.py`):** `PASS` (Devanagari numerals, Indic bilingual extraction, Schedule IV sampling, ZIP evidence manifest, Section 48 compounding calculator, Challan PDF).
- **Master Phase 1.7–1.9 Test Suite (`test_phase1_7_1_8_1_9.py`):** `PASS` (7/7 modules).
- **Integration & Hardening Suite (`test_phase1_4_1_5_1_6.py`):** `PASS` (13/13 scenarios).
- **Regression Suite (`test_phase1_3.py`):** `PASS` (13/13 scenarios).
- **Next.js Production Build (`npm run build`):** `PASS` (10/10 routes compiled with 0 lint errors and 0 type errors).

---

## 6. Known Limitations & Statutory Boundaries
1. **Decision Support Nature:** System is an assistive tool for field Legal Metrology Officers; it does not issue autonomous penalties or legal sanctions.
2. **Measurement Calibration:** Camera-based numeral height measurement requires reference object calibration; uncalibrated images strictly return `CheckResult.REVIEW`.
3. **Reference Catalog Scope:** Barcode/MRP validation uses a controlled demonstration catalog, not a live government database.
4. **Registry Verification:** Rule 27 manufacturer registration check verifies postal completeness and outputs `REVIEW` when external government validation is unavailable.
