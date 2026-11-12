"""Structured logging setup for CryptoTrace."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from cryptotrace.core.logging_utils import SensitiveDataRedactionFilter


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for log aggregators (ELK, Datadog)."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_payload.update(record.extra)
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)


def setup_logging(debug: bool = False, json_output: bool = False) -> logging.Logger:
    """Initialize root logger configuration."""
    logger = logging.getLogger("cryptotrace")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveDataRedactionFilter())
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    if not any(isinstance(f, SensitiveDataRedactionFilter) for f in logger.filters):
        logger.addFilter(SensitiveDataRedactionFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()
