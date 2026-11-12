# CryptoTrace Role 3 — API & Cross-Role Integration Guide

## 1. FastAPI Middleware & Compatibility

- **App Entrypoint:** `cryptotrace/main.py` (`app`)
- **Router Prefix:** `/api/v1/security` (`cryptotrace/api/v1/endpoints/security.py`)
- **Hardening Applied:**
  - `SecurityHeadersMiddleware` (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `Content-Security-Policy`, `X-Correlation-ID`)
  - `RequestSizeLimitMiddleware` (`413` on oversized bodies, `400` on malformed JSON or requests containing forbidden `private_key`, `seed_phrase`, `mnemonic`, `wallet_secret`, or `recovery_phrase` fields)
  - `RateLimitHTTPMiddleware` (`429` with `Retry-After`)
  - Explicit `CORSMiddleware` (`CORS_ALLOWED_ORIGINS`, defaulting to `http://localhost:3000` and `http://127.0.0.1:3000` for Role 4 Next.js; wildcard `*` rejected by `Settings`)
  - Team error contract preserved (`{"error", "message", "details", "correlation_id"}`) with sanitized validation details and redacted logs (`SensitiveDataRedactionFilter`)

---

## 2. Authentication & Authorization (`cryptotrace/core/auth.py`)

- Existing Role 1 routes (`/health`, `/api/v1/investigations/*`) remain unauthenticated by default so existing clients and tests continue working seamlessly (opt-in via `ENFORCE_AUTH_ON_CORE_ROUTES=true`).
- All `/api/v1/security/*` endpoints (except `/api/v1/security/health`) enforce fail-closed authentication (`get_auth_context`) and RBAC + investigation-level access checks (`enforce_investigation_access`).
- Missing `AUTH_SECRET` fails closed with `503 Service Unavailable`; missing/invalid/expired tokens return `401 Unauthorized`; missing role permission or out-of-scope `investigation_id` returns `403 Forbidden`.
- **Plugging in Team / Role 2 Auth:** Override `app.dependency_overrides[get_auth_context]` to map external JWT/session middleware into `AuthContext(actor_id, role, allowed_investigations, allow_all_investigations)`.

---

## 3. Security & Audit Endpoints

| Method & Path | Permission | Purpose |
| :--- | :--- | :--- |
| `GET /api/v1/security/health` | Public | Subsystem liveness status |
| `POST /api/v1/security/investigations/{investigation_id}/scan` | `run_security_analysis` | Run all Role 3 detectors & graph integrity on a persisted Role 1 investigation |
| `POST /api/v1/security/detect/address-poisoning` | `run_security_analysis` | Analyze address poisoning & look-alike wallets |
| `POST /api/v1/security/detect/dusting` | `run_security_analysis` | Asset-aware dusting detection |
| `POST /api/v1/security/detect/token-impersonation` | `run_security_analysis` | Contract-first token impersonation detection |
| `POST /api/v1/security/detect/graph-integrity` | `run_security_analysis` | NetworkX graph edge & decoy validation |
| `POST /api/v1/security/validate/blockchain-data` | `run_security_analysis` | Defensive validation & provider conflict check |
| `POST /api/v1/security/guardrails/traceai/inspect-input` | `run_traceai_guardrails` | Sanitize & isolate untrusted metadata; detect injection |
| `POST /api/v1/security/guardrails/traceai/validate-tool-call` | `run_traceai_guardrails` | Read-only TraceAI tool allowlist & scope gate |
| `POST /api/v1/security/guardrails/traceai/validate-output` | `run_traceai_guardrails` | Grounding, leakage, and epistemic label checks |
| `POST /api/v1/security/audit/events` | `write_audit` | Append SHA-256 hash-chained audit event |
| `POST /api/v1/security/audit/verify` | `verify_audit` | Verify investigation audit chain integrity |
| `GET /api/v1/security/audit/{investigation_id}` | `read_audit` | Retrieve investigation-scoped audit history |
| `GET /api/v1/security/audit/{investigation_id}/export` | `export_audit` | Export verifiable (+ optional Ed25519 signed) manifest |

---

## 4. Role 2 Integration Notes (ML & TraceAI)

- Use `SecurityOrchestrator(session).scan_investigation(investigation_id)` or `SharedFindingAdapter.to_shared_finding_dict(finding)` from `cryptotrace/schemas/findings.py` without altering `cryptotrace/schemas/contracts.py`.
- Wrap TraceAI prompt assembly, tool calls, and output responses with `TraceAISecurityGuardrails`.
- Record ML/AI lifecycle milestones via `AuditService(session).record_event(...)`.

