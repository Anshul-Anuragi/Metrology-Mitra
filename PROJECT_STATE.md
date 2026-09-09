# Project State — MetrologyMitra (SIH26034)

> **Single Source of Truth** for maintaining, resuming, and verifying the **MetrologyMitra** codebase across development sessions.

---

## 1. Current Status
- **Official Project Name:** **MetrologyMitra**
- **Problem Statement ID:** SIH26034 — Development of a Software Application for Compliance Inspection of Packaged Commodities
- **Regulatory Authority:** Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Government of India
- **Current Completion Milestone:** Phases 0.1 through 4.4, Real-Data Hardening Sprint, and Inspector Dashboard Completed/Compliant Audit Completed, Benchmarked & Integrated (All 20 Automated Backend Test Suites PASS 100%; Next.js 15/15 Routes Build PASS; Phase 4.1 Ministry Readiness 16/16 Golden Scenarios PASS 100%; Phase 4.2 Real Image Validation 28/28 Evaluated with 0 False Certainty; Phase 4.3 Perception Benchmark 28/28 Evaluated with 0 False Certainty & 0 Source Mutation; Phase 4.4 Production Pipeline & UI Evidence Fusion Card Integrated; Real-Data Hardening Sprint Completed with 107 variants, 3,978 tokens, 87 declarations, 8 barcodes, and 0 false certainty violations; Inspector Dashboard Dual-Dimension KPIs, Presets, and Completed-Compliant Seed Finalization Hardened).
- **Current Completion Milestone:** Phases 0.1 through 4.4, Real-Data Hardening Sprint, Inspector Dashboard Completed/Compliant Audit, and Final Frontend Product Sprints 1–3 Completed, Benchmarked & Released (All 20 Automated Backend Test Suites PASS 100%, 136.62s; Next.js 15/15 Routes Production Build PASS; Phase 4.1 Ministry Readiness 16/16 Golden Scenarios PASS 100%; Phase 4.2 Real Image Validation 28/28 Evaluated with 0 False Certainty; Phase 4.3 Perception Benchmark 28/28 Evaluated with 0 False Certainty & 0 Source Mutation; Phase 4.4 Production Pipeline & UI Evidence Fusion Card Integrated; Real-Data Hardening Sprint Completed with 107 variants, 3,978 tokens, 87 declarations, 8 barcodes, and 0 false certainty violations; Full Inspection Workstation Redesign & Curated SIH26034 Benchmark Showcase Released; Zero Backend Touch Safety Invariant Maintained).

---

