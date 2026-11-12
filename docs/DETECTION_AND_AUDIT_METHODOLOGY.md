# CryptoTrace Role 3 — Detection & Audit Verification Methodology

## 1. Address Poisoning & Look-Alike Wallet Detection

- **Modules:** `cryptotrace/services/security/address_similarity.py`, `cryptotrace/services/security/address_poisoning.py`
- **Chain Normalization & Checksums:**
  - EVM chains (`ethereum`, `polygon`, `bsc`, `arbitrum`, `optimism`, `base`, `avalanche`): `0x` + 40 hex chars, normalized lowercase for canonical comparison.
  - Bitcoin (`bitcoin`): Base58Check (`1...`, `3...`) with 4-byte double-SHA256 checksum verification; Bech32/Bech32m (`bc1...`) rejecting mixed case per BIP-173/350.
  - Solana (`solana`): Case-sensitive Base58 (`32..44` chars).
  - TRON (`tron`): Case-sensitive `T...` Base58Check with double-SHA256 checksum verification.
- **Similarity Metrics:** Prefix match, suffix match, normalized Levenshtein similarity (`rapidfuzz`), vanity bookend score, low edit-distance substitution, and Unicode confusable/invisible character inspection (`inspect_text_confusables`).
- **False-Positive Guardrail:** Address similarity alone never produces an `ADDRESS_POISONING` accusation; poisoning findings require contextual correlation (zero/micro-value decoy transfers, post-counterparty chronology, repeated decoy appearances, or subsequent outbound substitution).

## 2. Asset-Aware Dusting Detection

- **Module:** `cryptotrace/services/security/dusting_detector.py`
- **Threshold Resolution:** Contract overrides → `{chain}:{transfer_type}:{symbol}` asset rules → decimal-scaled fallback → chain-native fallback.
- **Suppression:** Excludes single ordinary small payments, baseline small-payment wallets, labeled exchange payouts, and legitimate airdrop claims.

## 3. Graph Poisoning & Decoy Edge Detection

- **Modules:** `cryptotrace/services/security/graph_integrity.py`, `cryptotrace/services/security/adapters.py`
- **Checks:** Duplicate edges, missing declared nodes, missing or unbacked `tx_hash` references, chain mismatches, reversed/mismatched endpoints, block/asset/contract/amount/provenance mismatches, heuristic edges marked `is_confirmed=True`, and contradictions against independently verified chain records.
- **Multi-Edge Support:** Supports Role 1 Bitcoin UTXO intermediate `tx:<tx_hash>` topology and Ethereum multi-log ERC-20 `TokenTransfer` edges without false positives.

## 4. Token Impersonation Detection

- **Module:** `cryptotrace/services/security/token_impersonation.py`
- **Primary Identity Rule:** Identifies tokens by `(chain, contract_address)` against verified registries (`DEFAULT_CANONICAL_TOKENS`), detecting Unicode homoglyphs/invisible bidi chars, symbol/name collisions, look-alike contracts, wrong-chain contracts, decimal mismatches, and historical metadata drift.

## 5. Defensive Blockchain Data Validation

- **Module:** `cryptotrace/services/security/blockchain_validator.py`
- **Statuses:** `VALID`, `INVALID`, `UNVERIFIED`, `CONFLICTING`, `INCOMPLETE` and `IndependentVerificationStatus` (`VERIFIED_AGREE`, `VERIFIED_CONFLICT`, `UNVERIFIED`, `NOT_INDEPENDENT`).
- **Multi-Provider Independence:** Tracks `upstream_source` per `ProviderObservation` so wrappers sharing an upstream provider are flagged `NOT_INDEPENDENT`.

## 6. Hash-Chained Forensic Audit & Verification

- **Modules:** `cryptotrace/services/audit/{audit_hasher,audit_service,audit_verifier,audit_export}.py`
- **Canonical Serialization (`canonical-json-v1`):** Deterministic sorted JSON, `Decimal` normalization, UTC ISO-8601 timestamps, `NaN`/`Inf` rejection, and automatic redaction of sensitive key names.
- **SHA-256 Chain (`cryptotrace-audit-v1`):** Domain-separated genesis anchor (`CryptoTrace:AuditGenesis:v1:<investigation_id>`), payload digest, and full event envelope hash committing to `event_id`, `sequence_number`, `actor`, `actor_role`, `event_type`, `timestamp`, `payload_hash`, and `previous_event_hash`.
- **Tamper-Evident Export:** `AuditExportService` generates verifiable manifests with optional Ed25519 signatures.

