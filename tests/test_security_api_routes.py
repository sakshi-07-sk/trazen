"""Integration tests covering Role 3 FastAPI v1 routes & cross-role Role 1->Role 3 flows."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_ADDRESS_1
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_ADDRESS_1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_detection_and_guardrail_api_endpoints(
    security_async_client: AsyncClient,
    make_auth_headers,
) -> None:
    headers = make_auth_headers(allowed_investigations=["inv-001"])
    victim = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    legit = "0x1234567890abcdef1234567890abcdef1234abcd"
    poisoner = "0x123456999999999999999999999999999999abcd"
    now = datetime(2026, 10, 1, 12, 0, tzinfo=UTC).isoformat()
    later = datetime(2026, 10, 1, 12, 3, tzinfo=UTC).isoformat()

    # 1. Address poisoning API
    ap_resp = await security_async_client.post(
        "/api/v1/security/detect/address-poisoning",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "target_wallet": victim,
            "chain": "ethereum",
            "transactions": [
                {
                    "tx_hash": "0x" + "1" * 64,
                    "chain": "ethereum",
                    "timestamp": now,
                    "from_address": victim,
                    "to_address": legit,
                    "amount": "2.0",
                    "asset_symbol": "ETH",
                },
                {
                    "tx_hash": "0x" + "2" * 64,
                    "chain": "ethereum",
                    "timestamp": later,
                    "from_address": poisoner,
                    "to_address": victim,
                    "amount": "0",
                    "asset_symbol": "ETH",
                },
            ],
        },
    )
    assert ap_resp.status_code == 200
    assert ap_resp.json()["total_findings"] == 1
    assert len(ap_resp.json()["shared_findings"]) == 1

    # 2. Dusting API
    dust_resp = await security_async_client.post(
        "/api/v1/security/detect/dusting",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "transactions": [
                {
                    "tx_hash": f"0x{i:064x}",
                    "chain": "ethereum",
                    "timestamp": now,
                    "from_address": "0xdddddddddddddddddddddddddddddddddddddddd",
                    "to_address": f"0x{i + 100:040x}",
                    "amount": "0.00001",
                    "asset_symbol": "ETH",
                }
                for i in range(1, 7)
            ],
        },
    )
    assert dust_resp.status_code == 200
    assert dust_resp.json()["total_findings"] == 1

    # 3. Token impersonation API
    tok_resp = await security_async_client.post(
        "/api/v1/security/detect/token-impersonation",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "tokens": [
                {
                    "chain": "ethereum",
                    "contract_address": "0x8888888888888888888888888888888888888888",
                    "symbol": "USDC",
                    "name": "USD Coin",
                    "decimals": 18,
                }
            ],
        },
    )
    assert tok_resp.status_code == 200
    assert tok_resp.json()["total_findings"] >= 1

    # 4. Graph integrity API
    graph_resp = await security_async_client.post(
        "/api/v1/security/detect/graph-integrity",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "nodes": [
                {"node_id": victim, "chain": "ethereum"},
                {"node_id": legit, "chain": "ethereum"},
            ],
            "edges": [
                {
                    "edge_id": "e1",
                    "source": victim,
                    "target": legit,
                    "tx_hash": "0x" + "1" * 64,
                    "chain": "ethereum",
                    "block_number": 10,
                    "asset": "ETH",
                    "amount": "2.0",
                }
            ],
            "evidence_transactions": [
                {
                    "tx_hash": "0x" + "1" * 64,
                    "chain": "ethereum",
                    "block_number": 10,
                    "from_address": victim,
                    "to_address": legit,
                    "amount": "2.0",
                    "asset_symbol": "ETH",
                }
            ],
        },
    )
    assert graph_resp.status_code == 200
    assert graph_resp.json()["is_integrity_clean"] is True

    # 5. TraceAI tool gate & output validation APIs
    tool_resp = await security_async_client.post(
        "/api/v1/security/guardrails/traceai/validate-tool-call",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "tool_name": "delete_audit_log",
            "arguments": {"investigation_id": "inv-001"},
        },
    )
    assert tool_resp.status_code == 200
    assert tool_resp.json()["allowed"] is False

    out_resp = await security_async_client.post(
        "/api/v1/security/guardrails/traceai/validate-output",
        headers=headers,
        json={
            "investigation_id": "inv-001",
            "response_text": "Verified transfer in " + ("0x" + "1" * 64),
            "cited_evidence_refs": ["0x" + "1" * 64],
            "allowed_evidence_refs": ["0x" + "1" * 64],
            "epistemic_label": "VERIFIED_FACT",
        },
    )
    assert out_resp.status_code == 200
    assert out_resp.json()["approved"] is True

    # 6. Audit history reflects all 6 recorded actions cleanly in sequential order
    hist_resp = await security_async_client.get("/api/v1/security/audit/inv-001", headers=headers)
    assert hist_resp.status_code == 200
    assert hist_resp.json()["total_returned"] == 6
    seqs = [e["sequence_number"] for e in hist_resp.json()["events"]]
    assert seqs == [1, 2, 3, 4, 5, 6]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_role1_investigation_to_role3_security_scan_btc_and_eth(
    security_async_client: AsyncClient,
    make_auth_headers,
) -> None:
    """Verify Role 1 BTC & ETH investigations scan cleanly with zero false graph integrity errors."""
    for chain, addr in (("ethereum", ETH_SAMPLE_ADDRESS_1), ("bitcoin", BTC_SAMPLE_ADDRESS_1)):
        inv_resp = await security_async_client.post(
            "/api/v1/investigations",
            json={
                "title": f"Cross-role {chain} trace",
                "blockchain": chain,
                "target_address": addr,
                "max_hops": 2,
            },
        )
        assert inv_resp.status_code == 201
        inv_id = inv_resp.json()["id"]

        headers = make_auth_headers(allowed_investigations=[inv_id])
        scan_resp = await security_async_client.post(
            f"/api/v1/security/investigations/{inv_id}/scan",
            headers=headers,
        )
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()
        assert scan_data["graph_integrity"]["is_integrity_clean"] is True
        assert scan_data["graph_integrity"]["flagged_edge_count"] == 0

        # Audit chain for this investigation includes CREATED, COMPLETED, and SECURITY_SCAN
        verify_resp = await security_async_client.post(
            "/api/v1/security/audit/verify",
            headers=headers,
            json={"investigation_id": inv_id},
        )
        assert verify_resp.status_code == 200
        v_data = verify_resp.json()
        assert v_data["is_valid"] is True
        assert v_data["verified_events"] >= 3
