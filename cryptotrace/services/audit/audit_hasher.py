"""Deterministic canonical JSON serialization and SHA-256 hash-chain construction."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

HASH_ALGORITHM = "SHA-256"
SERIALIZATION_VERSION = "canonical-json-v1"
HASH_CONSTRUCTION_VERSION = "cryptotrace-audit-v1"

# Keys whose raw values must NEVER be persisted inside forensic audit payloads
SENSITIVE_AUDIT_KEYS: frozenset[str] = frozenset(
    {
        "private_key",
        "seed_phrase",
        "mnemonic",
        "wallet_secret",
        "signing_key",
        "password",
        "passwd",
        "secret",
        "api_secret",
        "access_token",
        "refresh_token",
        "authorization",
    }
)


def sanitize_audit_payload(value: Any) -> Any:
    """Recursively redact sensitive secret keys before audit serialization."""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for k, v in value.items():
            key_str = str(k)
            if key_str.strip().lower() in SENSITIVE_AUDIT_KEYS:
                sanitized[key_str] = "[REDACTED]"
            else:
                sanitized[key_str] = sanitize_audit_payload(v)
        return sanitized
    if isinstance(value, (list, tuple)):
        return [sanitize_audit_payload(item) for item in value]
    return value


def _normalize_for_canonical_json(value: Any) -> Any:
    """Normalize supported Python values into deterministic JSON primitives."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite float values (NaN/Inf) are forbidden in canonical JSON.")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Non-finite Decimal values are forbidden in canonical JSON.")
        normalized = value.normalize()
        # Avoid scientific notation ambiguities for clean string determinism
        return (
            format(normalized, "f")
            if "E" in str(normalized) or "e" in str(normalized)
            else str(normalized)
        )
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {
            str(k): _normalize_for_canonical_json(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_for_canonical_json(item) for item in value]
    if isinstance(value, set):
        normalized_items = [_normalize_for_canonical_json(item) for item in value]
        return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True))
    return str(value)


def canonicalize_json(value: Any) -> str:
    """Produce byte-deterministic canonical JSON (sorted keys, UTF-8, compact separators)."""
    normalized = _normalize_for_canonical_json(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_genesis_hash(investigation_id: str) -> str:
    """Compute the deterministic domain-separated genesis anchor hash for an investigation."""
    material = f"CryptoTrace:AuditGenesis:v1:{investigation_id}".encode()
    return hashlib.sha256(material).hexdigest()


def compute_payload_hash(canonical_payload_json: str) -> str:
    """Compute domain-separated SHA-256 hash over canonical payload JSON."""
    material = f"CryptoTrace:Payload:v1:{canonical_payload_json}".encode()
    return hashlib.sha256(material).hexdigest()


def compute_event_hash(
    *,
    event_id: str,
    sequence_number: int,
    investigation_id: str,
    actor: str,
    actor_role: str,
    event_type: str,
    timestamp: str,
    payload_hash: str,
    previous_event_hash: str,
    hash_algorithm: str = HASH_ALGORITHM,
    serialization_version: str = SERIALIZATION_VERSION,
    hash_construction_version: str = HASH_CONSTRUCTION_VERSION,
) -> str:
    """Compute SHA-256 hash committing to the full audit envelope and predecessor link."""
    envelope = {
        "event_id": event_id,
        "sequence_number": sequence_number,
        "investigation_id": investigation_id,
        "actor": actor,
        "actor_role": actor_role,
        "event_type": event_type,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "previous_event_hash": previous_event_hash,
        "hash_algorithm": hash_algorithm,
        "serialization_version": serialization_version,
        "hash_construction_version": hash_construction_version,
    }
    canonical_envelope = canonicalize_json(envelope)
    material = f"CryptoTrace:AuditEvent:v1:{canonical_envelope}".encode()
    return hashlib.sha256(material).hexdigest()
