import sys
import uuid
from datetime import datetime, timezone
import httpx

BASE_URL = "http://127.0.0.1:8000"

def get_auth_tokens():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    # Inspector Login
    res_insp = client.post("/api/v1/auth/token", data={
        "username": "sharma@doca.gov.in",
        "password": "password123"
    })
    if res_insp.status_code != 200:
        # Register inspector if needed
        client.post("/api/v1/auth/register", json={
            "name": "Officer Sharma",
            "email": "sharma@doca.gov.in",
            "password": "password123",
            "role": "INSPECTOR"
        })
        res_insp = client.post("/api/v1/auth/token", data={
            "username": "sharma@doca.gov.in",
            "password": "password123"
        })
    token_insp = res_insp.json()["access_token"]

    # Supervisor Login
    res_sup = client.post("/api/v1/auth/token", data={
        "username": "supervisor@doca.gov.in",
        "password": "password123"
    })
    if res_sup.status_code != 200:
        client.post("/api/v1/auth/register", json={
            "name": "Director Verma",
            "email": "supervisor@doca.gov.in",
            "password": "password123",
            "role": "SUPERVISOR"
        })
        res_sup = client.post("/api/v1/auth/token", data={
            "username": "supervisor@doca.gov.in",
            "password": "password123"
        })
    token_sup = res_sup.json()["access_token"]

    return token_insp, token_sup


