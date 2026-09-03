# MetrologyMitra (SIH26034)
### Software Application for Compliance Inspection of Packaged Commodities

> **Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Government of India**  
> **Statutory Framework:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules, 2011)

---

## 📌 Project Overview

**MetrologyMitra** is an AI-assisted, deterministic compliance verification platform designed for field Legal Metrology Officers. It automates the inspection of packaged commodities through multi-angle photograph analysis, local OCR extraction, Schedule II numeral height measurement, e-commerce marketplace cross-verification, and chronological audit trail logging.

### Key Capabilities
- **Local Perception Engine:** Local Tesseract OCR 5 + ZXing-C++ barcode/QR decoding with spatial token bounding boxes.
- **Pre-Flight Image Quality Gate:** Automated optical diagnostics (Laplacian blur variance, specular glare, luminance exposure, resolution) + byte-level `SHA-256` evidence integrity hashing.
- **18 Active Statutory Rules:** Deterministic evaluation engine with temporal versioning (`effective_from`, `effective_to`) and channel filtering (`PHYSICAL_PACKAGE`, `ECOMMERCE`, `BOTH`).
- **Schedule II Numeral Height Assistant:** Evaluates Principal Display Panel (PDP) height tiers ($1.0\text{ mm}$ to $6.0\text{ mm}$) with prototype advisory disclaimers.
- **E-Commerce Digital Cross-Check:** Cross-verifies physical package declarations against online marketplace listings under Rule 6(10).
- **Inspector Adjudication & Permanent Mutation Lock:** Adjudication workflows (`CONFIRM`, `CORRECT`, `REQUEST_RETAKE`, `MARK_UNRESOLVED`) with immutable sealing (`HTTP 409 Conflict`).
- **Official Statutory Reports:** ReportLab PDF inspection memorandums and Section 36 notices with digital fingerprints and statutory citations.
- **Supervisor Analytics & Regional Heatmaps:** State/district violation clusters and brand repeat-offender intelligence.
- **7 Controlled Demo Presets:** One-click seeded test fixtures for demonstration and evaluation.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons, Axios |
| **Backend** | Python 3.11, FastAPI (Async ASGI), SQLAlchemy 2.0 (AsyncIO), Alembic |
| **Database** | PostgreSQL 16 (Port 5434:5432), `asyncpg`, `psycopg2-binary` |
| **Perception** | Tesseract OCR 5 (`pytesseract`), Pillow, OpenCV headless |
| **PDF Generation** | ReportLab 4.0+ |
| **Security** | JWT (HS256), `passlib[bcrypt]` |
| **Orchestration** | Docker Compose |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- [Node.js 18+](https://nodejs.org/) & `npm`
- Python 3.11+ (for local test running)

### 2. Clone the Repository
```bash
git clone https://github.com/Anshul-Anuragi/Metrology-Mitra.git
cd Metrology-Mitra
```

### 3. Start Backend & Database via Docker
```bash
# Start PostgreSQL and FastAPI backend
docker compose up -d

# Verify containers are running
docker compose ps
```

### 4. Run Database Migrations & Seed Statutory Rules
```bash
# Apply Alembic migrations to Head
docker exec metrology_backend alembic upgrade head

# Seed 18 Statutory Legal Rules into database
docker exec -e PYTHONPATH=/app metrology_backend python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.rule_seeder import seed_legal_rules

async def main():
    async with AsyncSessionLocal() as session:
        c = await seed_legal_rules(session)
        print('Successfully seeded active rules:', c)

asyncio.run(main())
"
```

### 5. Start Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## 🧪 Running Automated Tests

```bash
# Phase 1.7, 1.8, 1.9 Test Suite (Quality Gate, Measurement, Versioning, E-Commerce)
docker exec -e PYTHONPATH=/app metrology_backend python tests/test_phase1_7_1_8_1_9.py

# Phase 1.4, 1.5, 1.6 & Hardening Integration Suite (Review Workspace, 409 Lock, Audit)
docker exec -e PYTHONPATH=/app metrology_backend python tests/test_phase1_4_1_5_1_6.py

# Phase 1.3 Regression Suite
docker exec -e PYTHONPATH=/app metrology_backend python tests/test_phase1_3.py
```

---

## 👥 Default Test Accounts

| Role | Email | Password |
|---|---|---|
| **Field Inspector** | `sharma@doca.gov.in` | `password123` |
| **Supervisor / Director** | `supervisor@doca.gov.in` | `password123` |

---

## 📂 Repository Structure

```text
├── backend/
│   ├── alembic/                      # Database migrations (Alembic)
│   ├── app/
│   │   ├── api/v1/endpoints/         # REST API endpoints (inspections, analytics, auth, rules)
│   │   ├── core/                     # Configuration, JWT security, enums
│   │   ├── db/                       # Async SQLAlchemy session & engine
│   │   ├── models/                   # 12 SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic v2 DTO schemas
│   │   ├── services/                 # Rule engine, OCR, measurement, listing, quality gate, reports
│   │   └── main.py                   # FastAPI application factory
│   ├── tests/                        # Automated test suites
│   └── requirements.txt              # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 14 App Router pages
│   │   ├── components/               # UI components (ReviewWorkspace, PreFlightDiagnostics, etc.)
│   │   ├── lib/                      # API client and Auth context
│   │   └── types/                    # TypeScript data contracts
│   └── package.json
├── docs/                             # Architecture, statutory rules, memory notes
├── docker-compose.yml                # Docker compose configuration
├── PROJECT_STATE.md                  # Single Source of Truth
└── .gitignore                        # Git exclusion rules
```

