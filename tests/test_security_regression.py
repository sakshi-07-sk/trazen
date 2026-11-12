"""Regression tests verifying Role 1 compatibility, CORS, error contracts, and Role 3 hardening."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from cryptotrace.config import Settings
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_ADDRESS_1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_role1_routes_remain_unauthenticated_and_preserve_error_contracts(
    async_client: AsyncClient,
) -> None:
    # 1. Existing Role 1 endpoints work without Authorization header
    health = await async_client.get("/health")
    assert health.status_code == 200
    assert health.headers["x-content-type-options"] == "nosniff"
    assert "x-correlation-id" in health.headers

    # 2. 404 preserves Team's {"error": "INVESTIGATION_NOT_FOUND", "message": ..., "details": ...}
    not_found = await async_client.get("/api/v1/investigations/missing-id")
    assert not_found.status_code == 404
    nf_body = not_found.json()
    assert nf_body["error"] == "INVESTIGATION_NOT_FOUND"
    assert "message" in nf_body
    assert "details" in nf_body
    assert "correlation_id" in nf_body

    # 3. 422 preserves Team's {"error": "VALIDATION_ERROR", ...} without echoing raw input payloads
    invalid = await async_client.post(
        "/api/v1/investigations",
        json={"blockchain": "ethereum", "secret_probe": "should_not_echo"},
    )
    assert invalid.status_code == 422
    inv_body = invalid.json()
    assert inv_body["error"] == "VALIDATION_ERROR"
    assert "correlation_id" in inv_body
    assert "should_not_echo" not in invalid.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cors_allows_nextjs_localhost_and_rejects_wildcard(
    async_client: AsyncClient,
) -> None:
    # Explicit Next.js dev origin is allowed on preflight
    preflight = await async_client.options(
        "/api/v1/investigations",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Untrusted origin does not receive allow-origin header
    disallowed = await async_client.options(
        "/api/v1/investigations",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in disallowed.headers

    # Settings validator rejects wildcard "*"
    with pytest.raises(ValueError, match="Wildcard"):
        Settings(CORS_ALLOWED_ORIGINS=["*"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_role1_investigation_lifecycle_emits_verified_audit_chain(
    security_async_client: AsyncClient,
    make_auth_headers,
) -> None:
    create_resp = await security_async_client.post(
        "/api/v1/investigations",
        json={
            "title": "Regression Audit Lifecycle",
            "blockchain": "ethereum",
            "target_address": ETH_SAMPLE_ADDRESS_1,
            "max_hops": 1,
        },
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    analyze_resp = await security_async_client.post(
        f"/api/v1/investigations/{inv_id}/analyze",
        json={"max_hops": 1, "include_heuristics": False},
    )
    assert analyze_resp.status_code == 200

    headers = make_auth_headers(allowed_investigations=[inv_id])
    hist_resp = await security_async_client.get(
        f"/api/v1/security/audit/{inv_id}",
        headers=headers,
    )
    assert hist_resp.status_code == 200
    events = hist_resp.json()["events"]
    assert [e["event_type"] for e in events] == [
        "INVESTIGATION_CREATED",
        "INVESTIGATION_COMPLETED",
        "INVESTIGATION_ANALYZED",
    ]
    assert [e["sequence_number"] for e in events] == [1, 2, 3]

