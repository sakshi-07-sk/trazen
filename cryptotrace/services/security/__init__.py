"""Role 3 Security Services package."""

from cryptotrace.services.security.address_poisoning import AddressPoisoningDetector
from cryptotrace.services.security.address_similarity import (
    AddressSimilarityAnalyzer,
    inspect_text_confusables,
    normalize_chain_name,
    validate_and_normalize_address,
)
from cryptotrace.services.security.blockchain_validator import (
    BlockchainDataValidator,
    BlockchainValidationReport,
)
from cryptotrace.services.security.dusting_detector import DustingDetector
from cryptotrace.services.security.graph_integrity import (
    GraphIntegrityAnalyzer,
    GraphIntegritySummary,
)
from cryptotrace.services.security.security_guardrails import TraceAISecurityGuardrails
from cryptotrace.services.security.token_impersonation import TokenImpersonationDetector

__all__ = [
    "AddressPoisoningDetector",
    "AddressSimilarityAnalyzer",
    "BlockchainDataValidator",
    "BlockchainValidationReport",
    "DustingDetector",
    "GraphIntegrityAnalyzer",
    "GraphIntegritySummary",
    "TokenImpersonationDetector",
    "TraceAISecurityGuardrails",
    "inspect_text_confusables",
    "normalize_chain_name",
    "validate_and_normalize_address",
]
