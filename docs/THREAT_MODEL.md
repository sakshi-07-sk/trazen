# CryptoTrace Threat Model (Role 3 — Adversarial Defense & Evidence Integrity)

> **Scope:** Security, Forensics, Evidence Integrity, API Hardening, and TraceAI Guardrails  
> **Core Principle:** Suspicious indicators are **not** automatic proof of malice. Findings must present supporting evidence, confidence bounds, and explicit analytical limitations.

---

## 1. Assets Requiring Protection

| Asset ID | Asset | Security Properties Needed |
| :--- | :--- | :--- |
| **A1** | **Forensic Audit Trail (SHA-256 Hash Chain)** | Integrity, tamper-evidence, ordering fidelity, availability, confidential scoping |
| **A2** | **Investigation & Case Records** | Confidentiality (investigation-level authorization), integrity |
| **A3** | **Blockchain Evidence & Graph Inputs** | Provenance fidelity, schema/type validity, freedom from silent provider tampering |
| **A4** | **Security Findings & Risk Assessments** | Accuracy (low false positives/negatives), explainability, read-only immutability against AI tampering |
| **A5** | **TraceAI System Prompts, Tools & Context** | Instruction integrity, tool-execution safety, protection against cross-investigation data leakage |
| **A6** | **Platform Secrets & Signing Keys** | Strict confidentiality (API keys, DB credentials, export signing keys; never wallet private keys/seed phrases) |
| **A7** | **API Availability & Service Stability** | Resilience against oversized inputs, algorithmic complexity attacks, and request floods |

## 2. Threat Matrix & Implemented Mitigations

| ID | Threat Scenario | Target | Mitigation Implemented | Residual Risk |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | **Address Poisoning** | A3, A4 | Chain-normalized similarity + contextual decoy/chronology correlation (`address_poisoning.py`) | Sophisticated 6+ char vanity decoys still require human confirmation |
| **T2** | **Look-Alike Wallet Spoofing** | A3, A4 | Checksum validation, chain isolation, Unicode confusable/bidi checks (`address_similarity.py`) | Legitimate vanity addresses can produce informational alerts |
| **T3** | **Dusting Attacks** | A3, A4 | Asset/decimal/chain-aware thresholds with exchange/airdrop/baseline suppression (`dusting_detector.py`) | Campaigns calibrated just above configured thresholds |
| **T4** | **Decoy & Graph Manipulation** | A3, A4 | NetworkX integrity validation supporting Bitcoin UTXO `tx:` nodes and ERC-20 logs (`graph_integrity.py`, `adapters.py`) | Sybil patterns with valid on-chain tx hashes remain probabilistic |
| **T5** | **Token Impersonation** | A3, A4 | Contract-first canonical registry, homoglyph inspection, decimal/chain mismatch (`token_impersonation.py`) | Coverage depends on canonical registry completeness |
| **T6** | **Untrusted Provider Data** | A3, A4 | Validation statuses + `upstream_source` independence tracking (`blockchain_validator.py`) | Single shared compromised upstream indexer cannot be caught without an independent RPC |
| **T7** | **TraceAI Prompt Injection** | A2, A4, A5, A6 | Untrusted data delimiters, NFKC/bidi stripping, read-only tool allowlist, citation grounding (`security_guardrails.py`) | Novel semantic phrasing requires continuous adversarial regression testing |
| **T8** | **Audit Record Tampering** | A1 | Async savepoint/lock-safe SHA-256 chain, gap/reorder/hash verification, Ed25519 manifest signing (`services/audit/`) | Hash chaining provides tamper-evidence, not physical immutability without external anchoring |
| **T9** | **Unauthorized Investigation Access** | A1, A2 | Fail-closed RBAC & investigation-scope checks on `/api/v1/security/*` (`core/auth.py`) | Core Role 1 routes await team-wide auth rollout (`ENFORCE_AUTH_ON_CORE_ROUTES`) |
| **T10** | **API Abuse & Data Leakage** | A6, A7 | Request size limit, secret-field rejection, rate limiting, explicit CORS, security headers, log redaction (`core/middleware.py`, `core/logging_utils.py`) | Volumetric DDoS requires upstream network/WAF controls |

