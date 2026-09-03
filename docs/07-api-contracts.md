# API Contracts & Endpoints Reference — MetrologyMitra API (v1)

## Base URL
`/api/v1`

---

## Endpoints

### 1. Authentication (`/api/v1/auth`)
- `POST /auth/register` — Register a new user (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).
- `POST /auth/login` — Login with JSON credentials and receive JWT access token.
- `POST /auth/token` — OAuth2 Password Request Form login.
- `GET /auth/me` — Retrieve current authenticated user profile.

### 2. Inspections Lifecycle & Core Endpoints (`/api/v1/inspections`)
- `POST /inspections/` — Create a new inspection (`status: CREATED`, `overall_result: PENDING`, optional `batch_id`).
- `GET /inspections/` — List inspections with pagination (`skip`/`limit`), status/result filters, state/district filters, and search query.
- `GET /inspections/{inspection_id}` — Get composite inspection details with eager-loaded relations.
- `PATCH /inspections/{inspection_id}/declaration` — Upsert declaration fields and set `is_human_verified = True`. *(Rejected with `409 Conflict` if finalized)*.
- `POST /inspections/{inspection_id}/images` — Multipart file upload, image attachment, and `SHA-256` evidence integrity hash computation. *(Rejected with `409 Conflict` if finalized)*.
- `GET /inspections/{inspection_id}/images` — List images ordered by sequence number.
- `POST /inspections/demo-seed` — Idempotently seed 7 controlled presentation case presets.

### 3. Perception, Pre-Flight Diagnostics & Indic Language Support
- `POST /inspections/{inspection_id}/images/{image_id}/ocr` — Preprocess image, run local Tesseract OCR 5 with bilingual English/Hindi Devanagari numerals translation and script detection, store tokens, and parse declarations. *(Rejected with `409 Conflict` if finalized)*.
- `POST /inspections/{inspection_id}/images/{image_id}/diagnostics` — Fast optical quality diagnostics (blur score, specular glare %, exposure, resolution).
- `POST /inspections/{inspection_id}/images/{image_id}/quality-gate` — Automated pre-flight quality gate decision (`READY_FOR_ANALYSIS`, `RETAKE_RECOMMENDED`, `MANUAL_REVIEW`) with actionable guidance and `SHA-256` hash.

### 4. Rule Engine & Statutory Compliance (`/api/v1/inspections`)
- `POST /inspections/{inspection_id}/evaluate` — Deterministic evaluation of 18 encoded compliance checks based on selected provisions of LMPC Rules, 2011 with temporal versioning (`effective_from`, `effective_to`) and channel filtering (`PHYSICAL_PACKAGE`, `ECOMMERCE`, `BOTH`). *(Rejected with `409 Conflict` if finalized)*.
- `GET /inspections/{inspection_id}/checks` — List all compliance check records.

### 5. Automated Pipeline, Violations & Evidence (`/api/v1/inspections`)
- `POST /inspections/{inspection_id}/pipeline` — Execute full end-to-end pipeline (OCR $\to$ Extraction $\to$ Rule Engine $\to$ Violations $\to$ Evidence). *(Rejected with `409 Conflict` if finalized)*.
- `GET /inspections/{inspection_id}/violations` — Retrieve all generated violations with severity and rule citations.
- `GET /inspections/{inspection_id}/evidence` — Retrieve all spatial bounding box and textual evidence items.

### 6. Reference-Assisted Tools & Cross-Checks (`/api/v1/inspections`)
- `POST /inspections/{inspection_id}/measurement` — Reference-assisted numeral height evaluation under Rule 7 & Schedule II Table 1 PDP Area tiers. *(Uncalibrated physical scale outputs `CheckResult.REVIEW`)*.
- `POST /inspections/{inspection_id}/listing` — Ingest digital marketplace listing and cross-check against physical package declarations under Rule 6(10).

### 7. Inspector Adjudication, Finalization & Audit Trail (`/api/v1/inspections`)
- `GET /inspections/{inspection_id}/review` — Retrieve full adjudication workspace data including blocking reasons and audit events.
- `POST /inspections/{inspection_id}/review` — Submit inspector review decisions (`CONFIRM`, `CORRECT`, `REQUEST_RETAKE`, `MARK_UNRESOLVED`) with manual overrides and automatic re-evaluation. *(Rejected with `409 Conflict` if finalized)*.
- `POST /inspections/{inspection_id}/finalize` — Permanently lock inspection into `COMPLETED` and enforce backend mutation locks.
- `GET /inspections/{inspection_id}/audit` — Retrieve chronological audit trail for the inspection.

### 8. Batch / Lot Inspections & Schedule IV Sampling (`/api/v1/batches`)
- `POST /batches/` — Create new multi-sample lot inspection session.
- `GET /batches/` — List batch inspection lots with status filters.
- `GET /batches/{batch_id}` — Get batch details, Schedule IV statistical sampling assessment summary (label declarations protocol), and attached sample package records. *(Clearly separates digital declaration sampling from physical gravimetric weighing under Rule 24)*.
- `POST /batches/{batch_id}/inspections/{inspection_id}` — Attach an existing inspection to a batch.
- `GET /batches/{batch_id}/export-bundle` — Download offline legal filing ZIP bundle containing all inspection records, images, and SHA-256 evidence manifest (`manifest.json`).