## 2. Architecture
- **Perception Layer:** Local Tesseract OCR 5 (`pytesseract`) + local ZXing-C++ barcode/QR decoding with bilingual English/Hindi Devanagari numeral translation (०-९ $\to$ 0-9) and script detection (`ENG`, `HIN`, `MIXED`).
- **Rule Engine Layer:** Deterministic statutory evaluation engine executing 18 encoded compliance checks based on selected provisions of the Legal Metrology (Packaged Commodities) Rules, 2011, Rule 26 statutory exemptions, and Rules 21–22 special packaging.
- **Service Layer (`backend/app/services`):** Segregated services for Image Quality Pre-Flight Gating, OCR Text & Coordinate Extraction, Schedule II Numeral Height Measurement, E-Commerce Listing Cross-Check, Rule 19 + Fifth Schedule Batch Statistical Sampling & ZIP Bundle Exporter, First Schedule & Rule 19 + Sixth Schedule Gravimetric Net-Quantity & MPE Verification Engine, Rule 26 Statutory Exemptions Evaluator, Field Geofence & Provenance Chaining, Section 48 Statutory Compounding Assessment, Violation Synthesis, Evidence Linking, ReportLab PDF Generation (Inspection, Compounding, Panchnama, and Consolidated Dossier Reports), Supervisor Analytics, Case Intelligence & Supervisor Triage, and Investigation Dossier Management & Synthesis.
- **Validation Harness Layer (`backend/app/validation` & `backend/scripts`):** Ministry Readiness validation harness executing 16 comprehensive golden scenarios covering end-to-end edge cases, full statutory schedules, legal traceability assertions, and safety boundary constraints.
- **API Layer (`backend/app/api/v1`):** FastAPI async routers enforcing JWT Authentication, Role-Based Access Control (RBAC), Object-level Inspector isolation, and Permanent Finalization Mutation Locks (`HTTP 409 Conflict`).
- **Data Layer:** PostgreSQL 16 managed via SQLAlchemy 2.0 AsyncIO and Alembic migrations (Head: `0007_investigation_dossiers`).
- **Frontend Layer (`frontend/src`):** Responsive Web Application built with Next.js 14 App Router, React 18, TypeScript, and Tailwind CSS.
- **Dashboard Layer (`/inspections`):** Dual-dimension portfolio intelligence separating Lifecycle Status (`CREATED`, `PROCESSING`, `REVIEW_REQUIRED`, `COMPLETED`) from Statutory Verdict (`COMPLIANT`, `NON_COMPLIANT`, `NEEDS_REVIEW`), supported by serialized `@computed_field statutory_verdict` and scoped demo seed fixtures.

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
| Batch / Lot Inspections (Phase 2.1) | `IMPLEMENTED` | Multi-sample lot inspection management with Rule 19 + Fifth Schedule statistical sampling assessment, physical metrology separation, and offline ZIP evidence export. |
| Section 36 Notices & Compounding (Phase 2.2) | `IMPLEMENTED` | Statutory Section 48 compounding assessment (1st, 2nd, recurring offence tiers with statutory ceilings and Section 48(2) bar) and draft compounding memo PDFs. |
| Gravimetric Net-Weight & MPE Testing (Phase 2.3) | `IMPLEMENTED` | First Schedule MPE verification (Tables I–IV), Rule 19 + Sixth Schedule net-quantity testing methodology, sample mean deficit checks, double-MPE rejections, Seventh Schedule data sheets, and physical metrology decision-support disclaimer. |
| Rule 26 Statutory Exemptions (Phase 2.4) | `IMPLEMENTED` | Factual verification-gated exemptions: Rule 26(a) small pack ($\le 10\text{g/ml}$ with tobacco exclusion proviso), Rule 26(b) fast food, Rule 26(c) DPCO formulations, Rule 26(d) agricultural farm produce ($> 50\text{kg}$ with non-farm bulk `NEEDS_REVIEW`), Rule 26(c)/2(p) institutional consumer with contract & marking verification, and special packaging (Rules 21-22). |
| Geofence & Offline Sync Queue (Phase 2.5) | `IMPLEMENTED` | GPS boundary validation against Indian territory, Next.js offline sync client with localStorage queue, and SHA-256 provenance hash chaining. |
| Rule 27 Pre-Packer Registry (Phase 2.6) | `IMPLEMENTED` | Central & State pre-packer registry table, verification engine (`REGISTERED_VALID`, `EXPIRED`, `UNREGISTERED_VIOLATION`, `NEEDS_REVIEW`), and SHA-256 certificate fingerprints. |
| Section 15 Seizures & Panchnama (Phase 2.7) | `IMPLEMENTED` | Search & seizure recording, 2-witness Panchnama requirements, sample seal tagging, itemized inventory, and Form VI Panchnama PDF generation. |
| Section 49 Corporate Liability (Phase 2.8) | `IMPLEMENTED` | Corporate entity tracking (CIN), Section 49(2) Form I nominated director liability resolution vs Section 49(1) default person-in-charge liability. |
| Operational Case Intelligence & Supervisor Triage (Phase 2.9) | `IMPLEMENTED` | Evidence Completeness Index (0-100%) across 6 facets, actionable gap directives, Case Priority Score (0-100), advisory non-binding statutory next-steps, and supervisor operational triage queue. |
| Market Surveillance Investigation Dossiers (Phase 3.0 Completed) | `IMPLEMENTED` | Multi-inspection operational case containers, non-judicial lifecycle, factual cross-inspection synthesis, observed finding patterns, Section 15 seizure aggregation, Section 49 director review, 14-section ReportLab consolidated PDF export, Next.js workspace, and statutory boundary hardening. |
| Ministry Readiness & Validation Harness (Phase 4.1) | `IMPLEMENTED` | 16 deterministic golden scenarios (SCENARIO-01 to 16), 100% offline synthetic fixtures, statutory schedule traceability assertions, safety boundary guards, asynchronous `ValidationRunner`, standalone CLI (`run_validation.py`), and CI JSON export. |
| Real Package Image Validation (Phase 4.2) | `IMPLEMENTED` | 28 real-world package photographs, inventory registry, ground-truth schema, zero false certainty safety invariant, structured review tagging, baseline CLI runner and technical reports. |
| Evidence-Driven Perception Preprocessing (Phase 4.3 Sub-Batch 1) | `IMPLEMENTED` | Immutable RAW_MASTER ingress bytes, SHA-256 evidence integrity, 6 deterministic derivative variants, in-memory cryptographic provenance lineage (`original_image_hash`, `parent_variant_hash`, `processed_image_hash`), mathematically verified adaptive thresholding, dimension safety bounds, deterministic output bytes, run-specific timestamp semantics, non-destructive file handling, strict separation from statutory rule engine. |
| Multi-Variant OCR Consensus (Phase 4.3 Sub-Batch 2) | `IMPLEMENTED` | Execution across normalized derivatives, isolated variant result structures, token frequency alignment, stability scoring, divergent declaration conflict detection, and deterministic primary variant selection. |
| Barcode Quorum & Declaration Fusion (Phase 4.3 Sub-Batch 3) | `IMPLEMENTED` | Multi-format input support (PIL Image, bytes, Path), multi-variant barcode quorum voting with master catalog validation, statutory declaration fusion across variants (`CONFIRMED`, `PROBABLE`, `CONFLICTING`, `MISSING`), and automatic review escalation for OCR disagreements. |
| Multi-Modal Evidence Fusion Coordinator (Phase 4.3 Sub-Batch 4) | `IMPLEMENTED` | Orchestrates optical pre-flight quality, image derivatives, OCR token consensus, barcode quorum voting, statutory declaration synthesis, and physical scale telemetry into an immutable `UnifiedEvidencePacket`. |
| Real-Package Benchmark Validation (Phase 4.3 Sub-Batch 5) | `IMPLEMENTED` | Evaluated 28/28 real-world physical package photographs, 0 false certainties, 0 source file mutations, generated `phase4_3_benchmark_report.json` and `phase4_3_benchmark_report.md`. |
| Production Pipeline & UI Integration (Phase 4.4) | `IMPLEMENTED` | Full end-to-end integration into `pipeline_service.py`, enrichment of extracted statutory declarations, storage of fused evidence in `raw_extractions["fused_evidence"]`, and interactive `EvidenceFusionCard` in Next.js frontend inspection view (`/inspections/[id]`). |
| Inspector Dashboard Completed/Compliant Integrity & KPIs | `IMPLEMENTED` | Dimensional orthogonality separating Lifecycle Status from Statutory Verdict, serialized `@computed_field statutory_verdict`, scoped idempotent demo presets with rule-engine-evaluated Tata Sampann compliant case, 6-card KPI strip, quick filter presets, and dedicated automated test suite (`test_inspector_dashboard_completed_compliant.py`). |
| Statutory PDF & Section 36 Notice Reports | `IMPLEMENTED` | ReportLab generator producing branded MetrologyMitra memorandums with SHA-256 fingerprints. |
| Supervisor Analytics & Heatmaps | `IMPLEMENTED` | Regional KPIs, state/district violation clusters, and repeat-offender intelligence. |
| 7 Controlled Demo Presets | `IMPLEMENTED` | Seeded idempotently via `POST /api/v1/inspections/demo-seed` and one-click UI button. |

