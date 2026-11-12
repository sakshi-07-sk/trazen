"""Authentication, RBAC, and investigation-level authorization hooks for CryptoTrace."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from cryptotrace.config import Settings, get_settings
from cryptotrace.core.logging_utils import get_security_logger

_LOGGER = get_security_logger()

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset(
        {
            "read_audit",
            "verify_audit",
            "export_audit",
            "write_audit",
            "run_security_analysis",
            "run_traceai_guardrails",
        }
    ),
    "lead_investigator": frozenset(
        {
            "read_audit",
            "verify_audit",
            "export_audit",
            "write_audit",
            "run_security_analysis",
            "run_traceai_guardrails",
        }
    ),
    "investigator": frozenset(
        {
            "read_audit",
            "verify_audit",
            "export_audit",
            "write_audit",
            "run_security_analysis",
            "run_traceai_guardrails",
        }
    ),
    "auditor": frozenset(
        {
            "read_audit",
            "verify_audit",
            "export_audit",
            "run_security_analysis",
        }
    ),
    "readonly_analyst": frozenset(
        {
            "read_audit",
            "verify_audit",
            "run_security_analysis",
            "run_traceai_guardrails",
        }
    ),
    "service": frozenset(
        {
            "verify_audit",
            "write_audit",
            "run_security_analysis",
            "run_traceai_guardrails",
        }
    ),
}


@dataclass(frozen=True)
class AuthContext:
    """Authenticated caller identity and investigation scope."""

    actor_id: str
    role: str
    allowed_investigations: frozenset[str] = frozenset()
    allow_all_investigations: bool = False

    def has_permission(self, permission: str) -> bool:
        """Check role-based permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, frozenset())

    def can_access_investigation(self, investigation_id: str) -> bool:
        """Verify investigation-level authorization (horizontal privilege boundary)."""
        if self.allow_all_investigations:
            return True
        return investigation_id in self.allowed_investigations


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - (len(data) % 4)) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def issue_hmac_token(
    *,
    actor_id: str,
    role: str,
    allowed_investigations: list[str] | tuple[str, ...] = (),
    allow_all_investigations: bool = False,
    secret: str,
    issuer: str = "cryptotrace",
    ttl_seconds: int = 3600,
) -> str:
    """Create a signed HMAC-SHA256 bearer token compatible with CryptoTrace RBAC."""
    if not secret:
        raise ValueError("Cannot issue token without a configured AUTH_SECRET.")
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Unsupported role '{role}'.")
    now = int(time.time())
    payload = {
        "sub": actor_id,
        "role": role,
        "inv": list(allowed_investigations),
        "all_inv": bool(allow_all_investigations),
        "iss": issuer,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    header_b64 = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
    )
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def verify_hmac_token(token: str, secret: str, expected_issuer: str = "cryptotrace") -> AuthContext:
    """Validate HMAC-SHA256 bearer token with constant-time signature comparison."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed bearer token structure.")
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(sig_b64)
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid token encoding.") from exc

    if header.get("alg") != "HS256":
        raise ValueError("Unsupported token signature algorithm.")
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature.")

    now = int(time.time())
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < now:
        raise ValueError("Bearer token has expired.")
    if expected_issuer and payload.get("iss") != expected_issuer:
        raise ValueError("Invalid token issuer.")

    actor_id = str(payload.get("sub") or "").strip()
    role = str(payload.get("role") or "").strip()
    if not actor_id or role not in ROLE_PERMISSIONS:
        raise ValueError("Invalid actor or role claim.")

    raw_inv = payload.get("inv") or []
    allowed_inv = frozenset(str(i) for i in raw_inv if str(i).strip())
    allow_all = bool(payload.get("all_inv", False)) and role in ("admin", "auditor")
    return AuthContext(
        actor_id=actor_id,
        role=role,
        allowed_investigations=allowed_inv,
        allow_all_investigations=allow_all,
    )


def get_auth_context(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    """FastAPI dependency enforcing fail-closed authentication (pluggable via dependency_overrides)."""
    if not settings.AUTH_REQUIRED:
        return AuthContext(actor_id="local-dev", role="investigator", allow_all_investigations=True)

    if not settings.AUTH_SECRET:
        _LOGGER.error("Authentication failed closed: AUTH_SECRET / CRYPTOTRACE_AUTH_SECRET is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization bearer header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_hmac_token(
            token=token,
            secret=settings.AUTH_SECRET,
            expected_issuer=settings.AUTH_ISSUER,
        )
    except ValueError as exc:
        _LOGGER.warning("Authentication rejected: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def enforce_investigation_access(
    auth: AuthContext,
    investigation_id: str,
    permission: str,
) -> None:
    """Fail-closed RBAC and investigation-scope check."""
    if not auth.has_permission(permission):
        _LOGGER.warning(
            "Authorization denied: actor='%s' role='%s' lacks permission='%s'",
            auth.actor_id,
            auth.role,
            permission,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this security operation.",
        )

    if not auth.can_access_investigation(investigation_id):
        _LOGGER.warning(
            "Investigation access denied: actor='%s' role='%s' attempted unauthorized access to investigation='%s'",
            auth.actor_id,
            auth.role,
            investigation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for the requested investigation.",
        )

