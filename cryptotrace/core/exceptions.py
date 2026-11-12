"""CryptoTrace Core Domain and Integration Exceptions."""

from typing import Any, Dict, Optional


class CryptoTraceException(Exception):
    """Base exception for all CryptoTrace errors."""

    def __init__(
        self,
        message: str,
        code: str = "CRYPTOTRACE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code


class InvalidAddressError(CryptoTraceException):
    """Raised when a cryptocurrency address format is invalid."""

    def __init__(self, address: str, chain: str) -> None:
        super().__init__(
            message=f"Invalid {chain} address format: '{address}'",
            code="INVALID_ADDRESS",
            details={"address": address, "chain": chain},
            status_code=400,
        )


class InvalidHashError(CryptoTraceException):
    """Raised when a transaction hash format is invalid."""

    def __init__(self, tx_hash: str, chain: str) -> None:
        super().__init__(
            message=f"Invalid {chain} transaction hash: '{tx_hash}'",
            code="INVALID_TRANSACTION_HASH",
            details={"tx_hash": tx_hash, "chain": chain},
            status_code=400,
        )


class ProviderError(CryptoTraceException):
    """Base exception for external blockchain provider issues."""

    def __init__(
        self,
        provider: str,
        message: str,
        code: str = "PROVIDER_ERROR",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged = {"provider": provider}
        if details:
            merged.update(details)
        super().__init__(message=message, code=code, details=merged, status_code=status_code)


class ProviderTimeoutError(ProviderError):
    """Raised when an external blockchain provider request times out."""

    def __init__(self, provider: str, timeout_seconds: float) -> None:
        super().__init__(
            provider=provider,
            message=f"Blockchain provider '{provider}' timed out after {timeout_seconds}s",
            code="PROVIDER_TIMEOUT",
            status_code=504,
            details={"timeout_seconds": timeout_seconds},
        )


class RateLimitError(ProviderError):
    """Raised when an upstream provider throttles requests."""

    def __init__(self, provider: str, retry_after: Optional[float] = None) -> None:
        super().__init__(
            provider=provider,
            message=f"Provider '{provider}' rate limit exceeded. Retry after {retry_after}s",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )


class DuplicateTransactionError(CryptoTraceException):
    """Raised when duplicate transactions are detected in an ingestion cycle."""

    def __init__(self, tx_hash: str, chain: str) -> None:
        super().__init__(
            message=f"Duplicate transaction '{tx_hash}' on {chain}",
            code="DUPLICATE_TRANSACTION",
            details={"tx_hash": tx_hash, "chain": chain},
            status_code=409,
        )


class InvestigationNotFoundError(CryptoTraceException):
    """Raised when an investigation record cannot be found."""

    def __init__(self, investigation_id: str) -> None:
        super().__init__(
            message=f"Investigation '{investigation_id}' not found",
            code="INVESTIGATION_NOT_FOUND",
            details={"investigation_id": investigation_id},
            status_code=404,
        )


class GraphTraversalError(CryptoTraceException):
    """Raised when graph construction or traversal fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            code="GRAPH_TRAVERSAL_ERROR",
            details=details,
            status_code=400,
        )


class DataNormalizationError(CryptoTraceException):
    """Raised when raw blockchain data cannot be normalized into canonical form."""

    def __init__(self, message: str, raw_payload: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            code="DATA_NORMALIZATION_ERROR",
            details={"payload_snippet": str(raw_payload)[:200] if raw_payload else None},
            status_code=422,
        )
