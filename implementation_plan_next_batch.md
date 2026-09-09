# Implementation Plan — MetrologyMitra Master Batch (Phases 2.6, 2.7, 2.8)

**Project Official Name:** MetrologyMitra  
**Problem Statement ID:** SIH26034 — Development of a Software Application for Compliance Inspection of Packaged Commodities  
**Regulatory Framework:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011  
**Batch Scope:** Phase 2.6 + Phase 2.7 + Phase 2.8  

---

## 1. Executive Summary & Phase Selection

Following the successful implementation, hardening, and verification of Phases 0.1 through 2.5, this master batch implements the next three critical statutory enforcement and governance phases:

| Phase # | Phase Name | Primary Statutory Authority |
|---|---|---|
| **Phase 2.6** | Rule 27 Statutory Pre-Packer & Manufacturer Registration Registry | Rule 27, LMPC Rules, 2011 |
| **Phase 2.7** | Section 15 Seizure Memorandum, Panchnama & Evidence Chain of Custody | Section 15, Legal Metrology Act, 2009 & Rule 29 |
| **Phase 2.8** | Section 49 Corporate Entity & Nominated Director Liability Framework | Section 49, Legal Metrology Act, 2009 |

---

## 2. Detailed Phase Specifications

### Phase 2.6: Rule 27 Statutory Pre-Packer & Manufacturer Registration Registry

#### Objective:
Provide an authoritative local registry database and verification service for pre-packers, manufacturers, and importers registered under Rule 27 with the Central Director or State Controller of Legal Metrology. Enable automatic registry lookups during inspection declaration evaluation to verify valid registration numbers, registered premises addresses, and jurisdictional validity.

#### Key Capabilities:
- **Registry Data Model:** Maintain registered pre-packers with Registration Number, Entity Name, Registered Premises Address, Jurisdiction Level (`CENTRAL_DIRECTOR` vs `STATE_CONTROLLER`), Issuing Authority, State, Validity Period, and Registered Commodity Categories.
- **Rule 27 Registry Verification Engine:** Query registry against extracted manufacturer name/address or entered registration number. Returns `REGISTERED_VALID`, `EXPIRED`, `UNREGISTERED_VIOLATION`, or `ADDRESS_MISMATCH`.
- **Statutory Certificate Digest:** SHA-256 fingerprinting of registration certificates.
- **API Endpoints:** `POST /api/v1/registrations`, `GET /api/v1/registrations`, `GET /api/v1/registrations/{id}`, `POST /api/v1/registrations/verify`.

---

### Phase 2.7: Section 15 Seizure Memorandum, Panchnama & Custody Chain Protocol

#### Objective:
Implement a formal statutory seizure recording, Panchnama execution, and sample custody tracking module under Section 15 of the Legal Metrology Act, 2009 and Rule 29. Allows inspecting officers to inventory seized packages, record independent witness statements (panchas), record official sample seal tags, and generate printable draft Panchnama / Seizure Memo PDFs with SHA-256 evidence sealing.

#### Key Capabilities:
- **Seizure Record & Item Schema:** Record inspection linkage, venue/premises details, date/time, grounds for seizure (Section 15(1)), itemized package quantities seized, sample packages taken for testing, official seal numbers, and 2 independent pancha witness details (Name, Address, Phone, Signature declaration).
- **Draft Panchnama PDF Generator:** ReportLab generator for standard Form VI / Section 15 Seizure Memorandums bearing digital evidence hashes, inventory tables, and witness acknowledgement sections with explicit `[DRAFT / REFERENCE ONLY — RECORD OF SEIZURE]` disclaimers.
- **API Endpoints:** `POST /api/v1/seizures/`, `GET /api/v1/seizures/`, `GET /api/v1/seizures/{id}`, `GET /api/v1/seizures/{id}/panchnama-pdf`.

---

### Phase 2.8: Section 49 Corporate Entity & Nominated Director Liability Framework

#### Objective:
Implement a corporate liability and nominated director tracking engine under Section 49 of the Legal Metrology Act, 2009. Facilitates recording corporate entity details (CIN, Registered Office), Nominated Director under Section 49(2) (Form I board resolution nomination, DIN, Name, Tenure), and assessing vicarious liability for company offences vs director liability when generating statutory notices.

#### Key Capabilities:
- **Corporate & Nominated Director Schema:** Corporate entities (`companies`), Corporate Identification Number (CIN), Registered Office Address, Nominated Director under Section 49(2) (`nominated_directors`), Director Identification Number (DIN), Form I Nomination Notice Date, Active Status.
- **Section 49 Liability Evaluator:** Maps violations to company entity and determines whether a Section 49(2) nominated director is officially on record to receive statutory notices, or whether liability defaults to persons in charge under Section 49(1).
- **API Endpoints:** `POST /api/v1/companies/`, `GET /api/v1/companies/`, `GET /api/v1/companies/{id}`, `POST /api/v1/companies/{id}/directors`, `GET /api/v1/companies/lookup`.

