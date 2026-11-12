"""Unit & negative tests for contract-first token impersonation detection."""

from __future__ import annotations

import pytest

from cryptotrace.schemas.security_common import FindingCategory
from cryptotrace.schemas.security_inputs import TokenMetadataInput
from cryptotrace.services.security.token_impersonation import TokenImpersonationDetector


@pytest.mark.unit
def test_detects_fake_symbol_homoglyph_and_metadata_mutation() -> None:
    detector = TokenImpersonationDetector()

    fake_token = TokenMetadataInput(
        chain="ethereum",
        contract_address="0x9999999999999999999999999999999999999999",
        symbol="USD\u0422",  # Cyrillic Т
        name="Tether USD",
        decimals=18,
        previous_symbol="TMP",
    )
    findings = detector.analyze("inv-tok-1", fake_token)
    assert len(findings) >= 3
    types = {f.finding_type for f in findings}
    assert "homoglyph_or_invisible_token_symbol" in types
    assert "suspicious_token_metadata_change" in types
    assert "suspected_token_impersonation" in types
    assert all(f.finding_category == FindingCategory.TOKEN_IMPERSONATION for f in findings)


@pytest.mark.unit
def test_canonical_and_unrelated_clean_tokens_do_not_trigger_impersonation() -> None:
    """Negative test: canonical USDC and distinct legitimate token must pass cleanly."""
    detector = TokenImpersonationDetector()

    canonical_usdc = TokenMetadataInput(
        chain="ethereum",
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        symbol="USDC",
        name="USD Coin",
        decimals=6,
    )
    legit_custom = TokenMetadataInput(
        chain="ethereum",
        contract_address="0x4444444444444444444444444444444444444444",
        symbol="KRYP",
        name="Krypton Governance Token",
        decimals=18,
    )

    assert detector.analyze("inv-tok-clean", canonical_usdc) == []
    assert detector.analyze("inv-tok-clean", legit_custom) == []