### 9. Enforcement Notices & Section 48 Compounding Assessment (`/api/v1/enforcement`)
- `POST /enforcement/calculate-compounding` — Statutory compounding assessment under Section 48 for Section 36 offences. Returns statutory penalty ceiling, discretionary assessment status, versioning metadata, and disclaimers. *(If facts or version are indeterminate, returns `NEEDS_REVIEW` / `NOT_DETERMINABLE`)*.
- `POST /enforcement/notices` — Create draft enforcement notice / compounding case for finalized non-compliant inspection.
- `GET /enforcement/notices` — List enforcement notices with status filtering.
- `GET /enforcement/notices/{notice_id}` — Get enforcement notice details.
- `PATCH /enforcement/notices/{notice_id}` — Update notice status (`DRAFTED`, `ISSUED`, `COMPOUNDED`, `REFERRED_TO_COURT`), challan reference, and officer remarks.
- `GET /enforcement/notices/{notice_id}/challan-pdf` — Download draft statutory compounding memo PDF with explicit `[DRAFT / REFERENCE ONLY — SUBJECT TO FORMAL AUTHORIZED OFFICER REVIEW & EXECUTION]` watermark and non-issuance disclaimer.

### 10. Legal Rules Knowledge Base (`/api/v1/rules`)
- `GET /rules/` — List legal rules (`active_only=true` filter, channel filter).
- `GET /rules/{rule_id}` — Retrieve specific legal rule details.
- `POST /rules/seed` — Seed / update 18 statutory rules knowledge base with versioning and channel metadata.
- `GET /rules/benchmark` — Retrieve validation benchmark accuracy metrics.

### 11. Inspection Reports & Exports (`/api/v1/inspections/{id}/reports`)
- `POST /inspections/{inspection_id}/reports` — Generate draft inspection document (`report_type: PDF | JSON | NOTICE_SEC36`).
- `GET /inspections/{inspection_id}/reports` — List generated reports for an inspection.
- `GET /inspections/{inspection_id}/reports/{report_id}` — Get report metadata.
- `GET /inspections/{inspection_id}/reports/{report_id}/download` — Stream/download the PDF or JSON report file with SHA-256 fingerprint verification.

### 12. Supervisor Analytics & Intelligence (`/api/v1/analytics`)
- `GET /analytics/overview` — High-level enforcement KPIs (Total scans, compliance rate, violations count, high-severity rate, active officers).
- `GET /analytics/trends` — Time-series compliance and violation trends (`period=monthly|weekly|daily`).
- `GET /analytics/heatmaps` — Geographic state and district violation heatmaps with GPS cluster anchors (`state` optional filter).
- `GET /analytics/repeat-offenders` — Ranked entities with recurring non-compliance and common failed rule codes (`limit=1..100`).
- `GET /analytics/failing-rules` — Top statutory rules causing inspection failure or non-compliance (`limit=1..100`).

### 13. Physical Metrology & Gravimetric Testing (`/api/v1/gravimetric`)
- `POST /gravimetric/tests` — Create and statistically evaluate physical scale sample weights against Rule 24 and Schedule IV Table 2 MPE tolerances. Returns individual errors, mean deficit, defective count, and lot decision (`PASSED_MPE`, `FAILED_MEAN_DEFICIT`, `FAILED_EXCESSIVE_DEFECTIVES`, `FAILED_CRITICAL_DOUBLE_MPE`).
- `GET /gravimetric/tests/{test_id}` — Get gravimetric test detail and MPE description.
- `GET /gravimetric/tests/{test_id}/pdf` — Download official Gravimetric Net-Quantity Verification Memo PDF with SHA-256 digital integrity hash.

### 14. Statutory Exemptions & Special Packaging (`/api/v1/exemptions`)
- `POST /exemptions/evaluate` — Stateless statutory evaluation of package data under Rule 26 (<= 10g small packages, > 50kg bulk, institutional) and Rules 21–22 (multi-piece, combination packages).
- `POST /exemptions/apply/{inspection_id}` — Apply statutory exemption classification to an inspection's declaration and re-evaluate compliance rules.

### 15. Field Geofence & Offline Provenance (`/api/v1/provenance`)
- `POST /provenance/geovalidate` — Validates field officer GPS coordinates against Indian administrative boundaries (6°N–38°N, 68°E–98°E).
- `POST /provenance/sync-offline` — Ingests, validates, creates inspection cases, and computes SHA-256 provenance hashes for offline drafted field inspections.
- **Authorization:** `SUPERVISOR` & `ADMIN` only (`403 Forbidden` for `INSPECTOR`, `401 Unauthorized` for unauthenticated).
