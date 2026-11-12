// Automated RBAC, Authentication & Role Redirect Test Suite
async function runRbacTests() {
  console.log("=== CRYPTOTRACE RBAC & AUTHENTICATION TESTS ===");
  const BASE_URL = "http://127.0.0.1:3000";
  let passed = 0;
  let failed = 0;

  function assert(name, condition, detail = "") {
    if (condition) {
      console.log(`  ✓ PASS: ${name}`);
      passed++;
    } else {
      console.error(`  ✗ FAIL: ${name}${detail ? ` -> ${detail}` : ""}`);
      failed++;
    }
  }

  function extractCookie(res) {
    const raw = res.headers.get("set-cookie") || "";
    const match = raw.match(/cryptotrace_session=[^;]+/);
    return match ? match[0] : "";
  }

  try {
    // 1. Unauthenticated /admin/dashboard redirects to /signin
    const unauthAdminPage = await fetch(`${BASE_URL}/admin/dashboard`, {
      redirect: "manual",
    });
    assert(
      "Unauthenticated /admin/dashboard redirects to /signin",
      unauthAdminPage.status === 307 &&
        (unauthAdminPage.headers.get("location") || "").includes("/signin")
    );

    // 2. Unauthenticated /api/admin/users returns 401
    const unauthAdminApi = await fetch(`${BASE_URL}/api/admin/users`);
    assert("Unauthenticated /api/admin/users returns 401", unauthAdminApi.status === 401);

    // 3. Public signup attempting ADMIN role is blocked (403)
    const adminSignup = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fullName: "Rogue Admin",
        email: `rogue-${Date.now()}@test.io`,
        password: "Password123!",
        confirmPassword: "Password123!",
        organization: "Test Org",
        role: "ADMIN",
        termsAccepted: true,
      }),
    });
    assert("Public signup with ADMIN role rejected with 403", adminSignup.status === 403);

    // 4. Sign in as Investigator
    const invSignin = await fetch(`${BASE_URL}/api/auth/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "investigator@cryptotrace.io",
        password: process.env.DEMO_INVESTIGATOR_PASSWORD || "Investigator!2025",
      }),
    });
    const invData = await invSignin.json();
    const invCookie = extractCookie(invSignin);
    assert(
      "Investigator sign-in returns 200 and /investigator/dashboard redirect",
      invSignin.status === 200 && invData.redirectTo === "/investigator/dashboard"
    );

    // 5. Investigator cannot access /api/admin/users (403)
    const invAdminApi = await fetch(`${BASE_URL}/api/admin/users`, {
      headers: { Cookie: invCookie },
    });
    assert("Investigator blocked from /api/admin/users with 403", invAdminApi.status === 403);

    // 6. Investigator redirected away from /admin/dashboard
    const invAdminPage = await fetch(`${BASE_URL}/admin/dashboard`, {
      headers: { Cookie: invCookie },
      redirect: "manual",
    });
    assert(
      "Investigator redirected from /admin/dashboard to /investigator/dashboard",
      invAdminPage.status === 307 &&
        (invAdminPage.headers.get("location") || "").includes("/investigator/dashboard")
    );

    // 7. Sign in as Analyst
    const anaSignin = await fetch(`${BASE_URL}/api/auth/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "analyst@cryptotrace.io",
        password: process.env.DEMO_ANALYST_PASSWORD || "Analyst!2025",
      }),
    });
    const anaData = await anaSignin.json();
    const anaCookie = extractCookie(anaSignin);
    assert(
      "Analyst sign-in returns 200 and /analyst/dashboard redirect",
      anaSignin.status === 200 && anaData.redirectTo === "/analyst/dashboard"
    );

    // 8. Analyst cannot create investigations (403)
    const anaCreateInv = await fetch(`${BASE_URL}/api/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Cookie: anaCookie },
      body: JSON.stringify({
        target: "0x098b716b8aaf21512996dc57eb0615e2383e2f96",
        network: "ETH",
        type: "address",
        mode: "demo",
      }),
    });
    assert("Analyst blocked from POST /api/investigations with 403", anaCreateInv.status === 403);

    // 9. Sign in as Admin and access /api/admin/users
    const adminSignin = await fetch(`${BASE_URL}/api/auth/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "admin@cryptotrace.io",
        password: process.env.DEMO_ADMIN_PASSWORD || "AdminTrace!2025",
      }),
    });
    const adminData = await adminSignin.json();
    const adminCookie = extractCookie(adminSignin);
    assert(
      "Admin sign-in returns 200 and /admin/dashboard redirect",
      adminSignin.status === 200 && adminData.redirectTo === "/admin/dashboard"
    );

    const adminUsersApi = await fetch(`${BASE_URL}/api/admin/users`, {
      headers: { Cookie: adminCookie },
    });
    assert("Admin can access /api/admin/users (200)", adminUsersApi.status === 200);
  } catch (err) {
    console.error("Test runner error:", err);
    failed++;
  }

  console.log(`\nResults: ${passed} PASSED, ${failed} FAILED`);
  if (failed > 0) process.exit(1);
}

runRbacTests();
