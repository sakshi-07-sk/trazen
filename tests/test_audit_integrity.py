"""Async unit & tamper-simulation tests for SHA-256 hash-chained forensic audit integrity."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cryptotrace.db.models.audit import AuditEventModel
from cryptotrace.schemas.audit import AuditEventCreate
from cryptotrace.services.audit.audit_export import AuditExportService
from cryptotrace.services.audit.audit_hasher import canonicalize_json
from cryptotrace.services.audit.audit_service import AuditService
from cryptotrace.services.audit.audit_verifier import AuditVerifier


@pytest.mark.unit
@pytest.mark.asyncio
async def test_canonical_json_is_deterministic_and_redacts_secrets(
    test_db_session: AsyncSession,
) -> None:
    assert canonicalize_json({"b": 1, "a": {"y": 2, "x": 3}}) == '{"a":{"x":3,"y":2},"b":1}'

    svc = AuditService(test_db_session)
    ev = await svc.record_event(
        AuditEventCreate(
            investigation_id="inv-aud-1",
            event_type="TEST_EVENT",
            payload={"detail": "ok", "private_key": "0xdeadbeef", "seed_phrase": "word1 word2"},
        ),
        actor_override="tester",
        actor_role_override="investigator",
    )
    await test_db_session.commit()
    assert ev.canonical_payload["private_key"] == "[REDACTED]"
    assert ev.canonical_payload["seed_phrase"] == "[REDACTED]"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detects_altered_deleted_reordered_and_broken_chain_audit_events(
    test_async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    svc = AuditService(test_async_session_factory)
    verifier = AuditVerifier(test_async_session_factory)

    inv = "inv-tamper-1"
    for idx in range(1, 5):
        await svc.record_event(
            AuditEventCreate(
                investigation_id=inv,
                event_type="STEP",
                payload={"step": idx},
            ),
            actor_override="analyst-1",
            actor_role_override="investigator",
        )

    clean = await verifier.verify_investigation(inv)
    assert clean.is_valid
    assert clean.status == "VERIFIED"
    assert clean.verified_events == 4

    # 1. Alter event 2 payload directly in DB -> detected at seq 2
    async with test_async_session_factory() as session:
        await session.execute(
            update(AuditEventModel)
            .where(AuditEventModel.investigation_id == inv, AuditEventModel.sequence_number == 2)
            .values(canonical_payload_json='{"step":999}')
        )
        await session.commit()

    tampered_payload = await verifier.verify_investigation(inv)
    assert not tampered_payload.is_valid
    assert tampered_payload.status == "TAMPERED"
    assert tampered_payload.first_broken_sequence_number == 2

    # 2. Delete middle event on a fresh investigation -> detected via gap + chain break
    inv_del = "inv-tamper-del"
    for idx in range(1, 4):
        await svc.record_event(
            AuditEventCreate(investigation_id=inv_del, event_type="STEP", payload={"step": idx})
        )
    async with test_async_session_factory() as session:
        await session.execute(
            delete(AuditEventModel).where(
                AuditEventModel.investigation_id == inv_del,
                AuditEventModel.sequence_number == 2,
            )
        )
        await session.commit()

    deleted_report = await verifier.verify_investigation(inv_del)
    assert not deleted_report.is_valid
    assert deleted_report.first_broken_sequence_number == 2
    assert "MISSING_OR_DELETED_EVENT" in (deleted_report.failure_reason or "")

    # 3. Reorder events (swap seq numbers 2 and 3 in fresh chain) -> detected
    inv_reord = "inv-tamper-reord"
    for idx in range(1, 4):
        await svc.record_event(
            AuditEventCreate(investigation_id=inv_reord, event_type="STEP", payload={"step": idx})
        )
    async with test_async_session_factory() as session:
        await session.execute(
            update(AuditEventModel)
            .where(
                AuditEventModel.investigation_id == inv_reord, AuditEventModel.sequence_number == 2
            )
            .values(sequence_number=99)
        )
        await session.execute(
            update(AuditEventModel)
            .where(
                AuditEventModel.investigation_id == inv_reord, AuditEventModel.sequence_number == 3
            )
            .values(sequence_number=2)
        )
        await session.execute(
            update(AuditEventModel)
            .where(
                AuditEventModel.investigation_id == inv_reord, AuditEventModel.sequence_number == 99
            )
            .values(sequence_number=3)
        )
        await session.commit()

    reord_report = await verifier.verify_investigation(inv_reord)
    assert not reord_report.is_valid
    assert reord_report.status == "TAMPERED"

    # 4. Tail truncation caught when expected_event_count checkpoint is supplied
    inv_tail = "inv-tamper-tail"
    for idx in range(1, 4):
        await svc.record_event(
            AuditEventCreate(investigation_id=inv_tail, event_type="STEP", payload={"step": idx})
        )
    async with test_async_session_factory() as session:
        await session.execute(
            delete(AuditEventModel).where(
                AuditEventModel.investigation_id == inv_tail,
                AuditEventModel.sequence_number == 3,
            )
        )
        await session.commit()
    tail_report = await verifier.verify_investigation(inv_tail, expected_event_count=3)
    assert not tail_report.is_valid
    assert "TAIL_TRUNCATION_DETECTED" in (tail_report.failure_reason or "")

    # 5. Broken previous_event_hash link explicitly caught with expected vs actual hashes
    inv_link = "inv-tamper-link"
    for idx in range(1, 4):
        await svc.record_event(
            AuditEventCreate(investigation_id=inv_link, event_type="STEP", payload={"step": idx})
        )
    async with test_async_session_factory() as session:
        await session.execute(
            update(AuditEventModel)
            .where(
                AuditEventModel.investigation_id == inv_link, AuditEventModel.sequence_number == 2
            )
            .values(previous_event_hash="f" * 64)
        )
        await session.commit()
    link_report = await verifier.verify_investigation(inv_link)
    assert not link_report.is_valid
    assert link_report.first_broken_sequence_number == 2
    assert link_report.failure_reason == "CHAIN_LINK_BREAK_OR_REORDERED_EVENT"
    assert link_report.actual_previous_hash == "f" * 64


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_async_audit_insertion_maintains_unbroken_chain(
    test_async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    svc = AuditService(test_async_session_factory)
    verifier = AuditVerifier(test_async_session_factory)
    inv = "inv-concurrent-async-1"

    async def _worker(idx: int) -> int:
        rec = await svc.record_event(
            AuditEventCreate(
                investigation_id=inv,
                event_type="CONCURRENT_OP",
                payload={"worker": idx},
            ),
            actor_override=f"worker-{idx}",
        )
        return rec.sequence_number

    seqs = await asyncio.gather(*(_worker(i) for i in range(16)))

    assert sorted(seqs) == list(range(1, 17))
    report = await verifier.verify_investigation(inv)
    assert report.is_valid
    assert report.total_events_checked == 16
    assert report.verified_events == 16


@pytest.mark.unit
@pytest.mark.asyncio
async def test_audit_export_manifest_ed25519_signature_and_offline_verification(
    test_db_session: AsyncSession,
    ephemeral_ed25519_key_pem: str,
) -> None:
    svc = AuditService(test_db_session)
    verifier = AuditVerifier(test_db_session)
    exporter = AuditExportService(svc, verifier, signing_private_key_pem=ephemeral_ed25519_key_pem)

    inv = "inv-export-1"
    await svc.record_event(
        AuditEventCreate(investigation_id=inv, event_type="INIT", payload={"case": inv})
    )
    await svc.record_event(
        AuditEventCreate(investigation_id=inv, event_type="SCAN", payload={"alerts": 1})
    )
    await test_db_session.commit()

    manifest = await exporter.export_investigation(inv)
    assert manifest.verification_status == "VERIFIED"
    assert manifest.signature_algorithm == "Ed25519"
    assert AuditExportService.verify_manifest_signature(manifest)
    assert verifier.verify_manifest(manifest).is_valid

    manifest.events[0].canonical_payload["case"] = "forged"
    manifest.events[0].canonical_payload_json = '{"case":"forged"}'
    assert not AuditExportService.verify_manifest_signature(manifest)
    assert not verifier.verify_manifest(manifest).is_valid

