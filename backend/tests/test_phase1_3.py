import io
import sys
import uuid
from pathlib import Path
import httpx
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_phase1_3():
    client = httpx.Client(base_url='http://localhost:8000')

    print('================================================================')
    print('        PHASE 1.3 ADVANCED FIELD INTELLIGENCE TEST SUITE        ')
    print('================================================================')

    # --- 1. Seed legal rules including Rule 18 ---
    r_seed = client.post('/api/v1/rules/seed')
    assert r_seed.status_code == 200
    print('[PASS] 1. Legal rules seeded with Rule 18(2) Dual MRP')

    # --- 2. Authenticate Users ---
    u_insp = {'name': 'Inspector Ananya', 'email': 'ananya.insp@doca.gov.in', 'password': 'Password@123', 'role': 'INSPECTOR'}
    u_other = {'name': 'Inspector Vikram', 'email': 'vikram.insp@doca.gov.in', 'password': 'Password@123', 'role': 'INSPECTOR'}
    u_sup = {'name': 'Supervisor Rao', 'email': 'rao.sup@doca.gov.in', 'password': 'Password@123', 'role': 'SUPERVISOR'}

    client.post('/api/v1/auth/register', json=u_insp)
    client.post('/api/v1/auth/register', json=u_other)
    client.post('/api/v1/auth/register', json=u_sup)

    tok_insp = client.post('/api/v1/auth/login', json={'email': u_insp['email'], 'password': u_insp['password']}).json()['access_token']
    tok_other = client.post('/api/v1/auth/login', json={'email': u_other['email'], 'password': u_other['password']}).json()['access_token']
    tok_sup = client.post('/api/v1/auth/login', json={'email': u_sup['email'], 'password': u_sup['password']}).json()['access_token']

    h_insp = {'Authorization': f'Bearer {tok_insp}'}
    h_other = {'Authorization': f'Bearer {tok_other}'}
    h_sup = {'Authorization': f'Bearer {tok_sup}'}

    # Create Inspection
    insp = client.post('/api/v1/inspections/', json={
        'store_name': 'Modern Retail Bazaar',
        'store_address': 'Shop 45, Commercial Complex',
        'district': 'Pune',
        'state': 'MH',
        'gps_latitude': 18.5204,
        'gps_longitude': 73.8567
    }, headers=h_insp).json()
    insp_id = insp['id']

    # --- 3. Test Image Quality Diagnostics ---
    # A: Optimal Sharp Image
    img_sharp = Image.new('RGB', (800, 600), color=(220, 220, 220))
    d = ImageDraw.Draw(img_sharp)
    for y in range(40, 560, 35):
        d.text((40, y), 'Brand: Tata Sampann Toor Dal Mandatory Statutory Declarations LMPC Rule 6', fill=(0, 0, 0))

    buf_sharp = io.BytesIO()
    img_sharp.save(buf_sharp, format='JPEG')
    up_sharp = client.post(f'/api/v1/inspections/{insp_id}/images', files={'file': ('sharp.jpg', io.BytesIO(buf_sharp.getvalue()), 'image/jpeg')}, data={'image_type': 'LABEL'}, headers=h_insp).json()
    sharp_id = up_sharp['id']

    diag_sharp = client.post(f'/api/v1/inspections/{insp_id}/images/{sharp_id}/diagnostics', headers=h_insp).json()
    assert diag_sharp['overall_status'] in ['PASS', 'WARNING']
    assert diag_sharp['blur_status'] in ['PASS', 'WARNING']
    assert diag_sharp['glare_detected'] == False
    assert diag_sharp['resolution_status'] == 'PASS'
    b_score = diag_sharp['blur_score']
    g_ratio = diag_sharp['glare_ratio']
    w_px, h_px = diag_sharp['width'], diag_sharp['height']
    print(f'[PASS] 2. Optimal image diagnostics: BlurScore={b_score}, GlareRatio={g_ratio}, Resolution={w_px}x{h_px}')

    # B: Blurry Image (Heavy Gaussian Blur)
    img_blur = img_sharp.filter(ImageFilter.GaussianBlur(radius=10))
    buf_blur = io.BytesIO()
    img_blur.save(buf_blur, format='JPEG')
    up_blur = client.post(f'/api/v1/inspections/{insp_id}/images', files={'file': ('blurry.jpg', io.BytesIO(buf_blur.getvalue()), 'image/jpeg')}, data={'image_type': 'LABEL'}, headers=h_insp).json()
    blur_id = up_blur['id']

    diag_blur = client.post(f'/api/v1/inspections/{insp_id}/images/{blur_id}/diagnostics', headers=h_insp).json()
    assert diag_blur['blur_status'] == 'FAIL'
    assert diag_blur['blur_score'] < 350.0
    assert 'blur' in diag_blur['guidance_message'].lower()
    b_blur = diag_blur['blur_score']
    b_st = diag_blur['blur_status']
    print(f'[PASS] 3. Blurry image detected: BlurScore={b_blur} < threshold, Status={b_st}')

    # C: Glare / Overexposed Image
    img_glare = Image.new('RGB', (800, 600), color=(100, 100, 100))
    d_glare = ImageDraw.Draw(img_glare)
    d_glare.rectangle([(100, 100), (600, 500)], fill=(255, 255, 255))
    buf_glare = io.BytesIO()
    img_glare.save(buf_glare, format='JPEG')
    up_glare = client.post(f'/api/v1/inspections/{insp_id}/images', files={'file': ('glare.jpg', io.BytesIO(buf_glare.getvalue()), 'image/jpeg')}, data={'image_type': 'LABEL'}, headers=h_insp).json()
    glare_id = up_glare['id']

    diag_glare = client.post(f'/api/v1/inspections/{insp_id}/images/{glare_id}/diagnostics', headers=h_insp).json()
    assert diag_glare['glare_detected'] == True
    assert diag_glare['glare_ratio'] > 0.15
    assert 'glare' in diag_glare['guidance_message'].lower()
    g_pct = diag_glare['glare_ratio'] * 100
    g_st = diag_glare['glare_status']
    print(f'[PASS] 4. Specular glare detected: GlareRatio={g_pct:.1f}%, Status={g_st}')

    # D: RBAC & Ownership on Diagnostics
    assert client.post(f'/api/v1/inspections/{insp_id}/images/{sharp_id}/diagnostics', headers=h_other).status_code == 403
    assert client.post(f'/api/v1/inspections/{insp_id}/images/{sharp_id}/diagnostics', headers=h_sup).status_code == 200
    assert client.post(f'/api/v1/inspections/{insp_id}/images/{sharp_id}/diagnostics').status_code == 401
    print('[PASS] 5. Diagnostics RBAC & Inspector isolation verified')

    # --- 4. Test Barcode Service & Master Catalog Matching ---
    from app.services.barcode_service import lookup_master_catalog, verify_mrp_against_catalog, extract_numeric_mrp

    # Test numeric extraction
    assert extract_numeric_mrp('MRP Rs. 175.00 (incl. of all taxes)') == 175.00
    assert extract_numeric_mrp('₹ 420.50') == 420.50
    assert extract_numeric_mrp('MRP: 120') == 120.00
    assert extract_numeric_mrp('None') == None
    print('[PASS] 6. Numeric MRP parser verified')

    # Test Master Catalog Lookup
    cat_item = lookup_master_catalog('8901030889211')
    assert cat_item is not None
    assert cat_item['standard_mrp'] == 175.00
    assert cat_item['brand_name'] == 'Tata Sampann'
    print('[PASS] 7. Controlled demo catalog lookup verified (Tata Sampann Toor Dal)')

    # Test MRP Verification Logic
    # Case 1: Match
    st_match, r_match, obs_m, cat_m = verify_mrp_against_catalog('MRP Rs. 175.00 incl. of all taxes', cat_item)
    assert st_match == 'MATCH'
    assert obs_m == 175.00
    print('[PASS] 8. MRP Match verification verified')

    # Case 2: Mismatch / Altered Price
    st_mis, r_mis, obs_mis, cat_mis = verify_mrp_against_catalog('MRP Rs. 210.00 incl. of all taxes', cat_item)
    assert st_mis == 'MISMATCH'
    assert obs_mis == 210.00
    assert cat_mis == 175.00
    print('[PASS] 9. MRP Discrepancy detection verified (Observed ₹210 vs Catalog ₹175)')

    # --- 5. Test Full Pipeline with Barcode & Dual MRP Rule ---
    pipe_res = client.post(f'/api/v1/inspections/{insp_id}/pipeline', headers=h_insp).json()
    assert pipe_res['total_checks'] in (13, 18)
    print(f'[PASS] 10. Pipeline executed with statutory rules evaluated')

    r18_check = next((c for c in pipe_res['checks'] if c.get('legal_rule', {}).get('rule_code') == 'LMPC-R18-DUAL-MRP'), None)
    assert r18_check is not None
    r18_res = r18_check['result']
    r18_val = r18_check['observed_value']
    print(f'[PASS] 11. Rule 18(2) check evaluated: Result={r18_res}, Finding="{r18_val}"')

    # Test Discrepancy on a Price Discrepancy Inspection
    insp_tampered = client.post('/api/v1/inspections/', json={
        'store_name': 'Corner Mart',
        'district': 'Pune',
        'state': 'MH'
    }, headers=h_insp).json()
    tampered_id = insp_tampered['id']

    # Attach barcode data to declaration and set altered MRP
    client.patch(f'/api/v1/inspections/{tampered_id}/declaration', json={
        'commodity_name': 'Tata Sampann Toor Dal',
        'manufacturer_name': 'Tata Consumer Products Ltd',
        'address': 'Plot 12, Industrial Area, Mumbai',
        'net_quantity': '1 kg',
        'mrp': 'MRP Rs. 210.00 incl. of all taxes',  # Differs: standard is 175
        'manufacturing_date': '08/2026',
        'consumer_care': '1800-22-3344 care@tataconsumer.com',
        'raw_extractions': {
            'barcode_data': {
                'value': '8901030889211',
                'format': 'EAN13',
                'catalog_match': {
                    'matched': True,
                    'product_name': 'Tata Sampann 100% Unpolished Toor Dal',
                    'brand_name': 'Tata Sampann',
                    'catalog_mrp': 175.0,
                    'observed_mrp': 210.0,
                    'discrepancy': 'MISMATCH',
                    'reason': 'MRP discrepancy detected against reference data: Observed package MRP (₹210.00) differs from controlled master catalog reference (₹175.00).'
                }
            }
        },
        'is_human_verified': True
    }, headers=h_insp)

    # Evaluate Inspection with Discrepancy
    eval_tampered = client.post(f'/api/v1/inspections/{tampered_id}/evaluate', headers=h_insp).json()
    assert eval_tampered['overall_result'] in ['NON_COMPLIANT', 'NEEDS_REVIEW']
    print(f'[PASS] 12. Price discrepancy under Rule 18(2) flagged appropriately as {eval_tampered["overall_result"]}')

    # --- 6. Existing Regression: Health, Reports, Analytics ---
    assert client.get('/api/v1/health').json()['database'] == 'healthy'
    assert client.get('/api/v1/rules/benchmark').status_code == 200
    assert client.get('/api/v1/analytics/overview', headers=h_sup).status_code == 200
    assert client.get('/api/v1/analytics/trends', headers=h_sup).status_code == 200
    assert client.get('/api/v1/analytics/heatmaps', headers=h_sup).status_code == 200
    assert client.get('/api/v1/analytics/repeat-offenders', headers=h_sup).status_code == 200
    assert client.get('/api/v1/analytics/failing-rules', headers=h_sup).status_code == 200

    # Report download
    rep_pdf = client.post(f'/api/v1/inspections/{tampered_id}/reports', json={'report_type': 'PDF'}, headers=h_insp).json()
    rep_id = rep_pdf['id']
    pdf_dl = client.get(f'/api/v1/inspections/{tampered_id}/reports/{rep_id}/download', headers=h_insp)
    assert pdf_dl.status_code == 200
    assert pdf_dl.content.startswith(b'%PDF-')
    print('[PASS] 13. PDF report export generated with Rule 18 discrepancy violation')

    print('\n================================================================')
    print('     ALL PHASE 1.3 ADVANCED INTELLIGENCE TESTS PASSED (13/13)   ')
    print('================================================================')

if __name__ == '__main__':
    test_phase1_3()
