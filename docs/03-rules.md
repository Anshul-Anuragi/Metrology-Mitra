# Legal Metrology Rules Knowledge Base & Rule Engine Foundation

## 1. Rule Engine Architecture

The Legal Metrology Compliance System separates perception from legal reasoning:

```text
[Package Images / OCR Perception]
               │
               ▼
[Structured Declarations Data Model]
               │
               ▼
[Deterministic Legal Rule Engine]  <--- (No LLM / AI in final compliance verdict)
               │
               ▼
[Individual Compliance Checks: PASS / FAIL / REVIEW + Statutory Citation + Reason]
               │
               ▼
[Deterministic Aggregator: COMPLIANT / NON_COMPLIANT / NEEDS_REVIEW]
```

---

## 2. MVP Rule Scope & Statutory Codes

The initial rule knowledge base encodes 12 explicit statutory checks derived directly from the **Legal Metrology (Packaged Commodities) Rules, 2011** and subsequent official amendments:

| Rule Code | Statutory Reference | Title | Field | Rule Type |
|---|---|---|---|---|
| `LMPC-R6-COMMODITY-NAME` | Rule 6(1)(b) | Mandatory Generic / Common Name of Commodity | `commodity_name` | `REQUIRED_FIELD` |
| `LMPC-R6-MANUFACTURER` | Rule 6(1)(a) | Mandatory Name & Address of Manufacturer / Packer / Importer | `manufacturer_name` | `REQUIRED_FIELD` |
| `LMPC-R6-NET-QUANTITY` | Rule 6(1)(c) & Rule 13 | Mandatory Net Quantity in Standard SI Units (`g`, `kg`, `ml`, `l`, `N`) | `net_quantity` | `UNIT_CHECK` |
| `LMPC-R6-MRP` | Rule 6(1)(e) | Mandatory Retail Sale Price (MRP) with 'incl. of all taxes' | `mrp` | `REQUIRED_FIELD` |
| `LMPC-R6-DATE` | Rule 6(1)(d) | Mandatory Month & Year of Mfg / Packing / Import | `manufacturing_date` | `REQUIRED_FIELD` |
| `LMPC-R6-CONSUMER-CARE` | Rule 6(1)(f) | Mandatory Consumer Complaint Redressal Contact (Phone & Email/Address) | `consumer_care` | `REQUIRED_FIELD` |
| `LMPC-R6-ORIGIN` | Rule 6(1)(g) | Mandatory Country of Origin for Imported Commodities | `country_of_origin` | `REQUIRED_FIELD` |
| `LMPC-R6-USP` | Rule 6(11) (2021 Amend.) | Mandatory Unit Sale Price (USP) Declaration | `unit_sale_price` | `REQUIRED_FIELD` |
| `LMPC-R6-EXPIRY` | Rule 6(1)(d) proviso | Mandatory Best Before / Expiry Date on Perishable Goods | `expiry_date` | `EXPIRY_DATE_CHECK` |
| `LMPC-R7-FONT-HEIGHT` | Rule 7 & Schedule II | Minimum Height of Numerals & Letters based on Quantity & PDP Area | `net_quantity` | `NUMERAL_HEIGHT` |
| `LMPC-R8-PDP-PLACEMENT` | Rule 8 | Principal Display Panel (PDP) Grouping & Visibility | `pdp_area_sq_cm` | `CUSTOM_LOGIC` |
| `LMPC-R9-LEGIBILITY` | Rule 9 | Legibility, Readability & Prominent Background Contrast | `field_confidences` | `FORMAT_CHECK` |

---

## 3. Evaluation Semantics (PASS / FAIL / REVIEW)

- **`PASS`**: Requirement is explicitly and unambiguously satisfied by the declaration data.
- **`FAIL`**: Requirement is explicitly violated (e.g. non-standard unit like `gms`/`kgs`/`ltr` under Rule 13, missing mandatory 'incl. of all taxes' phrase under Rule 6(1)(e), missing mandatory manufacturer/commodity declaration).
- **`REVIEW`**: Available data or physical evidence is insufficient to make a legally certain determination (e.g., numeral height measurement without calibrated scale, partial contact info, PDP grouping without visual confirmation).

> **Core Legal Guardrail:** The system **never silently guesses or treats missing evidence as PASS**. Where data is unavailable or optical confidence is moderate, the engine strictly outputs `REVIEW`.

---

## 4. Overall Result Aggregation Logic

The overall inspection verdict is calculated deterministically across all evaluated checks:

```python
if any(check.result == CheckResult.FAIL for check in checks):
    overall_result = ComplianceResult.NON_COMPLIANT
elif any(check.result == CheckResult.REVIEW for check in checks):
    overall_result = ComplianceResult.NEEDS_REVIEW
elif checks and all(check.result == CheckResult.PASS for check in checks):
    overall_result = ComplianceResult.COMPLIANT
else:
    overall_result = ComplianceResult.NEEDS_REVIEW
```

- **Inspection Status Sync**:
  - `NON_COMPLIANT` / `COMPLIANT` $\rightarrow$ `status = COMPLETED`
  - `NEEDS_REVIEW` $\rightarrow$ `status = REVIEW_REQUIRED`

---

## 5. Explicit Limitations & Disclosures

1. **Assisted Enforcement, Not Autonomous Adjudication:** This software is an inspection-assistance tool designed for field officers and supervisors. It does not provide legal advice or autonomously issue binding penalties.
2. **Physical Measurement Scaling:** Numeral height verification under Rule 7 and PDP placement under Rule 8 require scale calibration or ocular inspection. When scale metadata is not provided, the engine safely defers to `REVIEW`.
3. **Exemptions & Amendments:** The rule engine is versioned (`version: 2011.1`, `2021.1`). Special industry exemptions (e.g., small packages $< 10\text{ g/ml}$ under Rule 26) can be added as data parameters without modifying backend engine code.

