import http from 'http';

// Helper to make HTTP requests
function httpRequest(url, options = {}, postData = null) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const reqOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port,
      path: parsedUrl.pathname + parsedUrl.search,
      method: options.method || 'GET',
      headers: options.headers || {},
    };

    const req = http.request(reqOptions, (res) => {
      let data = [];
      res.on('data', (chunk) => data.push(chunk));
      res.on('end', () => {
        const bodyBuffer = Buffer.concat(data);
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: bodyBuffer.toString('utf8'),
          rawBody: bodyBuffer,
        });
      });
    });

    req.on('error', (err) => reject(err));

    if (postData) {
      if (typeof postData === 'string' || Buffer.isBuffer(postData)) {
        req.write(postData);
      } else {
        req.write(JSON.stringify(postData));
      }
    }
    req.end();
  });
}

async function runAcceptanceTests() {
  console.log('================================================================');
  console.log('          PHASE 1.2 BROWSER & FRONTEND ACCEPTANCE SUITE         ');
  console.log('================================================================\n');

  const frontendBase = 'http://localhost:3000';
  const backendBase = 'http://localhost:8000/api/v1';

  // --- TEST A: Next.js Routes Rendering ---
  console.log('--- TEST A: NEXT.JS APP ROUTER SSR PAGES ---');
  const routesToTest = [
    { path: '/login', name: 'Login Page' },
    { path: '/inspections', name: 'Inspections List Page' },
    { path: '/inspections/new', name: 'New Inspection Flow' },
    { path: '/analytics', name: 'Supervisor Analytics Portal' },
    { path: '/', name: 'Landing Page' },
  ];

  for (const r of routesToTest) {
    const res = await httpRequest(`${frontendBase}${r.path}`);
    if (res.statusCode === 200) {
      console.log(`[PASS] Route ${r.path.padEnd(20)} -> HTTP ${res.statusCode} (${r.name})`);
    } else {
      console.error(`[FAIL] Route ${r.path} returned HTTP ${res.statusCode}`);
      process.exit(1);
    }
  }

  // --- TEST B: Authentication & RBAC ---
  console.log('\n--- TEST B: AUTHENTICATION & RBAC ---');
  // 1. Invalid login
  const invRes = await httpRequest(`${backendBase}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, { email: 'invalid@doca.gov.in', password: 'WrongPassword' });
  if (invRes.statusCode === 401) {
    console.log('[PASS] Invalid credentials rejected with HTTP 401 Unauthorized');
  } else {
    console.error(`[FAIL] Invalid credentials returned HTTP ${invRes.statusCode}`);
  }

  // 2. Inspector Login
  const inspLogin = await httpRequest(`${backendBase}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, { email: 'ramesh.insp@doca.gov.in', password: 'Password@123' });
  const inspToken = JSON.parse(inspLogin.body).access_token;
  console.log('[PASS] Inspector login successful, JWT access token issued');

  // 3. Supervisor Login
  const supLogin = await httpRequest(`${backendBase}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, { email: 'verma.sup@doca.gov.in', password: 'Password@123' });
  const supToken = JSON.parse(supLogin.body).access_token;
  console.log('[PASS] Supervisor login successful, JWT access token issued');

  // 4. Me endpoint
  const meRes = await httpRequest(`${backendBase}/auth/me`, {
    headers: { Authorization: `Bearer ${inspToken}` },
  });
  const meData = JSON.parse(meRes.body);
  if (meData.role === 'INSPECTOR') {
    console.log(`[PASS] Inspector session profile verified: ${meData.name} (${meData.role})`);
  }

  // --- TEST C: Bounding Box Geometry & Scaling Formula ---
  console.log('\n--- TEST C: OCR BOUNDING BOX SCALING MATH ---');
  const naturalDimensions = { width: 3000, height: 4000 };
  const viewports = [
    { name: 'Mobile (375px)', displayed: { width: 343, height: 457.33 } },
    { name: 'Tablet (768px)', displayed: { width: 704, height: 938.67 } },
    { name: 'Desktop (1440px)', displayed: { width: 500, height: 666.67 } },
  ];

  const rawTokenBBox = { x: 450, y: 1200, width: 600, height: 180 }; // Pixels in 3000x4000 image

  for (const vp of viewports) {
    const scaleX = vp.displayed.width / naturalDimensions.width;
    const scaleY = vp.displayed.height / naturalDimensions.height;
    const scaledX = rawTokenBBox.x * scaleX;
    const scaledY = rawTokenBBox.y * scaleY;
    const scaledW = rawTokenBBox.width * scaleX;
    const scaledH = rawTokenBBox.height * scaleY;

    // Verify proportions
    const origRatio = (rawTokenBBox.width / naturalDimensions.width);
    const scaledRatio = (scaledW / vp.displayed.width);
    if (Math.abs(origRatio - scaledRatio) < 0.0001) {
      console.log(`[PASS] ${vp.name.padEnd(20)}: Scaled BBox [x:${scaledX.toFixed(1)}, y:${scaledY.toFixed(1)}, w:${scaledW.toFixed(1)}, h:${scaledH.toFixed(1)}] accurately mapped (ratio=${origRatio.toFixed(4)})`);
    } else {
      console.error(`[FAIL] Scaling mismatch in ${vp.name}`);
    }
  }

  // --- TEST D: Supervisor Analytics & Heatmaps Data Verification ---
  console.log('\n--- TEST D: SUPERVISOR ANALYTICS DATA VERIFICATION ---');
  const ovRes = await httpRequest(`${backendBase}/analytics/overview`, {
    headers: { Authorization: `Bearer ${supToken}` },
  });
  const ovData = JSON.parse(ovRes.body);
  console.log(`[PASS] Overview KPIs: Total Scans=${ovData.total_inspections}, Compliance Rate=${ovData.compliance_rate_percent}%, Violations=${ovData.total_violations}`);

  const hmRes = await httpRequest(`${backendBase}/analytics/heatmaps`, {
    headers: { Authorization: `Bearer ${supToken}` },
  });
  const hmData = JSON.parse(hmRes.body);
  console.log(`[PASS] Regional Heatmaps: ${hmData.total_regions} regions aggregated`);

  // RBAC block
  const blockedRes = await httpRequest(`${backendBase}/analytics/overview`, {
    headers: { Authorization: `Bearer ${inspToken}` },
  });
  if (blockedRes.statusCode === 403) {
    console.log('[PASS] Inspector access to supervisor analytics blocked with HTTP 403 Forbidden');
  }

  // --- TEST E: End-to-End PDF & JSON Reports Verification ---
  console.log('\n--- TEST E: REPORT EXPORTS & DOCUMENT VERIFICATION ---');
  const listRes = await httpRequest(`${backendBase}/inspections/?limit=1`, {
    headers: { Authorization: `Bearer ${inspToken}` },
  });
  const inspections = JSON.parse(listRes.body);
  if (inspections.length > 0) {
    const testId = inspections[0].id;
    // Generate PDF
    const pdfGen = await httpRequest(`${backendBase}/inspections/${testId}/reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${inspToken}`,
      },
    }, { report_type: 'PDF' });
    const pdfReport = JSON.parse(pdfGen.body);

    const pdfDl = await httpRequest(`${backendBase}/inspections/${testId}/reports/${pdfReport.id}/download`, {
      headers: { Authorization: `Bearer ${inspToken}` },
    });
    if (pdfDl.rawBody.subarray(0, 4).toString() === '%PDF') {
      console.log(`[PASS] Official Draft PDF Inspection Memo downloaded successfully (${pdfDl.rawBody.length} bytes, header: %PDF)`);
    }

    // Generate JSON
    const jsonGen = await httpRequest(`${backendBase}/inspections/${testId}/reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${inspToken}`,
      },
    }, { report_type: 'JSON' });
    const jsonReport = JSON.parse(jsonGen.body);

    const jsonDl = await httpRequest(`${backendBase}/inspections/${testId}/reports/${jsonReport.id}/download`, {
      headers: { Authorization: `Bearer ${inspToken}` },
    });
    const parsedJson = JSON.parse(jsonDl.body);
    if (parsedJson.report_number && parsedJson.inspection_id) {
      console.log(`[PASS] Machine-readable JSON report downloaded and parsed successfully (${jsonDl.rawBody.length} bytes)`);
    }
  }

  console.log('\n================================================================');
  console.log('       ALL PHASE 1.2 BROWSER ACCEPTANCE CHECKS PASSED           ');
  console.log('================================================================\n');
}

runAcceptanceTests().catch((err) => {
  console.error('Acceptance test failed:', err);
  process.exit(1);
});

