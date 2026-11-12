import { test, expect } from "@playwright/test";

test.describe("CryptoTrace Investigation Platform", () => {
  test("1. Dashboard loading and KPI rendering", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/CryptoTrace/i);

    // Check header and SOC ready indicator
    await expect(page.locator("text=CYBERTRACE FORENSIC COMMAND CENTER")).toBeVisible();
    await expect(page.locator("text=SOC READY")).toBeVisible();

    // Check KPI cards
    await expect(page.getByText("INVESTIGATIONS", { exact: true })).toBeVisible();
    await expect(page.locator("text=WALLETS ANALYZED")).toBeVisible();
    await expect(page.locator("text=TRANSACTIONS TRACED")).toBeVisible();
    await expect(page.getByText("SUSPICIOUS FINDINGS", { exact: true })).toBeVisible();

    // Check recent cases table
    await expect(page.locator("table").getByText("Operation Lazarus Splitter")).toBeVisible();
  });

  test("2. New Investigation form and address validation", async ({ page }) => {
    await page.goto("/");
    // Click New Investigation in navbar
    await page.click("button:has-text('NEW INVESTIGATION')");

    await expect(page.locator("text=INITIATE ON-CHAIN INVESTIGATION")).toBeVisible();

    // Input invalid address
    await page.fill("input[placeholder*='0x...']", "invalid-crypto-string");
    await page.click("button:has-text('START FORENSIC INVESTIGATION')");

    // Check validation error
    await expect(
      page.locator("text=Invalid format. Expected a valid Ethereum address")
    ).toBeVisible();

    // Test live provider error mode when external RPC is unavailable
    await page.click("button:has-text('LIVE CONSENSUS RPC')");
    await page.fill("input[placeholder*='0x...']", "0x098b716b8aaf21512996dc57eb0615e2383e2f96");
    await page.click("button:has-text('START FORENSIC INVESTIGATION')");

    // Must show clear provider-error state and never fabricated data
    await expect(page.locator("text=LIVE INGESTION PROVIDER FAILURE")).toBeVisible();
    await expect(page.locator("text=SWITCH TO DEMO INVESTIGATION MODE")).toBeVisible();
  });

  test("3. Quick demo load and Cytoscape graph rendering", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('NEW INVESTIGATION')");

    // Click sample case button
    await page.click("button:has-text('Lazarus ETH Case')");
    await page.click("button:has-text('START FORENSIC INVESTIGATION')");

    // Wait for graph tab to be active
    await expect(page.locator("text=CASE: CT-CASE-2024-8841")).toBeVisible();
    await expect(page.locator("text=GRAPH FILTERS")).toBeVisible();
    await expect(page.locator("text=NODES:")).toBeVisible();
  });

  test("4. Wallet Intelligence view and risk meter", async ({ page }) => {
    await page.goto("/");
    // Switch to Wallet Intelligence tab
    await page.click("button:has-text('WALLET INTELLIGENCE')");

    await expect(page.locator("text=WALLET INTELLIGENCE DIRECTORY")).toBeVisible();
    await expect(page.locator("text=Lazarus Associated Cluster #4").first()).toBeVisible();

    // Inspect first wallet
    await page.locator("text=INSPECT IN GRAPH →").first().click();
    await expect(page.locator("text=THREAT SCORE")).toBeVisible();
    await expect(page.locator("text=DATA PROVENANCE & OBSERVABILITY")).toBeVisible();
  });

  test("5. Suspicious findings filtering and detection rules", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('SUSPICIOUS FINDINGS')");

    await expect(page.locator("text=OFAC Sanctioned Entity Ingress")).toBeVisible();
    // Click finding to expand details
    await page.locator("text=OFAC Sanctioned Entity Ingress").click();
    await expect(page.locator("text=RULE-SANCTION-OFAC-V3").first()).toBeVisible();

    // Filter by Critical
    await page.locator("select:has(option[value='CRITICAL'])").selectOption("CRITICAL");
    await expect(page.locator("text=SHOWING 2 OF 5 FINDINGS")).toBeVisible();
  });

  test("6. Receiver intelligence ranking and attribution ethics", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('RECEIVER INTELLIGENCE')");

    // Check methodology and ethics disclaimer
    await expect(
      page.locator("text=FORENSIC ATTRIBUTION METHODOLOGY & RESTRAINT PRINCIPLE")
    ).toBeVisible();
    await expect(
      page.locator("text=CryptoTrace does not claim to identify the real-world legal person")
    ).toBeVisible();

    // Check Rank #1 Candidate
    await expect(page.locator("text=#1").first()).toBeVisible();
    await expect(page.locator("text=Tornado.Cash 100 ETH Privacy Pool").first()).toBeVisible();
  });

  test("7. Investigation timeline chronological rail", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('TIMELINE')");

    await expect(page.locator("text=Target Ingress Funded")).toBeVisible();
    await expect(page.locator("text=ORDER: NEWEST FIRST")).toBeVisible();
  });

  test("8. Evidence Vault and SHA-256 Hash-Chain Verification", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('EVIDENCE VAULT')");

    await expect(page.locator("text=CRYPTOGRAPHIC EVIDENCE VAULT")).toBeVisible();
    await expect(page.locator("text=EVID-ETH-7721")).toBeVisible();

    // Click verify button
    await page.click("button:has-text('VERIFY HASH-CHAIN INTEGRITY')");
    await expect(
      page.locator("text=LEDGER INTEGRITY VERIFIED (SHA-256 CHECKPOINT)")
    ).toBeVisible();
  });

  test("9. TraceAI Copilot grounded questions and offline fallback", async ({ page }) => {
    await page.goto("/");
    // Open copilot drawer
    await page.click("button:has-text('TraceAI COPILOT')");

    await expect(page.locator("text=TraceAI COPILOT").first()).toBeVisible();
    await expect(page.locator("text=GROUNDED FORENSICS")).toBeVisible();

    // Click suggested query
    await page.click("button:has-text('Why is this wallet suspicious?')");
    await expect(page.locator("text=Based on forensic detection rule")).toBeVisible();
  });

  test("10. Forensic Report Generation Dossier", async ({ page }) => {
    await page.goto("/");
    await page.click("button:has-text('DOSSIER REPORT')");

    await expect(page.locator("text=FORENSIC CASE DOSSIER PREVIEW")).toBeVisible();
    await expect(page.locator("text=1. Case Identification & Target Scope")).toBeVisible();
    await expect(page.locator("text=3. Suspicious Activity Findings Matrix")).toBeVisible();
    await expect(page.locator("text=5. Tamper-Evident Audit & Data Provenance")).toBeVisible();
  });
});
