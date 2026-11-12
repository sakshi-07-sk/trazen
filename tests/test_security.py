"""Security, auth, payload size, and LRU store tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from forensics.api.app import create_app
from forensics.api.store import CaseConflictError, InMemoryInvestigationStore
from forensics.schemas.input import InvestigationCase


def test_forensics_api_key_required_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEYS", "secret-key-1,secret-key-2")
    client = TestClient(create_app())

    unauth = client.get("/api/v1/investigations/CASE-PEEL-ETH-01/findings")
    assert unauth.status_code == 401

    bad = client.get(
        "/api/v1/investigations/CASE-PEEL-ETH-01/findings",
        headers={"X-API-Key": "wrong-key"},
    )
    assert bad.status_code == 401

    ok = client.get(
        "/api/v1/investigations/CASE-PEEL-ETH-01/findings",
        headers={"X-API-Key": "secret-key-2"},
    )
    assert ok.status_code == 200


def test_forensics_oversized_body_returns_413() -> None:
    client = TestClient(create_app())
    oversized = b'{"case_ids": [], "cases": [], "pad": "' + (b"x" * (2 * 1024 * 1024 + 100)) + b'"}'
    resp = client.post(
        "/api/v1/forensics/cross-case",
        content=oversized,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 413


def test_forensics_invalid_payload_returns_422() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/api/v1/investigations/CASE-BAD/analyze",
        json={"invalid": "payload"},
    )
    assert resp.status_code == 422


def test_store_lru_eviction_and_conflict() -> None:
    store = InMemoryInvestigationStore(preload_demo_cases=False, max_entries=500)
    for i in range(1, 502):
        store.save_case(
            InvestigationCase(investigation_id=f"CASE-{i:04d}", title=f"Case {i}", chain="ethereum")
        )
    assert store.get_case("CASE-0001") is None
    assert store.get_case("CASE-0501") is not None

    with pytest.raises(CaseConflictError):
        store.save_case(
            InvestigationCase(investigation_id="CASE-0501", title="Modified Title", chain="ethereum")
        )


@pytest.mark.asyncio
async def test_cryptotrace_api_key_and_422(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_KEYS", "ct-key-123")

    health = await async_client.get("/health")
    assert health.status_code == 200

    unauth = await async_client.post(
        "/api/v1/investigations",
        json={
            "title": "Test Case",
            "blockchain": "ethereum",
            "target_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        },
    )
    assert unauth.status_code == 401

    bad_payload = await async_client.post(
        "/api/v1/investigations",
        json={"title": "x"},
        headers={"X-API-Key": "ct-key-123"},
    )
    assert bad_payload.status_code == 422
