# Project State — MetrologyMitra (SIH26034)

> **Single Source of Truth** for maintaining, resuming, and extending the **MetrologyMitra** codebase across development sessions.

---

## 1. Project Objective
- **Problem Statement ID:** SIH26034
- **Title:** Development of a Software Application for Compliance Inspection of Packaged Commodities
- **Official Name:** **MetrologyMitra**
- **Regulatory Authority:** Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Government of India
- **Statutory Source of Truth:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules, 2011)
- **Mission:** Empower field Legal Metrology Officers with an end-to-end visual inspection and adjudication system for packaged commodities, combining local OCR perception, deterministic statutory rule evaluation, pre-flight image quality gating, reference-assisted measurement, e-commerce marketplace cross-verification, and chronological audit trails.

---

## 2. MVP Objective & Completed Scope
Production-ready, verified compliance inspection system encompassing **Phases 0.1 through 1.9**:
1. **Multi-Angle Evidence Ingestion & Quality Gate:** Evaluates Laplacian blur, specular glare, luminance exposure, and image resolution with pre-flight decisions (`READY_FOR_ANALYSIS`, `RETAKE_RECOMMENDED`, `MANUAL_REVIEW`).
2. **Byte-Level Evidence Integrity Lineage:** Calculates and stores SHA-256 digital fingerprint hashes for every evidence photograph.
3. **Local Perception Engine:** Local Tesseract OCR 5 + ZXing-C++ barcode/QR decoding with OCR token coordinates and confidence scores.
4. **18 Statutory Rule Intelligence Engine:** Evaluates active statutory rules deterministically with temporal version resolution (`inspection_date`) and channel filtering (`PHYSICAL_PACKAGE`, `ECOMMERCE`, `BOTH`).
5. **Reference-Assisted Numeral Height Measurement:** Computes Schedule II Table 1 Principal Display Panel (PDP) height tiers ($1.0\text{ mm}$ to $6.0\text{ mm}$), strictly returning `CheckResult.REVIEW` when uncalibrated.
6. **E-Commerce Digital Marketplace Cross-Check:** Cross-verifies physical package declarations against online listing declarations under Rule 6(10) (detects origin, price, or manufacturer contradictions).
7. **Neutral MRP Reference Discrepancy:** Evaluates package MRP against controlled demo master catalog neutrally (`"MRP discrepancy detected against reference data"` $\to$ `NEEDS_REVIEW`), avoiding subjective tampering conclusions.
8. **Human-in-the-Loop Review Workspace:** Adjudication decisions (`CONFIRM`, `CORRECT`, `REQUEST_RETAKE`, `MARK_UNRESOLVED`) with field overrides and finalization guardrails.
9. **Permanent Backend Mutation Lock:** Rejects modifications on finalized (`COMPLETED`) inspections with `HTTP 409 Conflict`.
10. **Chronological Audit Trail:** Immutable recording of all automated and manual lifecycle events.
11. **Statutory Report Generation:** Safe PDF inspection memorandums and Section 36 notices branded **MetrologyMitra** with SHA-256 fingerprints, statutory citations, and draft disclaimers.
12. **Supervisor Analytics & Regional Heatmaps:** Real-time compliance rates, state/district violation heatmaps, repeat offender intelligence, and failing rule frequencies.
13. **Controlled Demo Presets:** 7 presentation test fixtures (`[Controlled Demo Data]`) seeded idempotently.

---

## 3. Technology Stack
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide React, Axios
- **Backend:** Python 3.11, FastAPI 0.111+ (Async ASGI), SQLAlchemy 2.0 (AsyncIO), `asyncpg`, `psycopg2-binary`
- **Database & Migrations:** PostgreSQL 16 (Port 5434:5432), Alembic 1.13+ (Head: `0003_regulatory_intelligence_and_versioning`)
- **OCR & Perception:** Tesseract OCR 5 (`pytesseract`), Pillow 10.3+, OpenCV headless
- **Document Generation:** ReportLab 4.0+ (Safe PDF Memorandums, Section 36 Notices, JSON Bundles)
- **Security & Auth:** PyJWT (HS256), `passlib[bcrypt]`, `bcrypt`
- **Containerization:** Docker Compose (FastAPI backend + PostgreSQL 16)

---

