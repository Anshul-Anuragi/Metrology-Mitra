# API Contracts & Endpoints Reference — Legal Metrology API (v1)

## Base URL
`/api/v1`

---

## Endpoints

### 1. Authentication (`/api/v1/auth`)
- `POST /auth/register` — Register a new user (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).
- `POST /auth/login` — Login with JSON credentials and receive JWT access token.
- `POST /auth/token` — OAuth2 Password Request Form login.
- `GET /auth/me` — Retrieve current authenticated user profile.

### 2. Inspections (`/api/v1/inspections`)
- `POST /inspections/` — Create a new inspection (`status: CREATED`, `overall_result: PENDING`).
- `GET /inspections/` — List inspections with pagination (`skip`/`limit`) and status/result filters.
- `GET /inspections/{inspection_id}` — Get composite inspection details with eager-loaded relations.
- `PATCH /inspections/{inspection_id}/declaration` — Upsert declaration fields and set `is_human_verified = True`.
- `POST /inspections/{inspection_id}/images` — Multipart file upload and image attachment.
- `GET /inspections/{inspection_id}/images` — List images ordered by sequence number.

### 3. Perception & OCR (`/api/v1/inspections/{id}/images/{image_id}/ocr`)
- `POST /inspections/{inspection_id}/images/{image_id}/ocr` — Preprocess image, run OCR, store tokens, and parse structured declarations.

### 4. Rule Engine & Compliance (`/api/v1/inspections`)
- `POST /inspections/{inspection_id}/evaluate` — Deterministic evaluation of all 12 LMPC 2011 statutory rules.
- `GET /inspections/{inspection_id}/checks` — List all compliance check records.

### 5. Automated Pipeline, Violations & Evidence (`/api/v1/inspections`)
- `POST /inspections/{inspection_id}/pipeline` — Execute full end-to-end pipeline (OCR $\to$ Extraction $\to$ Rule Engine $\to$ Violations $\to$ Evidence).
- `GET /inspections/{inspection_id}/violations` — Retrieve all generated violations with severity and rule citations.
- `GET /inspections/{inspection_id}/evidence` — Retrieve all spatial bounding box evidence items.

### 6. Legal Rules & Benchmarking (`/api/v1/rules`)
- `GET /rules/` — List legal rules (`active_only=true` filter).
- `GET /rules/{rule_id}` — Retrieve specific legal rule details.
- `POST /rules/seed` — Seed / update statutory rules knowledge base.
- `GET /rules/benchmark` — Retrieve validation benchmark accuracy metrics.

### 7. Inspection Reports & Exports (`/api/v1/inspections/{id}/reports`)
- `POST /inspections/{inspection_id}/reports` — Generate draft inspection document (`report_type: PDF | JSON | NOTICE_SEC36`).
- `GET /inspections/{inspection_id}/reports` — List generated reports for an inspection.
- `GET /inspections/{inspection_id}/reports/{report_id}` — Get report metadata.
- `GET /inspections/{inspection_id}/reports/{report_id}/download` — Stream/download the PDF or JSON report file.

### 8. Supervisor Analytics & Intelligence (Phase 1.1) (`/api/v1/analytics`)
- `GET /analytics/overview` — High-level enforcement KPIs (Total scans, compliance rate, violations count, high-severity rate, active officers).
- `GET /analytics/trends` — Time-series compliance and violation trends (`period=monthly|weekly|daily`).
- `GET /analytics/heatmaps` — Geographic state and district violation heatmaps with GPS cluster anchors (`state` optional filter).
- `GET /analytics/repeat-offenders` — Ranked entities with recurring non-compliance and common failed rule codes (`limit=1..100`).
- `GET /analytics/failing-rules` — Distribution and failure frequency of statutory LMPC rule codes (`limit=1..50`).
- **Authorization:** `SUPERVISOR` & `ADMIN` only (`403 Forbidden` for `INSPECTOR`, `401 Unauthorized` for unauthenticated).
