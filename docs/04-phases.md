# Project Roadmap & Implementation Phases

## Phase Breakdown

### Phase 0.1 — Domain Modeling & Architecture Blueprint
- Define 11 core domain entities (`users`, `products`, `inspections`, `inspection_images`, `ocr_results`, `declarations`, `legal_rules`, `compliance_checks`, `violations`, `evidence`, `reports`).
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
- Seeded 12 statutory LMPC 2011 rules (`LMPC-R6-*`, `LMPC-R7-*`, `LMPC-R8-*`, `LMPC-R9-*`), deterministic rule evaluator, `POST /evaluate` and `GET /checks` endpoints.

### Phase 0.8 — OCR + Structured Declaration Extraction Pipeline
- Tesseract 5 OCR integration, image preprocessor, spatial token extraction, deterministic LMPC Rule 6 declaration parser, `POST /images/{id}/ocr` endpoint, human verification protection.

### Phase 0.9 — End-to-End Automated Pipeline, Violation & Evidence Generation, and Validation Benchmarking
- **Violation Generation:** Automated creation of `Violation` records for each `CheckResult.FAIL`, with severity ratings (`HIGH`, `MEDIUM`, `LOW`), statutory citations, and plain-language legal reasons.
- **Evidence Linking:** Automatic extraction of spatial bounding boxes from OCR tokens for detected/failed fields, linking visual evidence to compliance checks and violations.
- **Unified Pipeline API:** `POST /api/v1/inspections/{inspection_id}/pipeline` orchestrating the entire automated flow (Image $\to$ Preprocessing $\to$ OCR $\to$ Extraction $\to$ Rule Engine $\to$ Violations $\to$ Evidence).
- **Violation & Evidence Inspection Endpoints:** `GET /inspections/{id}/violations`, `GET /inspections/{id}/evidence`.
- **Validation Dataset & Accuracy Benchmarking:** Real and synthetic package dataset evaluation harness measuring actual character accuracy, field recall/precision, and compliance decision accuracy without fabricated numbers.

### Phase 1.0 — Reports, Analytics & Frontend Integration (Future Phase)
- PDF Report generation, supervisor analytics, and Next.js inspection dashboard.