---

## 4. Database Architecture
- **Alembic Head:** `0007_investigation_dossiers` (Revises: `0006_registry_seizures_corporate` $\to$ `0005_gravimetric_and_exemptions` $\to$ `0004_batch_and_enforcement` $\to$ `0003_regulatory_intelligence` $\to$ `0002_audit_logs` $\to$ `0001_initial_schema`).
- **Domain Tables (21):**
  - `users`: Authentication, bcrypt password hashes, roles (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).
  - `products`: Product reference records.
  - `gravimetric_tests`: Physical tare/gross sample scale measurements, First Schedule MPE statistics, and lot verdicts.
  - `packer_registrations`: Rule 27 pre-packer registration number, entity name, address, jurisdiction level, state, valid dates, certificate hash.
  - `seizure_records`: Section 15 seizure records, premises, 2 independent witnesses, grounds, custody location, SHA-256 seal hash.
  - `seizure_items`: Itemized seized commodities, quantities, sample packages taken, and seal tag numbers.
  - `companies`: Corporate entity records (CIN, legal name, registered office, state).
  - `nominated_directors`: Section 49(2) Form I nominated directors (DIN, designation, notice date, validity).
  - `investigation_dossiers`: Phase 3.0 multi-inspection case container, unique dossier number, status, priority, target entity name, company FK, lead supervisor FK, tags, audit metadata.
  - `dossier_inspections`: Phase 3.0 associative junction table linking dossiers and inspections with unique constraint `uq_dossier_inspection`, relevance notes, and adder audit tracking.
  - `inspection_batches`: Batch lot containers, lot size, sample size, location, status, and summary stats.
  - `inspections`: Central inspection session, `batch_id`, `company_id`, `language_detected`, location, status, overall result, `geo_verified`, `offline_client_id`, `synced_at`.
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
- **Phase 4.4 Real-Data Hardening Suite (`test_phase4_4_real_data_hardening.py`):** `PASS` (13/13 tests validating optical quality formatting, conflict non-collapse invariants, compatible text corroboration, pipeline confidence capping, finalization mutation locks, raw master immutability, legal engine sole authority, zero false certainty, LOCAL_CONTRAST_ENHANCED determinism/provenance, comma-formatted MRP & USP disambiguation, net quantity serving size filtering, disaggregated root cause & recoverability classification, and real package image execution).
- **Phase 4.4 Production Inspection Pipeline Suite (`test_phase4_4_production_pipeline.py`):** `PASS` (2/2 end-to-end real photograph and virtual image integration tests).
- **Phase 4.3 Evidence Fusion Suite (`test_phase4_3_subbatch4_evidence_fusion.py`):** `PASS` (5/5 multi-modal coordinator, scale telemetry & provenance tests).
- **Phase 4.3 Declaration Fusion Suite (`test_phase4_3_subbatch3_declaration_fusion.py`):** `PASS` (6/6 barcode quorum & declaration fusion tests).
- **Phase 4.3 Multi-Variant OCR Suite (`test_phase4_3_subbatch2_multivariant_ocr.py`):** `PASS` (6/6 multi-variant consensus & conflict detection tests).
- **Phase 4.3 Perception Robustness Suite (`test_phase4_3_perception.py`):** `PASS` (12/12 invariant & mathematical verification tests).
- **Phase 4.3 Standalone Benchmark Runner (`scripts/run_phase4_3_benchmark.py`):** `PASS` (28/28 real photographs evaluated across multi-variant perception, 0 false certainties, 0 source mutations, reports generated in `reports/phase4_3_benchmark_report.*`).
- **Phase 4.2 Real Image Validation Suite (`test_phase4_2_real_image_validation.py`):** `PASS` (10/10 real-image integration & safety invariant tests).
- **Phase 4.2 Standalone CLI Runner (`scripts/run_phase4_2_validation.py`):** `PASS` (28/28 real-image evaluations, 0 false certainties, baseline JSON & MD reports generated).
- **Phase 4.1 Validation Harness Suite (`test_phase4_1_validation.py`):** `PASS` (9/9 async & sync verification tests).
- **Phase 4.1 Standalone CLI Runner (`scripts/run_validation.py`):** `PASS` (16/16 golden scenarios passing, 100.0% success rate, pretty terminal & CI JSON output).
- **Phase 3.0 Hardening & Consolidated Evidence PDF Suite (`test_phase3_0_subbatch5_hardening_pdf.py`):** `PASS` (25/25 tests).
- **Phase 3.0 Investigation Dossiers Suite (`test_phase3_0_dossiers.py`):** `PASS` (23/23 tests).
- **Phase 3.0 Sub-Batch 1 Models Suite (`test_phase3_0_subbatch1_dossier_models.py`):** `PASS` (10/10 tests).
- **Official Legal Dataset Audit Suite (`test_official_legal_dataset_audit.py`):** `PASS` (10/10 tests).
- **Phase 2.9 Case Intelligence Suite (`test_phase2_9_case_intelligence.py`):** `PASS` (13/13 tests).
- **Phase 2.6, 2.7, 2.8 Test Suite (`test_phase2_6_2_7_2_8.py`):** `PASS` (12/12 tests).
- **Phase 2.3, 2.4, 2.5 Test Suite (`test_phase2_3_2_4_2_5.py`):** `PASS` (11/11 tests).
- **Phase 2.0, 2.1, 2.2 Test Suite (`test_phase2_0_2_1_2_2.py`):** `PASS` (10/10 tests).
- **Master Phase 1.7–1.9 Test Suite (`test_phase1_7_1_8_1_9.py`):** `PASS` (10/10 tests).
- **Integration & Hardening Suite (`test_phase1_4_1_5_1_6.py`):** `PASS` (13/13 tests).
- **Regression Suite (`test_phase1_3.py`):** `PASS` (13/13 tests).
- **Regression Suite (`test_phase1_3.py`):** `PASS` (13/13 tests).
- **Completed/Compliant Dashboard Data Audit Suite (`test_inspector_dashboard_completed_compliant.py`):** `PASS` (7/7 tests).
- **Total Master Backend Test Suites:** **20 / 20 SUITES PASSED (100%)** (220 tests, 139.11s).
- **Frontend Production Build (`npm run build`):** `PASS` (15/15 routes compiled with 0 lint errors and 0 type errors).
- **Frontend Product Redesign (SIH26034 Operating System):** `COMPLETE` (AppShell workstation navigation, Command Center hero, 4-meter Readiness Health, Priority Actions panel, and immutable lock banner).

