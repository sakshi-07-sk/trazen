"""Common enumerations and evidence primitives for Role 3 security services."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ChainId(StrEnum):
    """Supported canonical blockchain network identifiers."""

    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    AVALANCHE = "avalanche"
    BITCOIN = "bitcoin"
    SOLANA = "solana"
    TRON = "tron"


EVM_CHAINS: frozenset[str] = frozenset(
    {
        ChainId.ETHEREUM.value,
        ChainId.POLYGON.value,
        ChainId.BSC.value,
        ChainId.ARBITRUM.value,
        ChainId.OPTIMISM.value,
        ChainId.BASE.value,
        ChainId.AVALANCHE.value,
    }
)


class Severity(StrEnum):
    """Normalized forensic finding severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationStatus(StrEnum):
    """Explicit blockchain data validation outcomes."""

    VALID = "VALID"
    INVALID = "INVALID"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTING = "CONFLICTING"
    INCOMPLETE = "INCOMPLETE"


class IndependentVerificationStatus(StrEnum):
    """Status of independent multi-provider verification."""

    VERIFIED_AGREE = "VERIFIED_AGREE"
    VERIFIED_CONFLICT = "VERIFIED_CONFLICT"
    UNVERIFIED = "UNVERIFIED"
    NOT_INDEPENDENT = "NOT_INDEPENDENT"


class FindingCategory(StrEnum):
    """Role 3 security and integrity finding categories."""

    ADDRESS_POISONING = "ADDRESS_POISONING"
    LOOKALIKE_WALLET = "LOOKALIKE_WALLET"
    DUSTING_ATTACK = "DUSTING_ATTACK"
    GRAPH_POISONING = "GRAPH_POISONING"
    DECOY_EDGE = "DECOY_EDGE"
    TOKEN_IMPERSONATION = "TOKEN_IMPERSONATION"  # nosec B105  # noqa: S105
    BLOCKCHAIN_DATA_INTEGRITY = "BLOCKCHAIN_DATA_INTEGRITY"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    AUDIT_TAMPERING = "AUDIT_TAMPERING"
    API_SECURITY = "API_SECURITY"


class EpistemicLabel(StrEnum):
    """Explicit epistemic distinction required by Role 3 and TraceAI guardrails."""

    VERIFIED_FACT = "VERIFIED_FACT"
    UNVERIFIED_OBSERVATION = "UNVERIFIED_OBSERVATION"
    SUSPICIOUS_INDICATOR = "SUSPICIOUS_INDICATOR"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class EvidenceReference(BaseModel):
    """Traceable reference pointing to underlying evidence."""

    ref_type: Literal[
        "transaction",
        "address",
        "block",
        "token_contract",
        "graph_edge",
        "provider_response",
        "audit_event",
        "document",
    ]
    ref_id: str = Field(..., min_length=1, max_length=256)
    chain: str | None = Field(default=None, max_length=64)
    provider: str | None = Field(default=None, max_length=128)
    detail: str | None = Field(default=None, max_length=1000)

