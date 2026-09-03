# Master Implementation Plan — Batch 2.3 + 2.4 + 2.5
## MetrologyMitra — SIH26034

---

### 1. Selected Development Phases

1. **Phase 2.3 — Rule 24 & Schedule IV Gravimetric Net-Quantity & Maximum Permissible Error (MPE) Verification Engine**
2. **Phase 2.4 — Rule 26 Statutory Exemptions & Special Package Provisions (Multi-Piece, Combination & Institutional)**
3. **Phase 2.5 — Field Geofence Verification, Offline Sync Queue & Inspection Provenance**

---

### 2. Phase Objectives

#### Phase 2.3: Rule 24 & Schedule IV Gravimetric Net-Quantity & MPE Verification Engine
- **Objective:** Bridge the statutory gap between digital label declaration sampling and physical metrology by implementing a deterministic net-quantity verification engine under Rule 24 and Schedule IV (Table 2 — Maximum Permissible Errors).
- **Domain Scope:**
  - Standard MPE table lookup based on declared nominal quantity ($Q_n$) for weight (g/kg) and volume (ml/L).
  - Multi-sample gross and tare weight entry per inspected unit.
  - Calculation of sample mean net weight ($\bar{x}$), sample standard deviation ($s$), and standard error of the mean.
  - Evaluation of individual sample units against statutory MPE thresholds (tolerable negative error, double MPE rejection).
  - Lot acceptance criteria under Schedule IV Clause 3 (Sample mean net weight $\ge Q_n$ and individual defective count within Schedule IV Table 1 limits).
  - Generation of printable Gravimetric Net Content Test Memo PDF.

#### Phase 2.4: Rule 26 Statutory Exemptions & Special Package Provisions
- **Objective:** Implement deterministic statutory exemption evaluation under Rule 26 and specialized packaging rules under Rules 21, 22, and 23.
- **Domain Scope:**
  - Rule 26(a): Exemption for small packages with net weight/volume $\le 10\text{ g}$ or $\le 10\text{ ml}$ (exempt from certain mandatory declarations like manufacturing date/MRP where applicable).
  - Rule 26(b): Exemption for agricultural produce packages $> 50\text{ kg}$.
  - Rule 26(c) & Rule 2(p): Institutional consumer package provisions (exempt from retail MRP when sold for direct institutional consumption under contract).
  - Rule 21: Multi-piece package declarations (number of individual pieces, individual net quantity, total net quantity).
  - Rule 22: Combination package declarations (distinct commodities, quantity of each commodity).
  - Seamless integration into the versioned 18-rule statutory rule engine.

#### Phase 2.5: Field Geofence Verification, Offline Sync Queue & Inspection Provenance
- **Objective:** Provide robust field provenance, GPS jurisdiction boundary validation, and offline inspection drafting capability for field officers in low-connectivity wholesale mandis/warehouses.
- **Domain Scope:**
  - GPS coordinate validation against assigned officer jurisdiction (State/District).
  - Offline inspection synchronization client in Next.js (IndexedDB / localStorage sync queue) with offline drafting, queuing, and automatic re-sync upon network restoration.
  - Inspection provenance record with immutable SHA-256 event chaining (device metadata, capture timestamp, geo-anchor).

---

### 3. Database Schema Impact & Alembic Migration

- **Migration Required:** **YES**
- **Migration Name:** `0005_gravimetric_and_exemptions`
- **New Tables:**
  1. `gravimetric_tests`:
     - `id` (UUID PK)
     - `inspection_id` (UUID FK to `inspections.id`, nullable)
     - `batch_id` (UUID FK to `inspection_batches.id`, nullable)
     - `nominal_quantity_value` (Float)
     - `nominal_quantity_unit` (VARCHAR: g, kg, ml, l)
     - `declared_tare_weight` (Float, default 0.0)
     - `mpe_value` (Float, statutory MPE in unit or %)
     - `sample_units_data` (JSONB: array of unit gross/tare/net weights and error calculations)
     - `sample_mean_net_quantity` (Float)
     - `sample_std_dev` (Float)
     - `defective_units_count` (Integer)
     - `lot_decision` (VARCHAR: `PASSED_MPE`, `FAILED_MEAN_DEFICIT`, `FAILED_EXCESSIVE_DEFECTIVES`, `INCOMPLETE`)
     - `statutory_standard` (VARCHAR: `LMPC Rules, 2011 — Schedule IV & Rule 24`)
     - `disclaimer` (TEXT)
     - `created_by_id` (UUID FK to `users.id`)
     - `created_at`, `updated_at` (TIMESTAMPTZ)
- **Table Alterations:**
  - `declarations`: Add `package_type` (VARCHAR: `STANDARD`, `MULTI_PIECE`, `COMBINATION`, `INSTITUTIONAL`, `SMALL_PACK`), `exemption_applied` (VARCHAR), `exemption_rationale` (TEXT), `multi_piece_count` (Integer), `combination_items` (JSONB).
  - `inspections`: Add `offline_client_id` (VARCHAR, nullable), `synced_at` (TIMESTAMPTZ, nullable), `geo_verified` (Boolean, default False).

---

### 4. Backend Service & API Changes