## 4. Repository Structure
```text
Matrology-Mitra_01/
├── backend/
│   ├── alembic/                      # Alembic migration environment
│   │   ├── versions/
│   │   │   ├── 0001_initial_schema.py
│   │   │   ├── 0002_audit_logs_and_review_workflow.py
│   │   │   └── 0003_regulatory_intelligence_and_versioning.py  # Active Head
│   │   └── env.py
│   ├── app/
│   │   ├── api/v1/                   # REST API v1 routing
│   │   │   ├── endpoints/
│   │   │   │   ├── analytics.py      # Supervisor KPIs, heatmaps & repeat offenders
│   │   │   │   ├── auth.py           # Registration, login & profile
│   │   │   │   ├── health.py         # Health check endpoint
│   │   │   │   ├── inspections.py    # Inspections, review, finalize, audit, listing, measurement, demo-seed
│   │   │   │   └── rules.py          # 18 Statutory rules knowledge base & seeding
│   │   │   └── router.py             # Main API v1 router
│   │   ├── core/                     # Configuration, JWT security, deps, enums
│   │   ├── db/                       # Async SQLAlchemy engine & session
│   │   ├── models/                   # 12 SQLAlchemy ORM domain models (including AuditLog)
│   │   ├── schemas/                  # Pydantic v2 DTO schemas
│   │   ├── services/                 # Services: OCR, Rule Engine, Measurement, Listing, Barcode, Quality Gate, Reports
│   │   └── main.py                   # FastAPI application factory
│   ├── Dockerfile                    # Backend container definition
│   └── requirements.txt              # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 14 App Router pages
│   │   │   ├── analytics/page.tsx    # Supervisor analytics & heatmaps portal
│   │   │   ├── inspections/page.tsx  # Field inspections list & demo seeder
│   │   │   ├── inspections/new/page.tsx # New inspection form, GPS & photo upload
│   │   │   ├── inspections/[id]/page.tsx # 3-Pane inspection & review workspace
│   │   │   ├── login/page.tsx        # Authentication screen
│   │   │   ├── layout.tsx            # Root layout with MetrologyMitra branding
│   │   │   └── page.tsx              # Landing / role redirect page
│   │   ├── components/               # PreFlightDiagnostics, MeasurementAssistant, DigitalListingCrossCheck, ReviewWorkspace, AuditTimeline
│   │   ├── lib/                      # Centralized API client (api.ts) & Auth context (auth.tsx)
│   │   └── types/                    # TypeScript interfaces matching backend models
│   ├── package.json                  # Next.js 14 dependencies
│   ├── tsconfig.json                 # TypeScript compiler configuration
│   ├── tailwind.config.js            # Tailwind styling rules
│   └── next.config.js                # Next.js settings
├── docs/                             # Statutory rules, architecture, API contracts
├── uploads/                          # Local storage for images and generated PDFs
├── docker-compose.yml                # Multi-container orchestration
└── PROJECT_STATE.md                  # Single Source of Truth
```

---

## 5. Verified Statutory Rules Knowledge Base (18 Active Rules)
1. `LMPC-R6-COMMODITY-NAME` — Generic/Common Name of Commodity (Rule 6(1)(b))
2. `LMPC-R6-MANUFACTURER` — Manufacturer/Packer/Importer Name (Rule 6(1)(a))
3. `LMPC-R6-NET-QUANTITY` — Net Quantity Declaration & Metric Units (Rule 6(1)(c) & Rule 11)
4. `LMPC-R6-MRP` — Maximum Retail Price & All Taxes Inclusive (Rule 6(1)(e))
5. `LMPC-R6-DATE` — Month and Year of Manufacture / Packing / Import (Rule 6(1)(d))
6. `LMPC-R6-CONSUMER-CARE` — Consumer Care Contact Details (Rule 6(1)(f))
7. `LMPC-R6-ORIGIN` — Country of Origin for Imported Products (Rule 6(1)(g))
8. `LMPC-R6-USP` — Unit Sale Price Declaration (Rule 6(11) / 2021 Amendment)
9. `LMPC-R6-EXPIRY` — Best Before / Expiry Date for Perishable Commodities (Rule 6(1)(h))
10. `LMPC-R7-FONT-HEIGHT` — Minimum Height of Numerals & Letters (Rule 7 & Schedule II Table 1)
11. `LMPC-R8-PDP-PLACEMENT` — Grouped Display on Principal Display Panel (Rule 8)
12. `LMPC-R9-LEGIBILITY` — Legibility, Readability & Prominent Contrast (Rule 9)
13. `LMPC-R18-DUAL-MRP` — Prohibition of MRP Overcharging / Discrepancies (Rule 18(2))
14. `LMPC-R6-PACKER-DISTINCTION` — Distinct Qualification of Manufacturer vs Packer (Rule 6(1)(a))
15. `LMPC-R12-SYMBOL-PLACEMENT` — Metric Unit Symbol Format & Non-Disallowed Casing (Rule 12(2) & Rule 13)
16. `LMPC-R10-ECOM-DECLARATIONS` — Mandatory E-Commerce Digital Marketplace Declarations (Rule 6(10))
17. `LMPC-R14-STANDARD-PACK` — Standard Packaging Metric Denominations (Schedule II / Rule 14)
18. `LMPC-R27-REGISTRATION` — Manufacturer/Packer Address & Regulatory Registry Completeness (Rule 27)

---

## 6. Verification & Test Suite Status
All test suites passed 100%:
- **`test_phase1_7_1_8_1_9.py`:** `PASS` (Image Quality Gate, 18-Rule Versioning, Rule 7 Schedule II PDP Tiers, Uncalibrated Scale REVIEW, Neutral MRP Discrepancy, E-Commerce Cross-Check, SHA-256 Lineage, Full Inspection Adjudication & PDF Generation).
- **`test_phase1_4_1_5_1_6.py`:** `PASS` (13/13 integration tests: Rule Seeding, 7 Demo Presets, Human Review Submission, Digital Listing Cross-Check, Finalization Lock 409 Conflict, Chronological Audit Trail, PDF Export, Supervisor Search).
- **`test_phase1_3.py`:** `PASS` (13/13 regression tests: Pre-flight diagnostics, Barcode parsing, Catalog match, Discrepancy handling).
- **Next.js Frontend Build (`npm run build`):** `PASS` (0 lint errors, 0 TypeScript errors).