---

## 6. Official Statutory Traceability & Corpus Architecture (SIH-OFFICIAL-LEGAL-DATASET-2011)

### Legal Metrology (Packaged Commodities) Rules, 2011 — Core Statutory Traceability Table

| Statutory Provision | Official Corpus Subject / Purpose | MetrologyMitra Implementation & Verification |
|---|---|---|
| **Rule 3** | Scope of Chapter II (Pre-packaged commodities intended for retail sale, subject to Rule 26 exceptions) | Inspection-local statutory gatekeeper. Chapter II checks strictly bypass non-retail/bulk commodities. Never aggregated into collective guilt. |
| **Rule 5 + Second Schedule** | Commodities to be packed in specified quantities (Standard pack sizes: Baby food, Biscuits, Bread, Tea, Edible oil, etc.) | Deterministic check on net quantity matching Second Schedule standard tiers; non-standard sizes flagged for officer review. |
| **Rule 6(1)(a)–(g)** | Mandatory declarations on retail packages (Name/address, Generic name, Net qty, Mfg date, MRP, Consumer care) | Core 18 deterministic compliance checks with multilingual English/Devanagari OCR parsing. |
| **Rule 7 & Schedule II** | Minimum height of numerals and letters based on Principal Display Panel (PDP) area tiers | Schedule II Table 1 tiers ($1.0\text{--}6.0\text{ mm}$). Uncalibrated images strictly output `REVIEW` under prototype disclaimer. |
| **Rule 18(1)–(2)** | Wholesale/Retail pricing & Maximum Retail Price (MRP) compliance | Neutral reference catalog discrepancy outputs `CheckResult.REVIEW` (never auto-inferring tampering). |
| **Rule 19 + Fifth Schedule** | Manner of selection of samples of packages for inspection | Sample size determination: $\le 4,000$ packages $\to$ 32 sample units; $> 4,000$ packages $\to$ 80 sample units. |
| **Rule 19 + Sixth Schedule** | Determination of Net Quantity and physical scale testing methodology | Gravimetric net-content determination, tare weight assessment, sample mean $\bar{x} \ge Q_n$, and allowable negative error limits. |
| **Rule 19 + Seventh Schedule** | Form of report / data-sheet for recording test results | Structured data records in `gravimetric_tests` and printable Gravimetric Test Record PDF. |
| **First Schedule** | Maximum Permissible Errors (MPE) on net quantity (Tables I–IV: Mass/Volume, Length, Area, Count) | Exact statutory MPE boundaries encoded across all tiers; negative errors beyond $2\times\text{MPE}$ trigger critical defect rejection. |
| **Rule 21 & 22** | Special packaging provisions: Multi-piece and Combination packages | Piece count declarations, individual net content declarations, and multi-commodity itemized evaluation. |
| **Rule 24** | Declarations applicable to wholesale packages (Chapter III) | Wholesale package declarations (Name/address, Identity, Total Net Quantity, Wholesale Price); strictly distinguished from retail packages and MPE. |
| **Rule 26(a)–(d)** | Statutory exemptions ($\le 10\text{g/ml}$, fast food, DPCO formulations, agricultural bulk $> 50\text{kg}$) | Factual verification gating. Agricultural bulk non-farm commodities strictly gated to `NEEDS_REVIEW`. |
| **Rule 27** | Pre-Packer & Manufacturer Registration with Central/State Controllers | Central & State registry lookup (`packer_registrations`), ₹500 fee, 90-day application period context, and certificate SHA-256 hashes. |
| **Section 15 Act** | Statutory Search, Seizure & Panchnama | 2 independent witnesses, itemized inventory, custody location, and Form VI Panchnama PDF. |
| **Section 48 Act** | Compounding of Offences (First offence vs 3-year recurrence bar under Section 48(2)) | Statutory tiered fee calculations, Section 48(2) non-compoundable bar enforcement. |
| **Section 49 Act** | Offences by Companies (Section 49(2) Form I nominated director vs 49(1) person in charge) | Nominated director registry; strictly informational review in dossiers without personal liability. |

---

## 7. Known Limitations & Statutory Boundaries
1. **Decision Support Nature:** System is an assistive tool for field Legal Metrology Officers; it does not issue autonomous penalties or legal sanctions.
2. **Measurement Calibration:** Camera-based numeral height measurement requires reference object calibration; uncalibrated images strictly return `CheckResult.REVIEW`.
3. **Reference Catalog Scope:** Barcode/MRP validation uses a controlled demonstration catalog, not a live government database.
4. **Registry Verification:** Rule 27 manufacturer registration check verifies postal completeness and outputs `REVIEW` when external government validation is unavailable.
5. **Authoritative SIH Legal Reference Corpus:** Verified against official SIH provided document `"The legal Metrology official dataset in ocr english.pdf"` (Gazette Notification G.S.R. 202(E) / 203(E) dated 7 March 2011). The system explicitly preserves this as historical 2011 notification baseline rather than asserting universal unamended current-law equivalence.
6. **Dossier Boundary Guarantee:** Investigation dossiers operate strictly as non-judicial case-management containers. Dossiers do not determine statutory guilt, cannot override individual inspection determinations, do not infer Section 49 personal director liability, and maintain strict cascade safety.
