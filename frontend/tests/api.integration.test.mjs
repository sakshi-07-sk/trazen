// API Integration Test Suite for CryptoTrace Endpoints
async function runApiTests() {
  console.log("=== CRYPTOTRACE API ENDPOINT INTEGRATION TESTS ===");
  const BASE_URL = "http://127.0.0.1:3000";
  let passed = 0;
  let failed = 0;

  function assert(name, condition, msg) {
    if (condition) {
      console.log(`  ✓ PASS: ${name}`);
      passed++;
    } else {
      console.error(`  ✗ FAIL: ${name} -> ${msg}`);
      failed++;
    }
  }

  try {
    // 1. GET /api/stats
    const statsRes = await fetch(`${BASE_URL}/api/stats`);
    assert("GET /api/stats status is 200", statsRes.status === 200);
    const stats = await statsRes.json();
    assert("Stats returns totalInvestigations", typeof stats.totalInvestigations === "number" && stats.totalInvestigations > 0);

    // 2. GET /api/investigations
    const casesRes = await fetch(`${BASE_URL}/api/investigations`);
    assert("GET /api/investigations status is 200", casesRes.status === 200);
    const cases = await casesRes.json();
    assert("Returns at least 2 default investigations", Array.isArray(cases) && cases.length >= 2);

    // 3. GET /api/investigations/CT-CASE-2024-8841
    const singleCaseRes = await fetch(`${BASE_URL}/api/investigations/CT-CASE-2024-8841`);
    assert("GET specific case status is 200", singleCaseRes.status === 200);
    const caseData = await singleCaseRes.json();
    assert("Case contains nodes and edges", caseData.nodes?.length > 0 && caseData.edges?.length > 0);
    assert("Case contains findings and receivers", caseData.findings?.length > 0 && caseData.receivers?.length > 0);

    // 4. POST /api/investigations (Validation Rejection)
    const badPostRes = await fetch(`${BASE_URL}/api/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: "bad-crypto-address", network: "ETH", type: "address" }),
    });
    assert("POST invalid target returns 400", badPostRes.status === 400);

    // 5. POST /api/investigations (Live provider failure without credentials)
    const livePostRes = await fetch(`${BASE_URL}/api/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target: "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
        network: "ETH",
        type: "address",
        mode: "live",
      }),
    });
    assert("POST live mode without RPC keys returns 503 provider error", livePostRes.status === 503);
    const liveError = await livePostRes.json();
    assert("Provider error explains that fabricated data is never returned", liveError.message?.includes("fabricated data is never returned"));

    // 6. POST /api/investigations (Demo Case creation)
    const demoPostRes = await fetch(`${BASE_URL}/api/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target: "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
        network: "ETH",
        type: "address",
        mode: "demo",
      }),
    });
    assert("POST demo mode returns 200", demoPostRes.status === 200);

    // 7. POST /api/copilot (Grounded Question)
    const copilotRes = await fetch(`${BASE_URL}/api/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caseId: "CT-CASE-2024-8841",
        query: "Why is this wallet suspicious?",
      }),
    });
    assert("POST /api/copilot status is 200", copilotRes.status === 200);
    const copilotData = await copilotRes.json();
    assert("Copilot response is grounded with evidence IDs", copilotData.evidenceIds?.length > 0);
    assert("Copilot cites detection rule", copilotData.message?.includes("RULE-SANCTION-OFAC"));

    // 8. GET /api/audit/verify (SHA-256 Hash Chain)
    const verifyRes = await fetch(`${BASE_URL}/api/audit/verify?caseId=CT-CASE-2024-8841`);
    assert("GET /api/audit/verify status is 200", verifyRes.status === 200);
    const verifyData = await verifyRes.json();
    assert("Audit verification reports INTACT hash-chain", verifyData.chainIntegrity === "INTACT" && verifyData.verified === true);
    assert("Audit verification provides head Merkle hash", typeof verifyData.headHash === "string" && verifyData.headHash.length > 20);

    console.log(`\nAPI Test Results: ${passed} PASSED, ${failed} FAILED\n`);
    if (failed > 0) process.exit(1);
  } catch (err) {
    console.error("API test execution error:", err);
    process.exit(1);
  }
}

runApiTests();
