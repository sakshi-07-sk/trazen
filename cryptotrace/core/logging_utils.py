"""Sensitive-data log redaction filter and safe security logging."""

from __future__ import annotations

import logging
import re

_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*"), r"\1[REDACTED]"),
    (
        re.compile(
            r"(?i)(private_key|seed_phrase|mnemonic|wallet_secret|signing_key|password|passwd|api_secret|api_key|auth_secret)\s*[:=]\s*['\"]?[^\s,'\";}]+['\"]?"
        ),
        r"\1=[REDACTED]",
    ),
    (re.compile(r"(?i)(postgres(?:ql)?|mysql|mongodb)://[^:\s]+:[^@\s]+@"), r"\1://[REDACTED]@"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY_PEM]",
    ),
)


def redact_sensitive_text(message: str) -> str:
    """Mask secrets, tokens, private key PEMs, and credentials from log messages."""
    redacted = message
    for pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class SensitiveDataRedactionFilter(logging.Filter):
    """Logging filter that strips sensitive material from log records before emission."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        else:
            record.msg = redact_sensitive_text(str(record.msg))
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_text(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: redact_sensitive_text(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
        return True


def get_security_logger(name: str = "cryptotrace.security") -> logging.Logger:
    """Return a configured security logger with mandatory sensitive-data redaction."""
    sec_logger = logging.getLogger(name)
    if not any(isinstance(f, SensitiveDataRedactionFilter) for f in sec_logger.filters):
        sec_logger.addFilter(SensitiveDataRedactionFilter())
    if not sec_logger.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(SensitiveDataRedactionFilter())
        formatter = logging.Formatter(
            fmt="%(asctime)sZ | %(levelname)s | %(name)s | %(message)s",
        )
        handler.setFormatter(formatter)
        sec_logger.addHandler(handler)
        sec_logger.setLevel(logging.INFO)
        sec_logger.propagate = False
    return sec_logger

