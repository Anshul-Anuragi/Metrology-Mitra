# Project Roadmap & Implementation Phases

## Phase Breakdown

### Phase 0.1 — Domain Modeling & Architecture Blueprint
- Define core domain entities (`users`, `products`, `inspections`, `inspection_images`, `ocr_results`, `declarations`, `legal_rules`, `compliance_checks`, `violations`, `evidence`, `reports`).
- Establish strict separation between AI Perception, Deterministic Legal Reasoning, and Human Decisions.

### Phase 0.2 — PostgreSQL Schema Design & Relational Modeling
- Define PostgreSQL DDL, native ENUMs, foreign keys, cascade delete rules, unique constraints, and indexes.

### Phase 0.3 — Backend Scaffolding & Project Setup
- FastAPI async application, SQLAlchemy 2.0 ORM, Docker Compose environment with PostgreSQL 16 on port 5434:5432.

### Phase 0.4 — Database Migrations & Single Source of Truth
- Alembic async migration configuration, initial schema migration `0001_initial_schema`, 100% schema parity.

### Phase 0.5 — JWT Authentication & RBAC Layer
- Password hashing with bcrypt, JWT token generation, role-based dependencies (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).

### Phase 0.6 — Inspection Core API & Storage Abstraction
- Full inspection lifecycle API, GPS validation, storage service abstraction, image attachment, sequence tracking, declaration updates.

### Phase 0.7 — Legal Rules Knowledge Base & Deterministic Rule Engine
- Seeded statutory LMPC 2011 rules, deterministic rule evaluator, `POST /evaluate` and `GET /checks` endpoints.

### Phase 0.8 — OCR + Structured Declaration Extraction Pipeline
- Tesseract 5 OCR integration, image preprocessor, spatial token extraction, deterministic LMPC Rule 6 declaration parser, human verification protection.

### Phase 0.9 — End-to-End Automated Pipeline, Violation & Evidence Generation
- Unified Pipeline API: `POST /api/v1/inspections/{inspection_id}/pipeline` (OCR $\to$ Extraction $\to$ Rule Engine $\to$ Violations $\to$ Evidence).

### Phase 1.0 — PDF Reports & Section 36 Notice Generation
- ReportLab generator for PDF compliance memorandums, draft Section 36 notices, and JSON export bundles.

### Phase 1.1 — Supervisor Analytics & Brand Repeat-Offender Intelligence
- Enforcement KPIs, time-series trends, state/district violation heatmaps, repeat offenders rank, and failing rule frequencies.

### Phase 1.2 — Next.js Responsive Web Application & Inspection Workspace
- Complete inspector workspace with bounding box overlays, human review modal, and supervisor portal.

### Phase 1.3 — Advanced Field Intelligence
- Local barcode/QR decoding (ZXing-C++), controlled master catalog comparison, and pre-flight image diagnostics.

### Phases 1.4–1.6 — Human Review, Finalization Lock & Chronological Audit Trail
- Multi-action adjudication workspace (`CONFIRM`, `CORRECT`, `REQUEST_RETAKE`, `MARK_UNRESOLVED`), permanent backend mutation lock (`HTTP 409 Conflict`), and chronological audit logs.

### Phases 1.7–1.9 — 18 Statutory Rules, Measurement Assistant & E-Commerce Cross-Check
- 18 statutory rules with temporal versioning and channel filtering, SHA-256 evidence hashes, Rule 7 Schedule II numeral height assistant, and Rule 6(10) digital marketplace cross-check.

### Phase 2.0 — Indic Multilingual Perception & Devanagari Numeral Engine
- Multi-script OCR parsing for bilingual Hindi/English declarations under Rule 6(1), Devanagari numerals translation (०-९ $\to$ 0-9), and script language detection (`ENG`, `HIN`, `MIXED`).

### Phase 2.1 — Batch / Lot Inspection & Statistical Sampling (Rule 19 + Fifth Schedule)
- Wholesale depot / warehouse lot management, Rule 19 + Fifth Schedule statistical sampling assessment for label declarations, physical metrology separation, and offline ZIP evidence bundle exporter with SHA-256 manifest.

### Phase 2.2 — Statutory Section 36 Notice Tracking & Section 48 Compounding Assessment
- Statutory Section 48 compounding assessment (1st, 2nd, and recurring offence tiers with statutory ceilings and Section 48(2) non-compoundable statutory bar), versioned legal metadata, draft notice lifecycle management, and draft compounding memo PDF generator with explicit non-issuance disclaimers.

### Phase 2.3 — Gravimetric Net-Quantity, MPE & Testing Methodology (First Schedule, Rule 19 + Sixth & Seventh Schedules)
- Statutory Maximum Permissible Error (MPE) table lookup (First Schedule Tables I–IV), Rule 19 + Sixth Schedule physical scale testing methodology, sample mean net content ($\bar{x}$) calculation, standard deviation ($s$), negative error defectives count, critical double-MPE rejection, Seventh Schedule inspection data recording, and printable Gravimetric Test Record PDF.

