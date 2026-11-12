import { validateCryptoInput } from "../src/lib/validation";

function runTests() {
  console.log("Running CryptoTrace Forensic Validation Unit Tests...\n");
  let passed = 0;
  let failed = 0;

  function assert(name: string, condition: boolean, message?: string) {
    if (condition) {
      console.log(`  ✓ ${name}`);
      passed++;
    } else {
      console.error(`  ✗ ${name}: ${message || "Assertion failed"}`);
      failed++;
    }
  }

  // 1. Ethereum Address Validation
  const validEthAddr = "0x098b716b8aaf21512996dc57eb0615e2383e2f96";
  const ethRes = validateCryptoInput(validEthAddr);
  assert("Valid ETH address accepted", ethRes.isValid && ethRes.detectedNetwork === "ETH" && ethRes.detectedType === "address");

  // 2. Ethereum Tx Hash Validation
  const validEthTx = "0x3a4b912c01992e5f8841a12001992bc45012e88a7199bc4123d45e671239aa01";
  const ethTxRes = validateCryptoInput(validEthTx);
  assert("Valid ETH tx hash accepted", ethTxRes.isValid && ethTxRes.detectedNetwork === "ETH" && ethTxRes.detectedType === "transaction");

  // 3. Bitcoin Bech32 Address Validation
  const validBtcAddr = "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6";
  const btcRes = validateCryptoInput(validBtcAddr);
  assert("Valid BTC bech32 address accepted", btcRes.isValid && btcRes.detectedNetwork === "BTC" && btcRes.detectedType === "address");

  // 4. Bitcoin Legacy Address Validation
  const validBtcLegacy = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
  const btcLegRes = validateCryptoInput(validBtcLegacy);
  assert("Valid BTC legacy address accepted", btcLegRes.isValid && btcLegRes.detectedNetwork === "BTC");

  // 5. Bitcoin Tx Hash Validation
  const validBtcTx = "7b4c91a02934ef8192038475628192a3b4c5d6e7f8091234567890abcdef1234";
  const btcTxRes = validateCryptoInput(validBtcTx);
  assert("Valid BTC tx hash accepted", btcTxRes.isValid && btcTxRes.detectedNetwork === "BTC" && btcTxRes.detectedType === "transaction");

  // 6. Network Mismatch Detection
  const mismatchRes = validateCryptoInput(validEthAddr, "BTC", "address");
  assert("Network mismatch flagged", !mismatchRes.isValid && mismatchRes.error?.includes("selected network is BTC"));

  // 7. Invalid String Rejection
  const invalidRes = validateCryptoInput("invalid-token-input-404");
  assert("Invalid token string rejected", !invalidRes.isValid);

  console.log(`\nTest results: ${passed} passed, ${failed} failed.\n`);
  if (failed > 0) process.exit(1);
}

runTests();
