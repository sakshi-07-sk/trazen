"""Tests for FastAPI Endpoints and API Contracts."""

import pytest
from httpx import AsyncClient
from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_ADDRESS_1
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_ADDRESS_1


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["version"] == "0.1.0"
    assert "database_connected" in data


@pytest.mark.asyncio
async def test_create_and_query_investigation_lifecycle(async_client: AsyncClient):
    # 1. POST /api/v1/investigations
    create_payload = {
        "title": "CryptoTrace Ingestion Case #1",
        "description": "Multi-hop trace of Ethereum Seed EOA",
        "blockchain": "ethereum",
        "target_address": ETH_SAMPLE_ADDRESS_1,
        "max_hops": 2,
    }
    create_resp = await async_client.post("/api/v1/investigations", json=create_payload)
    assert create_resp.status_code == 201
    inv_data = create_resp.json()
    assert "id" in inv_data
    inv_id = inv_data["id"]
    assert inv_data["status"] == "completed"
    assert inv_data["blockchain"] == "ethereum"
    assert inv_data["target_address"] == ETH_SAMPLE_ADDRESS_1

    # 2. GET /api/v1/investigations/{id}
    get_resp = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inv_id

    # 3. GET /api/v1/investigations/{id}/graph
    graph_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/graph")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert graph_data["node_count"] > 0
    assert graph_data["edge_count"] > 0

    # 4. GET /api/v1/investigations/{id}/transactions
    tx_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/transactions?page=1&page_size=20")
    assert tx_resp.status_code == 200
    tx_page = tx_resp.json()
    assert "items" in tx_page
    assert "total" in tx_page
    assert "page" in tx_page
    assert tx_page["page"] == 1

    # 5. POST /api/v1/investigations/{id}/analyze
    analyze_payload = {
        "max_hops": 2,
        "include_heuristics": True,
    }
    analyze_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/analyze", json=analyze_payload)
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.json()
    assert analyze_data["investigation_id"] == inv_id
    assert "flow_analysis" in analyze_data
    assert "overall_metrics" in analyze_data["flow_analysis"]


@pytest.mark.asyncio
async def test_investigation_not_found(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/investigations/nonexistent-case-id")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "INVESTIGATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_payload_validation(async_client: AsyncClient):
    # Missing target_address and title
    resp = await async_client.post("/api/v1/investigations", json={"blockchain": "bitcoin"})
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_bitcoin_investigation_and_wallet_upsert(async_client: AsyncClient):
    # Test Bitcoin investigation lifecycle and idempotence/upsert of wallets
    payload = {
        "title": "CryptoTrace Ingestion Case #2 (BTC)",
        "description": "Multi-hop trace of Bitcoin UTXO seed",
        "blockchain": "bitcoin",
        "target_address": BTC_SAMPLE_ADDRESS_1,
        "max_hops": 2,
    }
    resp = await async_client.post("/api/v1/investigations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["blockchain"] == "bitcoin"
    assert data["status"] == "completed"

    # Ingesting same address again checks wallet upsert without integrity crash
    resp2 = await async_client.post("/api/v1/investigations", json=payload)
    assert resp2.status_code == 201
    assert resp2.json()["status"] == "completed"