### Phase 2.4 — Rule 26 Statutory Exemptions & Special Package Provisions
- Deterministic statutory exemption evaluation under Rule 26 (Rule 26(a) small pack $\le 10\text{g/ml}$, Rule 26(b) bulk agricultural $> 50\text{kg}$, Rule 26(c)/Rule 2(p) institutional consumer) and special packaging rules (Rule 21 multi-piece piece count and Rule 22 combination pack multi-commodity rules) integrated into the deterministic statutory rule engine.

### Phase 2.5 — Field Geofence Verification, Offline Sync Queue & Inspection Provenance
- Field GPS coordinate validation against official Indian territorial bounds (6°N–38°N, 68°E–98°E), offline inspection draft synchronization queue (IndexedDB/localStorage sync client), and SHA-256 digital event provenance chaining.

### Phase 2.6 — Rule 27 Statutory Pre-Packer & Manufacturer Registration Registry
- Authoritative central and state pre-packer registry table (`packer_registrations`), deterministic Rule 27 lookup engine (`REGISTERED_VALID`, `EXPIRED`, `UNREGISTERED_VIOLATION`, `NEEDS_REVIEW`), and SHA-256 digital registration certificate fingerprints.

### Phase 2.7 — Section 15 Seizure Memorandum, Panchnama & Evidence Chain of Custody
- Statutory search & seizure recording under Section 15 of Legal Metrology Act, 2009 and Rule 29, 2-independent-witness Panchnama attestation, sample seal tag tracking, itemized non-compliant commodity inventory, and official printable Form VI Panchnama PDF generator.

### Phase 2.8 — Section 49 Corporate Entity & Nominated Director Liability Framework
- Corporate entity registration (CIN, registered office), Section 49(2) Form I nominated director tracking (DIN, designation, board notice date), and statutory liability evaluation determining notice recipients (nominated Director under Section 49(2) vs default persons in charge under Section 49(1)).

### Legal Dataset Audit & Statutory Correction Pass
- Comprehensive audit of deterministic rule engine, database records, and citations against official SIH Legal Metrology dataset (`SIH-OFFICIAL-LEGAL-DATASET-2011`).
- Verified neutral Rule 18 reference-price mismatch evaluation (`CheckResult.REVIEW`, never auto-inferring tampering).
- Verified Rule 19 & Fifth Schedule sampling boundaries (<4000 $\to$ 32, >4000 $\to$ 80) and Sixth Schedule physical weighing / net-quantity testing methodology.
- Verified official First Schedule MPE boundaries across all mass, length, area, and count tiers (Tables I–IV).
- Verified Rule 5 & Second Schedule specified standard packaging quantities.
- Verified Rule 24 applies strictly to declarations on wholesale packages under Chapter III (not MPE/net-quantity).
- Corrected Rule 26 statutory subclauses: 26(a) $\le 10\text{g/ml}$ + 10g-20g proviso + tobacco exclusion, 26(b) fast food, 26(c) DPCO formulations, 26(d) agricultural produce $>50\text{kg}$ with strict non-farm bulk gating to `NEEDS_REVIEW`.
- Realigned Institutional consumers to Rule 2(p) read with Rule 3, and Multi-piece / Combination packages to Rules 21 & 22 special packaging provisions.

### Phase 2.9 — Operational Case Intelligence, Evidence Completeness & Supervisor Triage
- **Evidence Completeness Index (0–100%):** Six-facet evaluation model (Visual Packaging, Mandatory Declarations, Perception Quality, Regulatory Registry, Physical Measurement, Corporate Governance) with transparent application-level weights and actionable gap directives.
- **Case Priority Engine (0–100):** Deterministic operational prioritization (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) factoring violation severities, unresolved review items, repeat offender history, and inspection age without altering legal determinations.
- **Advisory Statutory Action Guidance:** Non-binding next steps (`is_advisory = True`) for field officers and supervisors (photo retake guidance, registry verification prompts, draft notice suggestions, compounding calculations).
- **Supervisor Operational Triage Workspace:** Interactive prioritized case triage queue (`/inspections/triage`) with priority filtering, search, and quick review routing.

