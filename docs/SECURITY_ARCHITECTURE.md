# CryptoTrace Security & Forensic Audit Architecture (Role 3 Integration)

> **Package Root:** `cryptotrace/`  
> **Primary Author Scope:** Role 3 — Senior Cybersecurity & Digital Forensics Engineer  
> **Integration Target:** Unified FastAPI + Async SQLAlchemy 2.0 + Alembic backend

---

## 1. Integrated Module Layout

- `cryptotrace/core/auth.py` — HMAC-SHA256 bearer auth, `ROLE_PERMISSIONS` RBAC, and horizontal investigation-scope guards (`get_auth_context`, `enforce_investigation_access`).
- `cryptotrace/core/middleware.py` — `SecurityHeadersMiddleware`, `RequestSizeLimitMiddleware` (early payload cap + malformed JSON + forbidden private-key/seed-phrase rejection), `SlidingWindowRateLimiter`, and `RateLimitHTTPMiddleware`.
- `cryptotrace/core/logging_utils.py` & `cryptotrace/core/logging.py` — Mandatory `SensitiveDataRedactionFilter` stripping bearer tokens, passwords, private keys, and DB credentials from logs.
- `cryptotrace/db/models/audit.py` & `alembic/versions/0002_add_security_audit_events.py` — `security_audit_events` table with monotonic `(investigation_id, sequence_number)` and `(investigation_id, previous_event_hash)` unique constraints.
- `cryptotrace/schemas/{security_common,findings,audit,security_inputs,security_requests}.py` — Pydantic v2 schemas and `SharedFindingAdapter` preserving frozen `cryptotrace/schemas/contracts.py`.
- `cryptotrace/services/security/` — Detectors, validator, TraceAI guardrails, `adapters.py` (Role 1 Bitcoin UTXO & Ethereum ERC-20 bridges), and `security_orchestrator.py` (modular entry point for Role 1 and future Role 2).
- `cryptotrace/services/audit/` — Canonical JSON + SHA-256 `audit_hasher.py`, async `AuditService`, `AuditVerifier`, and `AuditExportService` (with optional Ed25519 signing).
- `cryptotrace/api/v1/endpoints/security.py` — `/api/v1/security/*` REST endpoints mounted onto `api_v1_router`.

---

## 2. Async Audit Persistence & Concurrency Design

`AuditService` supports both FastAPI request-scoped `AsyncSession` (`Depends(get_db)`) and standalone `async_sessionmaker[AsyncSession]`:

1. **Per-Investigation Serialization:** Acquires a loop-scoped `asyncio.Lock` per `investigation_id`.
2. **PostgreSQL Row Locking:** Uses `SELECT ... FOR UPDATE` (`with_for_update()`) on non-SQLite dialects when reading the latest sequence number and head hash.
3. **Savepoint Isolation:** Inside a shared request `AsyncSession` (such as `InvestigationService`), `AuditService` wraps each append inside `async with session.begin_nested():` (SQL `SAVEPOINT`), ensuring transient lock/constraint retries never roll back uncommitted investigation or transaction writes.

---

## 3. Role 1 UTXO & ERC-20 Graph Adapter

`cryptotrace/services/security/adapters.py` bridges Role 1's `CanonicalTransaction` / `TransactionModel` and `TransactionGraph` without modifying Role 1 graph semantics:

- **Bitcoin UTXO:** Expands `vin` (`Address -> tx:<tx_hash>`) and `vout` (`tx:<tx_hash> -> Address`) into individual `TransactionRecord` evidence items (`TransferType.UTXO`) and validates `HEURISTIC_CO_SPEND` edges as explicitly unconfirmed (`is_confirmed=False`) participant links.
- **Ethereum Native & ERC-20:** Preserves native ETH/contract calls alongside per-log `TokenTransfer` (`TransferType.ERC20`, `token_contract`, `log_index`) so `GraphIntegrityAnalyzer` verifies multi-edge transactions accurately with zero false positives.

