// Node.js pure ESM test runner for cryptographic input validation
function validateCryptoInput(input, expectedNetwork, expectedType) {
  const trimmed = (input || "").trim();
  if (!trimmed) {
    return { isValid: false, error: "Input address or transaction hash is required" };
  }

  const isEthAddress = /^0x[a-fA-F0-9]{40}$/.test(trimmed);
  const isEthTx = /^0x[a-fA-F0-9]{64}$/.test(trimmed);
  const isBtcBech32 = /^bc1[a-zA-HJ-NP-Z0-9]{25,62}$/i.test(trimmed);
  const isBtcLegacyOrScript = /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(trimmed);
  const isBtcAddress = isBtcBech32 || isBtcLegacyOrScript;
  const isBtcTx = /^[a-fA-F0-9]{64}$/.test(trimmed) && !trimmed.startsWith("0x");

  let detectedNetwork;
  let detectedType;

  if (isEthAddress) {
    detectedNetwork = "ETH";
    detectedType = "address";
  } else if (isEthTx) {
    detectedNetwork = "ETH";
    detectedType = "transaction";
  } else if (isBtcAddress) {
    detectedNetwork = "BTC";
    detectedType = "address";
  } else if (isBtcTx) {
    detectedNetwork = "BTC";
    detectedType = "transaction";
  }

  if (!detectedNetwork || !detectedType) {
    return {
      isValid: false,
      error: "Invalid format. Expected a valid Ethereum address (0x...), Ethereum tx hash (0x...), Bitcoin address (1..., 3..., bc1...), or 64-char Bitcoin tx hash.",
    };
  }

  if (expectedNetwork && detectedNetwork !== expectedNetwork) {
    return {
      isValid: false,
      error: `Input format corresponds to ${detectedNetwork}, but selected network is ${expectedNetwork}.`,
      detectedNetwork,
      detectedType,
    };
  }

  if (expectedType && detectedType !== expectedType) {
    return {
      isValid: false,
      error: `Input format corresponds to a ${detectedType}, but selected target type is ${expectedType}.`,
      detectedNetwork,
      detectedType,
    };
  }

  return {
    isValid: true,
    detectedNetwork,
    detectedType,
  };
}

console.log("=== CRYPTOTRACE FORENSIC VALIDATION SUITE ===");
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

// 1. Ethereum Address
const r1 = validateCryptoInput("0x098b716b8aaf21512996dc57eb0615e2383e2f96");
assert("Ethereum target address format", r1.isValid && r1.detectedNetwork === "ETH" && r1.detectedType === "address");

// 2. Ethereum Tx Hash
const r2 = validateCryptoInput("0x3a4b912c01992e5f8841a12001992bc45012e88a7199bc4123d45e671239aa01");
assert("Ethereum transaction hash format", r2.isValid && r2.detectedNetwork === "ETH" && r2.detectedType === "transaction");

// 3. Bitcoin Bech32 Address
const r3 = validateCryptoInput("bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6");
assert("Bitcoin Bech32 address format", r3.isValid && r3.detectedNetwork === "BTC" && r3.detectedType === "address");

// 4. Bitcoin Legacy Address
const r4 = validateCryptoInput("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa");
assert("Bitcoin Legacy 1... address format", r4.isValid && r4.detectedNetwork === "BTC");

// 5. Bitcoin Script 3... Address
const r5 = validateCryptoInput("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy");
assert("Bitcoin Script 3... address format", r5.isValid && r5.detectedNetwork === "BTC");

// 6. Bitcoin Tx Hash
const r6 = validateCryptoInput("7b4c91a02934ef8192038475628192a3b4c5d6e7f8091234567890abcdef1234");
assert("Bitcoin 64-char transaction hash format", r6.isValid && r6.detectedNetwork === "BTC" && r6.detectedType === "transaction");

// 7. Network Mismatch Rejection
const r7 = validateCryptoInput("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "BTC", "address");
assert("Rejects Ethereum address when Bitcoin network selected", !r7.isValid);

// 8. Target Type Mismatch Rejection
const r8 = validateCryptoInput("0x098b716b8aaf21512996dc57eb0615e2383e2f96", "ETH", "transaction");
assert("Rejects 40-char address when transaction hash type selected", !r8.isValid);

// 9. Malformed input rejection
const r9 = validateCryptoInput("invalid-random-data-string");
assert("Rejects arbitrary non-crypto strings", !r9.isValid);

console.log(`\nResults: ${passed} PASSED, ${failed} FAILED\n`);
if (failed > 0) process.exit(1);