### Phase 3.0 — Market Surveillance Dossiers & Multi-Inspection Investigation Engine (Sub-Batches 1–4)
### Phase 3.0 — Market Surveillance Dossiers & Multi-Inspection Investigation Engine (COMPLETED)
- **Sub-Batch 1 (Data Model & Persistence):** Operational case-management container tables `investigation_dossiers` and `dossier_inspections` (migration `0007_investigation_dossiers`), non-judicial statuses (`ACTIVE`, `EVALUATION`, `NOTICE_REVIEW`, `COMPOUNDING_REVIEW`, `CLOSED`), unique constraint `uq_dossier_inspection`, strict separation from statutory verdicts.
- **Sub-Batch 2 (Dossier Service & Synthesis):** `DossierService` implementing operational CRUD, linking/unlinking inspections (preserving underlying records 100% intact), factual cross-inspection synthesis (verdict counts, territorial footprints, observed finding frequency patterns with non-judicial labels, aggregated Section 15 seizure quantities, Section 49 director reviews).
- **Sub-Batch 3 (API & RBAC Layer):** 7 REST endpoints under `/api/v1/dossiers/` with supervisor/admin creation & status management, and object-level inspector access scoping (inspectors view only dossiers linking their own authored inspections).
- **Sub-Batch 3 (API & RBAC Layer):** REST endpoints under `/api/v1/dossiers/` with supervisor/admin creation & status management, and object-level inspector access scoping (inspectors view only dossiers linking their own authored inspections).
- **Sub-Batch 4 (Next.js Investigation Workspace):** Frontend navigation, Dossiers dashboard (`/dossiers`) with KPI metrics, status/priority filters, and creation modal; Dossier Investigation Workspace (`/dossiers/[id]`) with 6 operational tabs (Overview & Synthesis, Linked Inspections with link/unlink modal, Observed Finding Patterns, Recorded Seizures, Corporate Governance, Timeline & Audit Log) and prominent statutory boundary disclaimers.
- **Sub-Batch 5 (Final Hardening, PDF Export & Legal Corpus Validation):**
  - **Statutory Corpus Validation:** Authoritative baseline verified against official SIH reference document (`The legal Metrology official dataset in ocr english.pdf` / Gazette Notification G.S.R. 202(E) & 203(E) dated 7 March 2011). Fully verified across all 34 rules and 7 schedules. Preserved as historical 2011 notification corpus.
  - **Consolidated Evidence PDF Export:** ReportLab generator producing printable investigation dossier summary with 14 mandatory sections, SHA-256 evidence digests, and statutory non-judicial disclaimers.
  - **Boundary Hardening:** Verified that dossiers never compute collective compliance verdicts, cannot override individual inspection results, enforce explicit corporate associations without fuzzy matching, never auto-infer Section 49 personal director liability, and maintain cascade safety (deleting a dossier leaves underlying inspections and violations 100% intact).
### Phase 4.1 — Ministry Readiness & Real-World Validation: Validation Harness & Scenario Dataset (COMPLETED)
- **Reusable Validation Scenario Infrastructure (`backend/app/validation`):**
  - Scenario model (`ValidationScenario`) and 16 deterministic golden scenarios (`SCENARIO-01` through `SCENARIO-16`) covering retail compliance, missing declarations, low-quality optical perception, bilingual/Devanagari numerals, physical gravimetric scale deficits, Rule 3 applicability, Rule 26 statutory exemptions, neutral reference MRP discrepancies, Rule 27 pre-packer registry, digital evidence SHA-256 provenance, finalized inspection mutation locking (HTTP 409), RBAC permissions, corporate governance & Section 49 director non-liability, multi-inspection dossier synthesis without collective guilt, Section 15 seizure panchnama aggregation, and 14-section ReportLab consolidated PDF export.
  - 100% offline synthetic fixtures (`fixtures.py`) marked with explicit statutory metadata (`SYNTHETIC_VALIDATION_FIXTURE`).
  - Strict legal traceability assertions (`assert_legal_traceability`) enforcing statutory citations, Schedule mappings, and preventing Rule 24 misattribution to MPE.
  - Safety boundary guards (`assert_safety_boundaries`) scanning text and JSON payloads for prohibited autonomous claims, prosecution recommendations, fake government decrees, or collective guilt.
- **Asynchronous Runner & Standalone CLI (`scripts/run_validation.py`):**
  - `ValidationRunner` producing structured `ScenarioResult` and `ValidationSummary` objects.
  - Standalone executable CLI supporting `--json` for CI/CD integration, `--scenario` filtering, and colorized terminal summary tables.
- **Verification & Regression:**
  - Automated test suite `backend/tests/test_phase4_1_validation.py` passing 100%.
  - Full 12-suite backend regression running across all historical phases: 166/166 tests passing (100%).
  - Next.js production build passing with all 15 routes cleanly compiled.
  - Docker runtime healthy with Alembic head at `0007_investigation_dossiers`.

