# ⚖️ MetrologyMitra (SIH 2026 • Problem Statement SIH26034)
### Automated Legal Metrology Inspection & Statutory Enforcement Operating System

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026_Problem_SIH26034-orange?style=for-the-badge&logo=target)](https://sih.gov.in)
[![Ministry of Consumer Affairs](https://img.shields.io/badge/Government_of_India-DOCA-blue?style=for-the-badge&logo=governance)](https://consumeraffairs.nic.in)
[![Legal Framework](https://img.shields.io/badge/Statute-LMPC_Rules_2011_%E2%80%A2_Act_2009-emerald?style=for-the-badge)](https://consumeraffairs.nic.in)
[![Deterministic Engine](https://img.shields.io/badge/Zero_False_Certainty-Active-teal?style=for-the-badge)](#)
[![Next.js 14](https://img.shields.io/badge/Next.js-14_App_Router-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109_Async-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16_Alpine-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)

---

## 🏛️ Executive Summary

**MetrologyMitra** is an AI-assisted, legally deterministic compliance verification and statutory enforcement platform engineered specifically for **Legal Metrology Officers** under the **Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Food & Public Distribution, Government of India**.

Addressing Smart India Hackathon Problem Statement **SIH26034**, MetrologyMitra transforms manual, time-consuming market inspections into a streamlined, automated, and tamper-proof digital workflow. It combines **Google Gemini Vision OCR**, local multi-variant optical character recognition, Schedule II numeral typography validation, e-commerce marketplace cross-verification, Section 15 digital Panchnama generation, and cryptographic SHA-256 audit sealing.

```
       [ Package Photo Capture / Upload ]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ Optical Quality Gate ]    [ Gemini 3.7 Vision OCR ]
 (Laplacian Blur & Glare)     (Monospace Detection)
         │                           │
         └─────────────┬─────────────┘
                       ▼
       [ Evidence Fusion Consensus ]
                       │
                       ▼
   [ Deterministic Statutory Legal Engine ]
      (LMPC Rules 2011: Rules 1 to 34)
                       │
                       ▼
    [ Officer Adjudication & Decision Bay ]
  (Confirm / Reject / Rescan / Not Applicable)
                       │
                       ▼
  [ Tamper-Proof Panchnama & Dossier Export ]
           (SHA-256 Mutation Lock)
```

---

## 🌟 Core Differentiators & Competitive Highlights

MetrologyMitra decisively surpasses traditional manual methods and existing field prototypes:

| Feature / Dimension | Conventional / Competitor Tools | MetrologyMitra (SIH26034) |
| :--- | :--- | :--- |
| **Perception Engine** | Rigid single-engine OCR; high failure on curved/glare surfaces. | **Hybrid Consensus**: Google Gemini 3.7 Flash Vision OCR + Local Tesseract 5 + ZXing-C++ barcode quorum. |
| **Statutory Rule Engine** | Heuristic regex scoring; produces false certainties. | **Deterministic Engine**: 100% statutory rule mapping (Rules 6, 18, 27, Sched. I-VII) with *Zero False Certainty*. |
| **Inspector Workstation** | Single monolithic review screen. | **Complete Inspector Operating System**: 5 dedicated modules (`/inspector`, `/inspector/scan`, `/inspector/inspections`, `/inspector/reports`, `/inspector/profile`). |
| **Customizable UI** | Fixed layout; unoptimized for field vs. jury demos. | **Desk Customizer & 3 Density Modes**: Compact (mandi throughput), Standard (touch tablets), and Judge Presentation Mode. |
| **Optical Quality Gate** | Silent failures on blur or glare. | **Pre-Flight Diagnostics**: Automated Laplacian blur variance, luminance histogram, specular glare detection with retake advice. |
| **Adjudication Flow** | Single binary confirmation checkbox. | **Dual Inspector Decision Bays**: 4 distinct legal actions, officer notes, optimistic UI feedback, and immutable mutation locking. |
| **Enforcement Powers** | Simple inspection checklist. | **Statutory Enforcement Modules**: Rule 27 Pre-Packer Directory, Section 15 Seizures (Panchnama), Section 49 Corporate Director Liability, and Section 36/48 Investigation Dossiers. |
| **Audit & Integrity** | Mutable database entries. | **Cryptographic Immutability**: Byte-level SHA-256 evidence hashing, tamper-proof PDF generation, and append-only audit trail. |

---

## 📸 Key Workstation Capabilities

### 1. 🔍 Gemini Vision OCR Evidence Bay
Under every compliance rule check, an interactive **View evidence** drawer reveals:
- Captured package surface photo with optical preprocessing metadata.
- **OCR Extraction Card**: Engine attribution (`google/gemini-3.7-flash vision OCR`), quantitative confidence rating (95%), surface panel (`front`), and statutory field name.
- **Detected Text Monospace Box**: Clear, high-contrast, selectable raw extracted characters.
- **Statutory Citation & Provenance**: Explicit citation of the Legal Metrology (Packaged Commodities) Rules 2011 rule code, requirement text, and green verified provenance badge (`Provenance: verified from source`).

### 2. ⚖️ Dual Inspector Decision Sections
Officer adjudication is available **both** on the legal rule trace and immediately following report generation:
- **4 Action Buttons**:
  - `Confirm result`: Officially ratifies the algorithmic finding.
  - `Reject AI finding`: Overrules automated extraction with officer discretion.
  - `Request rescan`: Dispatches prompt for re-capture due to adverse lighting or glare.
  - `Mark not applicable`: Exempts package under statutory exclusion (Rule 26 / Schedule IV).
- **Officer Remarks**: Mandatory observation note recorded with timestamp and officer ID.
- **SHA-256 Mutation Lock**: Once finalized, inspection records return `HTTP 409 Conflict` on tampering attempts.

### 3. 📱 5-Bay Multi-Panel Field Capture (`/inspector/scan`)
Guided 5-step wizard engineered for field touchscreen tablets:
1. **Premises & GPS Geofencing**: Auto-captures GPS coordinates and retail establishment credentials.
2. **5-Bay Panel Capture**: Separate bays for Front, Statutory Declarations, MRP & Dates, Barcode, and Top/Base.
3. **Optical Quality Diagnostics**: Instant feedback on blur, glare, and resolution before cloud ingestion.
4. **Multi-Modal Consensus Review**: Cross-checks OCR extraction against barcode decoding and catalog registries.
5. **Statutory Adjudication**: Immediate legal verdict generation under 21 active statutory rules.

### 4. 🗂️ Statutory Enforcement Modules
- **Rule 27 Pre-Packer Registration Registry (`/registrations`)**: Look up registered pre-packers and flag non-registered entities.
- **Section 15 Seizure & Panchnama Generator (`/seizures`)**: Create legally admissible electronic Panchnama seizure orders with witness signatures.
- **Section 49 Corporate Liability Assistant (`/dossiers`)**: Attribute legal liability to Company Directors and designated Persons-in-Charge.
- **Sixth Schedule Gravimetric MPE Analyzer (`/gravimetric`)**: Calculate Maximum Permissible Error tolerances for net quantity verifications.

---

## 🎯 Pre-Calibrated SIH Benchmark Evaluation Presets

For rapid jury demonstration, MetrologyMitra includes pre-calibrated golden benchmark cases accessible with **1 click**:

| Case | Package / Product | Statutory Scenario | Expected Verdict |
| :--- | :--- | :--- | :--- |
| **Case A** | *Tata Sampann Toor Dal 1kg* | Complete statutory coverage (MRP, Net Qty, Packer Address, Customer Care). | `COMPLIANT` (18/18 Checks PASS) |
| **Case B** | *Premium Dry Fruits (Almonds)* | Optical specular glare flagged by Quality Gate; missing manufacturer postal PIN code. | `NON_COMPLIANT` (Statutory Defect) |
| **Case C** | *Heritage Spices Garam Masala* | Mandatory retail price declaration omitted under Rule 6(1)(e); zero false certainty safety engaged. | `NEEDS_REVIEW` (Adjudication Queue) |

---

## 👥 Fast-Access Evaluation Accounts

The login portal (`/login`) features **1-Click Quick Access buttons** for SIH evaluators:

| Role | Official Email | Password | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| **Field Inspector** | `p11.insp@doca.gov.in` | `Password@123` | Field capture, multi-panel OCR, on-site adjudication, Panchnama generation |
| **Supervisor** | `p11.sup@doca.gov.in` | `Password@123` | Operational triage queue, regional risk heatmaps, dossier approvals |
| **Administrator** | `p11.admin@doca.gov.in` | `Password@123` | Rule engine configuration, statutory dataset audits, officer registry |

---

## 🛠️ Technology Stack

```
Frontend:  Next.js 14.2 (App Router) • React 18 • TypeScript • Tailwind CSS • Lucide Icons
Backend:   Python 3.11 • FastAPI (Async ASGI) • SQLAlchemy 2.0 (AsyncIO) • Pydantic v2
Database:  PostgreSQL 16 (Alpine) • asyncpg • Alembic Migrations
Vision:    Google Gemini 3.7 Flash Vision OCR • Tesseract 5 • ZXing-C++ • OpenCV Headless
Reports:   ReportLab 4.0+ (Official DoCA Memorandums & Form 1 Panchnama)
Security:  JWT Authentication (HS256) • Passlib (Bcrypt) • SHA-256 Evidence Hashing
DevOps:    Docker • Docker Compose • Multi-Stage Production Builds
```

---

## 🚀 Quickstart & Installation Guide

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- [Node.js 18+](https://nodejs.org/) & `npm` (if running frontend outside container)
- Python 3.11+ (if running tests locally)

### 1. Clone the Repository
```bash
git clone https://github.com/Anshul-Anuragi/Metrology-Mitra.git
cd Metrology-Mitra
```

### 2. Launch Entire Platform via Docker Compose
```bash
# Start PostgreSQL database, FastAPI backend, and Next.js frontend
docker compose up -d

# Verify all services are healthy
docker compose ps
```

### 3. Run Database Migrations & Seed Statutory Legal Rules
```bash
# Apply Alembic schema migrations
docker compose exec backend alembic upgrade head

# Seed 21 Active Statutory Rules & Pre-Calibrated Demo Presets
docker compose exec backend python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.rule_seeder import seed_legal_rules

async def main():
    async with AsyncSessionLocal() as session:
        c = await seed_legal_rules(session)
        print(f'Successfully seeded active statutory rules: {c}')

asyncio.run(main())
"
```

### 4. Access the Application
- **Frontend Portal**: [http://localhost:3000](http://localhost:3000)
  - **Login Screen**: [http://localhost:3000/login](http://localhost:3000/login)
  - **Inspector Command Center**: [http://localhost:3000/inspector](http://localhost:3000/inspector)
  - **Field Scan Wizard**: [http://localhost:3000/inspector/scan](http://localhost:3000/inspector/scan)
  - **Supervisor Triage**: [http://localhost:3000/inspections/triage](http://localhost:3000/inspections/triage)
- **FastAPI Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Automated Verification & Test Suites

The backend includes comprehensive test suites covering all phases:

```bash
# Perception, Vision OCR & Preprocessing Suite
docker compose exec backend pytest tests/test_phase4_3_perception.py -v

# Real Image Validation & Golden Fixtures Suite
docker compose exec backend pytest tests/test_phase4_2_real_image_validation.py -v

# Legal Metrology Rule Engine & Versioning Suite
docker compose exec backend pytest tests/test_phase2_3_2_4_2_5.py -v

# Investigation Dossiers & PDF Generation Suite
docker compose exec backend pytest tests/test_phase3_0_dossiers.py -v

# Frontend TypeScript Typecheck
docker compose exec frontend npx tsc --noEmit
```

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── alembic/                      # Database schema versioning & migrations
│   ├── app/
│   │   ├── api/v1/endpoints/         # Modular REST routers (inspections, dossiers, seizures, etc.)
│   │   ├── core/                     # JWT security, settings, statutory enums
│   │   ├── db/                       # Async SQLAlchemy engine & base session
│   │   ├── models/                   # 18 relational ORM models
│   │   ├── schemas/                  # Pydantic v2 DTO schemas with strict type validation
│   │   ├── services/                 # Rule engine, OCR perception, Panchnama, PDF generation
│   │   └── main.py                   # FastAPI ASGI factory & CORS middleware
│   ├── tests/                        # Full regression, perception & statutory test suites
│   └── requirements.txt              # Production Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 14 App Router
│   │   │   ├── inspector/            # Inspector Operating System (5 sub-routes)
│   │   │   ├── inspections/          # Inspection workspace, detail & supervisor triage
│   │   │   ├── dossiers/             # Investigation dossiers (Section 36 & 48)
│   │   │   ├── seizures/             # Electronic Panchnama generation (Section 15)
│   │   │   ├── registrations/        # Rule 27 Packer Directory lookups
│   │   │   └── login/                # Executive frosted glass authentication workstation
│   │   ├── components/               # Glassmorphic UI components (Evidence, Adjudication, AppShell)
│   │   ├── lib/                      # Axios API client, Auth provider, offline store
│   │   └── types/                    # Canonical TypeScript interfaces
│   ├── package.json
│   └── tsconfig.json
├── docs/                             # Statutory rule mappings, API contracts, architectural designs
├── docker-compose.yml                # Multi-service container orchestration
└── README.md                         # Project documentation
```

---

## 📜 Statutory Framework & Compliance References

MetrologyMitra strictly adheres to the legal mandates established by the Government of India:
1. **The Legal Metrology Act, 2009 (No. 1 of 2010)**:
   - Section 15: Power of inspection, search, seizure, and forfeiture.
   - Section 36: Penalty for manufacture, sale, etc., of non-standard packages.
   - Section 48: Compounding of offences by authorized officers.
   - Section 49: Offences by companies and director liability attribution.
2. **Legal Metrology (Packaged Commodities) Rules, 2011**:
   - Rule 6: Mandatory declarations (commodity, manufacturer, net qty, MRP, date, customer care).
   - Rule 18: Uniform MRP enforcement and alteration prohibition.
   - Rule 26: Statutory exemptions and non-applicability provisions.
   - Rule 27: Mandatory registration of manufacturers, packers, and importers.
   - Schedule II: Minimum font height specifications for numerals based on area of Principal Display Panel (PDP).
   - Schedule VI: Maximum Permissible Error (MPE) thresholds for net quantity determination.

---

## 👨‍💻 Team & Acknowledgments

- **Developed for**: Smart India Hackathon 2026 (SIH 2026)
- **Problem Statement**: SIH26034
- **Organization**: Ministry of Consumer Affairs, Food & Public Distribution • Department of Consumer Affairs (DoCA)
- **Repository**: [https://github.com/Anshul-Anuragi/Metrology-Mitra](https://github.com/Anshul-Anuragi/Metrology-Mitra)

---

<p align="center">
  <strong>MetrologyMitra</strong> • <em>Empowering Legal Metrology Officers with Deterministic Intelligence & Transparent Justice</em> 🇮🇳
</p>