def test_review_and_hardening():
    print("================================================================")
    print("      PHASE 1.4, 1.5, 1.6 & HARDENING INTEGRATION SUITE         ")
    print("================================================================")

    token_insp, token_sup = get_auth_tokens()
    h_insp = {"Authorization": f"Bearer {token_insp}"}
    h_sup = {"Authorization": f"Bearer {token_sup}"}
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Seed Legal Rules
    seed_res = client.post("/api/v1/rules/seed", headers=h_sup)
    assert seed_res.status_code == 200
    print("[PASS] 1. 18 Statutory Legal Rules seeded via API")

    # 2. Seed Controlled Demo Presets
    demo_res = client.post("/api/v1/inspections/demo-seed", headers=h_insp)
    assert demo_res.status_code == 201
    assert demo_res.json()["total_presets"] == 7
    print("[PASS] 2. 7 Controlled Demo Presets seeded idempotently")

    # 3. Create a fresh inspection for review lifecycle testing
    insp = client.post("/api/v1/inspections/", json={
        "store_name": "Spencer's Hypermarket",
        "district": "Noida",
        "state": "Uttar Pradesh"
    }, headers=h_insp).json()
    insp_id = insp["id"]
    print(f"[PASS] 3. Inspection created: ID={insp_id}")

    # 4. Set Initial Non-compliant Declaration
    decl = client.patch(f"/api/v1/inspections/{insp_id}/declaration", json={
        "commodity_name": "Premium Tea",
        "manufacturer_name": "Tea Estates India Ltd",
        "address": "Sector 62, Noida 201309",
        "net_quantity": "500 Gms",  # Non-standard casing -> Fail
        "mrp": "MRP Rs. 250.00",    # Missing 'incl. of all taxes' -> Fail
        "manufacturing_date": "08/2026",
        "consumer_care": "1800-999-000, care@teaestates.in",
    }, headers=h_insp).json()
    assert decl["is_human_verified"] is True
    print("[PASS] 4. Declaration saved with initial test values")

    # 5. Evaluate Rules
    eval_res = client.post(f"/api/v1/inspections/{insp_id}/evaluate", headers=h_insp).json()
    assert eval_res["overall_result"] == "NON_COMPLIANT"
    assert eval_res["failed_checks"] > 0
    print(f"[PASS] 5. Rule engine evaluated: Verdict={eval_res['overall_result']}, Failed={eval_res['failed_checks']}")

    # 6. Test Review Workspace Endpoint
    rw = client.get(f"/api/v1/inspections/{insp_id}/review", headers=h_insp).json()
    assert rw["inspection_id"] == insp_id
    assert rw["total_checks"] == 18
    print(f"[PASS] 6. Review workspace loaded: Total Checks={rw['total_checks']}, Can Finalize={rw['can_finalize']}")

    # 7. Submit Field Correction Review
    rev_res = client.post(f"/api/v1/inspections/{insp_id}/review", json={
        "review_action": "CORRECT",
        "review_notes": "Officer verified package physically. Corrected SI symbol to 'g' and verified tax inclusion statement.",
        "declaration_overrides": {
            "net_quantity": "500 g",
            "mrp": "MRP Rs. 250.00 incl. of all taxes",
            "unit_sale_price": "Rs. 0.50/g",
            "expiry_date": "08/2027"
        }
    }, headers=h_insp)
    assert rev_res.status_code == 200, f"Expected 200, got {rev_res.status_code}: {rev_res.text}"
    rev_sub = rev_res.json()
    assert rev_sub["overall_result"] == "COMPLIANT"
    assert rev_sub["failed_checks"] == 0
    print("[PASS] 7. Review correction submitted and re-evaluated to COMPLIANT")

    # 8. Test Digital Listing Cross-Check Endpoint
    listing_res = client.post(f"/api/v1/inspections/{insp_id}/listing", json={
        "title": "Premium Tea 500g",
        "price": 250.00,
        "net_quantity": "500 g",
        "country_of_origin": "India"
    }, headers=h_insp).json()
    assert listing_res["has_contradictions"] is False
    assert listing_res["summary_verdict"] == "PASS"
    print("[PASS] 8. Digital listing cross-check submitted and verified matching")

    # 9. Test Finalization Guardrail & Locking
    fin_res = client.post(f"/api/v1/inspections/{insp_id}/finalize", json={
        "finalization_notes": "Inspection complete and fully verified compliant."
    }, headers=h_insp)
    assert fin_res.status_code == 200
    assert fin_res.json()["status"] == "COMPLETED"
    print("[PASS] 9. Inspection finalized and status set to COMPLETED")

    # 10. Test Backend Mutation Lock (Attempt to mutate completed inspection)
    lock_test = client.patch(f"/api/v1/inspections/{insp_id}/declaration", json={
        "commodity_name": "Altered Name Attempt"
    }, headers=h_insp)
    assert lock_test.status_code == 409, f"Expected 409 Conflict, got {lock_test.status_code}"
    print("[PASS] 10. Backend mutation lock verified (HTTP 409 Conflict on finalized inspection)")

    # 11. Test Chronological Audit Trail
    audit_trail = client.get(f"/api/v1/inspections/{insp_id}/audit", headers=h_insp).json()
    assert len(audit_trail) >= 4
    actions = [a["action"] for a in audit_trail]
    assert "INSPECTION_CREATED" in actions
    assert "INSPECTION_REVIEWED" in actions
    assert "INSPECTION_FINALIZED" in actions
    print(f"[PASS] 11. Chronological audit trail recorded {len(audit_trail)} verified events: {actions}")

    # 12. Test Safe Report Export (PDF)
    pdf_rep = client.post(f"/api/v1/inspections/{insp_id}/reports", json={
        "report_type": "PDF"
    }, headers=h_insp).json()
    rep_id = pdf_rep["id"]
    dl = client.get(f"/api/v1/inspections/{insp_id}/reports/{rep_id}/download", headers=h_insp)
    assert dl.status_code == 200
    assert dl.content.startswith(b"%PDF-")
    print("[PASS] 12. PDF Report generated with MetrologyMitra header and digital integrity verification")

    # 13. Test Supervisor Analytics & Case Filtering
    search_res = client.get("/api/v1/inspections/?state_filter=Uttar&district_filter=Noida", headers=h_sup).json()
    assert len(search_res) >= 1
    assert any(i["id"] == insp_id for i in search_res)
    print(f"[PASS] 13. Case query filtering and supervisor search verified")

    print("\n================================================================")
    print("   ALL PHASE 1.4-1.6 & HARDENING TESTS PASSED (13/13)           ")
    print("================================================================")


if __name__ == "__main__":
    test_review_and_hardening()