### Phase 4.2 — Real Package Image Validation (COMPLETED)
- **Dataset Discovery & Inventory (`validation_data/phase4_2_real_packages`):**
  - Canonical inventory registry `metadata/image_inventory.csv` cataloging all 28 real packaged commodity photographs (26 unique contents, 2 documented duplicate entries) with SHA-256 digests, dimensions, EXIF orientation, and integrity flags.
  - Structured ground-truth metadata schema `metadata/ground_truth.json` capturing physical package formats (jars, bottles, tubes, cartons, pouches), visible languages, human-verified declarations, optical quality characteristics, expected legal behavior, and review reason codes.
- **Baseline Pipeline Evaluation Engine (`backend/app/validation/real_image_runner.py`):**
  - Seamlessly chains production services without mocking: `assess_image_quality`, `decode_barcodes_from_image`, `ocr_service.extract_text`, `extract_declaration_from_ocr`, and `evaluate_inspection`.
  - Captures optical metrics, barcode detection rates, OCR character and confidence distributions, field-level extraction rates, and structured review reasons (`INSUFFICIENT_PHYSICAL_EVIDENCE`, `BLUR_OBSCURES_DECLARATION`, `LOW_OCR_CONFIDENCE`, `PARTIAL_OCCLUSION`, `GLARE_OBSCURES_TEXT`, `AMBIGUOUS_NUMERIC_VALUE`, `UNRESOLVED_LANGUAGE`).
  - Enforces safety boundary invariant: **`FALSE_CERTAINTY_COUNT = 0`** (100% of ambiguous/compromised captures route safely to `NEEDS_REVIEW` without hallucinatory passes or false non-compliance verdicts).
- **Standalone CLI Runner & Technical Baseline Reports:**
  - `backend/scripts/run_phase4_2_validation.py` with terminal color summary, `--json`, and `--category` flags.
  - Automatically exports comprehensive baseline report `metadata/phase4_2_baseline_report.json` and 14-section Markdown documentation `metadata/phase4_2_baseline_report.md` (Sections A through N).
- **Automated Regression Suite (`test_phase4_2_real_image_validation.py`):**
  - 10 automated tests verifying inventory cryptographic integrity, ground-truth schema completeness, optical diagnostics consistency, barcode decoding, pipeline execution, zero false certainty invariant, structured review tagging, and CLI JSON compliance.
  - Baseline real package evaluation established and frozen with zero false certainty.

### Phase 4.3 — Evidence-Driven Perception Robustness & Multi-Stage Image Processing (Sub-Batch 1 COMPLETED & FREEZE-GATED)
- **Sub-Batch 1 — Evidence-Preserving Image Preprocessing Pipeline (`backend/app/services/image_preprocessing_service.py`):**
  - **Master Evidence Immutability:** Raw ingress byte stream designated as `RAW_MASTER`, protected from modification. Digital SHA-256 fingerprint computed immediately upon ingress and retained across all downstream operations.
  - **Normalized Derivative Distinction:** `NORMALIZED_ORIGINAL` (aliased as `ORIGINAL`) strictly identified as a normalized derivative (`is_raw_master=False`) produced after EXIF orientation correction and RGB standardization, never conflated with untouched raw evidence.
  - **Cryptographic Provenance Lineage:** In-memory lineage linking each variant through `original_image_hash` (raw master digest), `parent_variant_hash` (direct parent digest), and `processed_image_hash` (derivative digest).
  - **6 Standard Deterministic Variants:** Bounded derivative generation generating `NORMALIZED_ORIGINAL`, `GRAYSCALE`, `CONTRAST_NORMALIZED`, `SHARPENED`, `UPSCALED`, and `ADAPTIVE_THRESHOLD`.
  - **Adaptive Thresholding Mathematical Validation:** Verified exact equivalence of Pillow subtraction lookup implementation against statutory/mathematical formula $\text{out}(x,y) = 255 \text{ if } \text{gray}(x,y) \ge \text{local\_mean}(x,y) - C \text{ else } 0$ with 0 mismatches across all 65,536 8-bit pairs. Documented limitations regarding severe specular saturation/glare recovery.
  - **Dimension Safety & Non-Destructive Handling:** Strict dimension clamping ($100 \le \text{px} \le 3000$) via Lanczos resampling, non-destructive file path handling without on-disk file mutation.
  - **Determinism & Timestamp Semantics:** Output image bytes determinism confirmed (`IMAGE_OUTPUT_DETERMINISM = PASS`), with run-specific timestamp semantics (`PROVENANCE_TIMESTAMP = RUN_SPECIFIC`).
  - **Architectural Isolation:** Preprocessing pipeline restricted to evidence extraction support; statutory decision authority remains 100% reserved for the deterministic versioned legal rule engine.
  - **Automated Verification:** 12/12 unit tests passing in `backend/tests/test_phase4_3_perception.py`. Full backend regression expanded to **181 / 181 tests passing (100%)** across 14 suites.
  - **Freeze Gate:** Audited, hardened, and freeze-gated before Sub-Batch 2 initiation.