#### A. Gravimetric & MPE Engine (`backend/app/services/gravimetric_service.py`)
- `get_statutory_mpe(nominal_value: float, unit: str) -> Tuple[float, str]`: Computes statutory Maximum Permissible Error under Schedule IV Table 2.
- `evaluate_gravimetric_samples(nominal_value: float, unit: str, samples: List[Dict[str, float]], lot_size: int) -> Dict[str, Any]`: Computes statistical mean, standard deviation, individual negative errors, double-MPE rejections, and Schedule IV lot compliance verdict.
- `build_gravimetric_test_pdf(test: GravimetricTest, inspector: User) -> bytes`: Generates printable Gravimetric Net Quantity Verification Report PDF.

#### B. Exemptions & Special Package Evaluator (`backend/app/services/exemption_service.py`)
- `evaluate_package_exemptions(decl: Declaration) -> Dict[str, Any]`: Deterministically evaluates Rule 26(a) small package ($\le 10\text{ g/ml}$), Rule 26(b) large bulk package ($> 50\text{ kg}$), and Rule 2(p) institutional consumer exemptions.
- Integration into `rule_engine.py` so exempt declarations bypass retail-only rules with explicit `CheckResult.PASS` (Exempt under Rule 26) instead of false violations.

#### C. Geofence & Provenance Service (`backend/app/services/provenance_service.py`)
- Validates latitude/longitude coordinates against inspector assigned jurisdiction state/district.
- Computes provenance SHA-256 hash chaining.

#### D. API Endpoints
- `POST /api/v1/gravimetric/tests` — Create & evaluate gravimetric net-weight test session.
- `GET /api/v1/gravimetric/tests/{test_id}` — Get gravimetric test record.
- `GET /api/v1/gravimetric/tests/{test_id}/pdf` — Download gravimetric test memorandum PDF.
- `POST /api/v1/inspections/{inspection_id}/exemptions` — Evaluate Rule 26 statutory exemptions & package classification.
- `POST /api/v1/inspections/sync-offline` — Ingest and reconcile offline drafted inspection payloads.

---

### 5. Frontend Changes

1. **Gravimetric Testing View & Modal (`frontend/src/app/gravimetric/page.tsx` & `/gravimetric/[id]/page.tsx`):**
   - Interactive Gross/Tare weighing entry table with live auto-computation of individual net weights, MPE bounds, mean deficit, and Schedule IV verdict.
   - 1-Click download of Gravimetric Test Report PDF.
2. **Exemptions & Special Package Classifier (`frontend/src/components/ExemptionPanel.tsx`):**
   - Package type selector (`STANDARD`, `SMALL_PACK (<=10g)`, `INSTITUTIONAL`, `MULTI_PIECE`, `COMBINATION`).
   - Rule 26 exemption status indicator and multi-piece piece count editor.
3. **Offline Sync Queue & Status Indicator (`frontend/src/components/OfflineSyncBadge.tsx` & `frontend/src/lib/offlineStore.ts`):**
   - Offline detection banner, local storage queue for unsynced drafts, and one-click "Sync All" button.
4. **Navigation:** Updated `Navbar.tsx` with `Net-Weight (MPE)` menu item.

---

### 6. Testing Strategy

1. **Unit & Integration Tests (`backend/tests/test_phase2_3_2_4_2_5.py`):**
   - Schedule IV Table 2 MPE lookup accuracy (10g, 50g, 100g, 500g, 1kg, 5kg).
   - Sample mean deficit detection ($\bar{x} < Q_n$).
   - Tolerable negative error count vs excessive defectives lot rejection.
   - Rule 26(a) small pack ($\le 10\text{g}$) exemption verification.
   - Rule 2(p) institutional consumer label exemption verification.
   - Rule 21 multi-piece package declaration verification.
   - Geofence verification and offline payload sync endpoint.
2. **Full Regression Harness:** Run `test_phase1_3.py`, `test_phase1_4_1_5_1_6.py`, `test_phase1_7_1_8_1_9.py`, `test_phase2_0_2_1_2_2.py`, and `test_phase2_3_2_4_2_5.py`.
3. **Frontend Build:** Verify `npm run build` in `frontend/` compiles with 0 lint and 0 type errors across all new routes.

---

### 7. Legal & Statutory Guardrails

1. **Equipment Disclaimer:** Gravimetric gross and tare weights must be recorded from verified/calibrated physical metrological weighing equipment by the authorized officer.
2. **Exemption Preservation:** Exemption claims under Rule 26 are evaluated strictly against statutory criteria (e.g. quantity thresholds $\le 10\text{g}$ or contractual institutional consumer packaging).
3. **Deterministic Reasoning:** All MPE and exemption rules execute via deterministic statutory logic without probabilistic LLM inference.
4. **Non-Issuance:** Draft gravimetric memorandums and exemption memos remain strictly decision-support records.

---

### 8. Explicit Out-of-Scope Items

- Bluetooth hardware scale integration (manual entry from certified scales is used).
- Real-time IoT sensor network.
- Automated court e-filing API integration (court filings remain printable PDF / ZIP bundles).
- Microservices, Vector DBs, or Blockchain ledgers.
