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

### Phase 2.1 — Batch / Lot Inspection & Schedule IV Statistical Sampling
- Wholesale depot / warehouse lot management, Schedule IV statistical sampling assessment for label declarations, physical metrology separation (Rule 24 gravimetric disclaimer), and offline ZIP evidence bundle exporter with SHA-256 manifest.

### Phase 2.2 — Statutory Section 36 Notice Tracking & Section 48 Compounding Assessment
- Statutory Section 48 compounding assessment (1st, 2nd, and recurring offence tiers with statutory ceilings and Section 48(2) non-compoundable statutory bar), versioned legal metadata, draft notice lifecycle management, and draft compounding memo PDF generator with explicit non-issuance disclaimers.

### Phase 2.3 — Rule 24 & Schedule IV Gravimetric Net-Quantity & MPE Verification Engine
- Statutory Maximum Permissible Error (MPE) table lookup (Schedule IV Table 2), multi-sample gross/tare physical scale weight logging, sample mean net content ($\bar{x}$) calculation, standard deviation ($s$), negative error defectives count, critical double-MPE rejection, and printable Gravimetric Test Record PDF.

### Phase 2.4 — Rule 26 Statutory Exemptions & Special Package Provisions
- Deterministic statutory exemption evaluation under Rule 26 (Rule 26(a) small pack $\le 10\text{g/ml}$, Rule 26(b) bulk agricultural $> 50\text{kg}$, Rule 26(c)/Rule 2(p) institutional consumer) and special packaging rules (Rule 21 multi-piece piece count and Rule 22 combination pack multi-commodity rules) integrated into the deterministic statutory rule engine.

### Phase 2.5 — Field Geofence Verification, Offline Sync Queue & Inspection Provenance
- Field GPS coordinate validation against official Indian territorial bounds (6°N–38°N, 68°E–98°E), offline inspection draft synchronization queue (IndexedDB/localStorage sync client), and SHA-256 digital event provenance chaining.
