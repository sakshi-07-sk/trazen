# Security Policy — CryptoTrace

## Status

Role 3 security, blockchain validation, TraceAI guardrails, and async tamper-evident SHA-256 audit services are integrated into `cryptotrace/`. Production deployment requires configuring environment-managed secrets (`AUTH_SECRET` / `CRYPTOTRACE_AUTH_SECRET`, `DATABASE_URL`, explicit `CORS_ALLOWED_ORIGINS`, and optional `AUDIT_SIGNING_PRIVATE_KEY_PEM`).

---

## Security & Digital Forensics Scope (Role 3)

CryptoTrace handles adversarial blockchain investigations where both **on-chain inputs** and **investigation consumers** may be hostile. Role 3 owns the security posture and forensic integrity of the platform across:

1. **Adversarial On-Chain & Graph Threat Detection**
   - Address poisoning detection (`cryptotrace/services/security/address_poisoning.py`)
   - Look-alike wallet detection (`cryptotrace/services/security/address_similarity.py`)
   - Asset-aware dusting detection (`cryptotrace/services/security/dusting_detector.py`)
   - Graph integrity & decoy-edge detection (`cryptotrace/services/security/graph_integrity.py`, `cryptotrace/services/security/adapters.py`)
   - Contract-first token impersonation detection (`cryptotrace/services/security/token_impersonation.py`)
2. **Forensic Data & Audit Integrity**
   - Defensive blockchain data validation & multi-provider conflict checks (`cryptotrace/services/security/blockchain_validator.py`)
   - Async SHA-256 hash-chained audit system (`cryptotrace/services/audit/audit_service.py`, `cryptotrace/services/audit/audit_hasher.py`)
   - Deterministic audit verification and Ed25519-signed manifest export (`cryptotrace/services/audit/audit_verifier.py`, `cryptotrace/services/audit/audit_export.py`)
3. **Application & AI Defense**
   - API security: fail-closed RBAC/investigation auth (`cryptotrace/core/auth.py`), size/secret/rate-limit/header middlewares (`cryptotrace/core/middleware.py`), explicit CORS, and log redaction (`cryptotrace/core/logging_utils.py`)
   - TraceAI prompt injection defense & read-only tool gating (`cryptotrace/services/security/security_guardrails.py`)

---

## Core Security Invariants

1. **Validate Before Trusting:** Externally sourced or connector-supplied blockchain records SHOULD pass through `BlockchainDataValidator` (`cryptotrace/services/security/blockchain_validator.py`) before high-stakes risk scoring or AI reasoning.
2. **Tamper-Evident Audit Trail:** Security scans, investigation lifecycle milestones, and TraceAI guardrail evaluations emit canonicalized events to `AuditService` (`security_audit_events`). Hash chaining provides **cryptographic tamper-evidence**, not physical immutability—external checkpoints or Ed25519-signed exports are required to detect silent tail truncation.
3. **Untrusted Data Isolation in TraceAI:** On-chain strings (token symbols/names, transaction memos, calldata, ENS labels) are **untrusted adversarial input**. They MUST pass through `TraceAISecurityGuardrails` (`inspect_and_isolate_context`, `validate_tool_call`, `validate_ai_output`) and remain strictly read-only with respect to forensic evidence.
4. **Fail-Closed Security Boundaries:** `/api/v1/security/*` endpoints (except `/health`) enforce fail-closed authentication (`get_auth_context`) and investigation-level RBAC (`enforce_investigation_access`). Missing `AUTH_SECRET` fails closed with `503`. Existing Role 1 routes remain unauthenticated by default unless `ENFORCE_AUTH_ON_CORE_ROUTES=true` is enabled.
5. **Zero Secrets or Live Evidence in VCS:** Never commit API keys, RPC credentials, signing keys, `.env` files, or sensitive real-world forensic data. Requests containing `private_key`, `seed_phrase`, `mnemonic`, `wallet_secret`, or `recovery_phrase` fields are rejected with HTTP `400`, and logs are filtered via `SensitiveDataRedactionFilter`.