---

## 3. Database Schema Changes & Alembic Migration

### New Migration: `0006_registry_seizures_corporate.py`
- **Revises:** `0005_gravimetric_and_exemptions`
- **New Tables (4):**
  1. `packer_registrations`: Rule 27 registration number, entity name, address, jurisdiction level, state, issuing authority, registered categories, valid from/to, is_active.
  2. `seizure_records`: Inspection link, batch link, seizure memo number, venue, seizure date, statutory grounds, inspecting officer id, witness_1_data, witness_2_data, custody_location, status, sha256_seal_hash.
  3. `seizure_items`: Seizure record link, commodity name, brand, batch/lot number, quantity seized, quantity taken as sample, sample seal tag number.
  4. `companies`: Corporate name, CIN, registered office, state, contact email/phone, is_active.
  5. `nominated_directors`: Company link, director name, DIN, designation, form_i_nomination_date, effective from/to, is_active.
- **Table Alterations (1):**
  - `inspections`: Add `company_id` (FK to companies, nullable), `seizure_id` (FK to seizure_records, nullable).

---

## 4. Backend Architecture & Services

- `backend/app/models/packer_registration.py` & `backend/app/models/seizure.py` & `backend/app/models/company.py`
- `backend/app/schemas/packer_registration.py`
- `backend/app/schemas/seizure.py`
- `backend/app/schemas/company.py`
- `backend/app/services/registration_service.py` (Rule 27 registry verification)
- `backend/app/services/seizure_service.py` (Seizure inventory & Panchnama PDF generation)
- `backend/app/services/company_service.py` (Section 49 corporate liability resolver)
- `backend/app/api/v1/endpoints/registrations.py`
- `backend/app/api/v1/endpoints/seizures.py`
- `backend/app/api/v1/endpoints/companies.py`
- Register new routers in `backend/app/api/v1/router.py`.

---

## 5. Frontend Architecture & UI Components

- `frontend/src/types/index.ts`: TypeScript interfaces for Registrations, Seizures, Panchnama, Companies, Nominated Directors.
- `frontend/src/lib/api.ts`: Client methods for all new endpoints.
- `frontend/src/app/registrations/page.tsx`: Rule 27 pre-packer registry lookup & certificate verification view.
- `frontend/src/app/seizures/page.tsx`: Section 15 seizure records, item inventory, Panchnama generator, and PDF download.
- `frontend/src/components/CompanyLiabilityCard.tsx`: Section 49 corporate director liability card component.
- `frontend/src/components/Navbar.tsx`: Add navigation links for Registry and Seizures.

---

## 6. Docker & Full-Stack Containerization Impact

- Full-stack container ecosystem: `metrology_postgres` (5434:5432), `metrology_backend` (8000:8000), `metrology_frontend` (3000:3000).
- Container networking: Frontend calls backend via `http://localhost:8000/api/v1` from browser or `http://backend:8000` internally.
- Verified healthy startup and zero port collisions.

---

## 7. Testing Strategy

- Write comprehensive automated test suite `backend/tests/test_phase2_6_2_7_2_8.py`:
  - Rule 27 registration lookup & status checking (`REGISTERED_VALID`, `EXPIRED`, `UNREGISTERED_VIOLATION`).
  - Section 15 seizure memo creation, itemized inventory, 2-witness Panchnama requirements, and Panchnama PDF generation.
  - Section 49 corporate entity registration, DIN recording, Form I nominated director liability evaluation.
- Run complete regression suite across all phases (`test_phase1_3.py`, `test_phase1_4_1_5_1_6.py`, `test_phase1_7_1_8_1_9.py`, `test_phase2_0_2_1_2_2.py`, `test_phase2_3_2_4_2_5.py`, `test_phase2_6_2_7_2_8.py`).
- Run Next.js production build (`npm run build`).

---

## 8. Legal Safeguards & Invariants

1. **No Autonomous Legal Seizure Orders:** Panchnama documents are strictly draft records reflecting officer manual entries on the ground.
2. **Witness Requirement:** Panchnama records strictly mandate 2 independent witness declarations as required by Indian criminal procedure and Section 15.
3. **No Fabricated Director Disclosures:** Section 49 records require explicit Form I nomination filings; absence of nomination defaults to person in charge under Section 49(1).
4. **Registry Integrity:** Rule 27 registry is maintained as an authoritative local lookup table with transparent status explanations.

---

## 9. Explicit Out-of-Scope Items

- Real-time national biometric registry integrations (DoCA does not provide an external public biometric API).
- Autonomous court filing / e-Courts API automated case filing.
- Electronic payment gateways for on-spot challan collection.
