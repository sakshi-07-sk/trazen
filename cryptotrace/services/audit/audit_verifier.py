"""Deterministic async forensic audit chain verification and tamper-localization engine."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cryptotrace.db.models.audit import AuditEventModel
from cryptotrace.schemas.audit import (
    AuditEventRecord,
    AuditExportManifest,
    AuditVerificationReport,
)
from cryptotrace.services.audit.audit_hasher import (
    HASH_ALGORITHM,
    HASH_CONSTRUCTION_VERSION,
    SERIALIZATION_VERSION,
    canonicalize_json,
    compute_event_hash,
    compute_genesis_hash,
    compute_payload_hash,
)
from cryptotrace.services.audit.audit_service import model_to_record


class AuditVerifier:
    """Verifies SHA-256 hash-chained audit records and pinpoints tampering or omissions."""

    def __init__(
        self,
        db: AsyncSession | async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        if isinstance(db, AsyncSession):
            self._session: AsyncSession | None = db
            self._session_factory: async_sessionmaker[AsyncSession] | None = None
        else:
            self._session = None
            self._session_factory = db

    async def verify_investigation(
        self,
        investigation_id: str,
        *,
        expected_event_count: int | None = None,
        expected_head_hash: str | None = None,
    ) -> AuditVerificationReport:
        """Load stored events for investigation_id and run full cryptographic verification."""
        if self._session is None and self._session_factory is None:
            raise RuntimeError("AuditVerifier requires an AsyncSession or async_sessionmaker for DB verification.")

        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.investigation_id == investigation_id)
            .order_by(AuditEventModel.id.asc())
        )
        if self._session is not None:
            rows = (await self._session.execute(stmt)).scalars().all()
        else:
            assert self._session_factory is not None
            async with self._session_factory() as session:
                rows = (await session.execute(stmt)).scalars().all()

        events = [model_to_record(r) for r in rows]
        return self.verify_events(
            investigation_id=investigation_id,
            events=events,
            expected_event_count=expected_event_count,
            expected_head_hash=expected_head_hash,
        )

    def verify_manifest(
        self,
        manifest: AuditExportManifest,
        *,
        expected_event_count: int | None = None,
        expected_head_hash: str | None = None,
    ) -> AuditVerificationReport:
        """Verify an exported AuditExportManifest independently of the live database."""
        return self.verify_events(
            investigation_id=manifest.investigation_id,
            events=manifest.events,
            expected_event_count=expected_event_count
            if expected_event_count is not None
            else manifest.total_events,
            expected_head_hash=expected_head_hash or manifest.head_hash,
        )

    def verify_events(
        self,
        investigation_id: str,
        events: list[AuditEventRecord],
        *,
        expected_event_count: int | None = None,
        expected_head_hash: str | None = None,
    ) -> AuditVerificationReport:
        """Deterministically verify sequence continuity, payload digests, and SHA-256 chaining."""
        total = len(events)
        genesis_hash = compute_genesis_hash(investigation_id)

        if total == 0:
            if expected_event_count is not None and expected_event_count > 0:
                return AuditVerificationReport(
                    investigation_id=investigation_id,
                    status="TAMPERED",
                    is_valid=False,
                    total_events_checked=0,
                    verified_events=0,
                    failed_events=expected_event_count,
                    first_broken_sequence_number=1,
                    failure_reason=(
                        f"TAIL_OR_FULL_CHAIN_MISSING: expected {expected_event_count} events, found 0"
                    ),
                    expected_previous_hash=genesis_hash,
                    actual_previous_hash=None,
                    expected_event_hash=expected_head_hash,
                    actual_event_hash=None,
                )
            return AuditVerificationReport(
                investigation_id=investigation_id,
                status="EMPTY",
                is_valid=True,
                total_events_checked=0,
                verified_events=0,
                failed_events=0,
            )

        expected_seq = 1
        expected_prev_hash = genesis_hash
        verified_count = 0
        failed_count = 0

        first_broken_seq: int | None = None
        first_reason: str | None = None
        first_exp_prev: str | None = None
        first_act_prev: str | None = None
        first_exp_hash: str | None = None
        first_act_hash: str | None = None

        def _record_failure(
            seq: int,
            reason: str,
            exp_prev: str | None,
            act_prev: str | None,
            exp_hash: str | None,
            act_hash: str | None,
        ) -> None:
            nonlocal failed_count, first_broken_seq, first_reason
            nonlocal first_exp_prev, first_act_prev, first_exp_hash, first_act_hash
            failed_count += 1
            if first_broken_seq is None:
                first_broken_seq = seq
                first_reason = reason
                first_exp_prev = exp_prev
                first_act_prev = act_prev
                first_exp_hash = exp_hash
                first_act_hash = act_hash

        for event in events:
            event_failed = False

            # 1. Verify investigation isolation
            if event.investigation_id != investigation_id:
                _record_failure(
                    event.sequence_number,
                    f"INVESTIGATION_ID_MISMATCH: expected '{investigation_id}', got '{event.investigation_id}'",
                    expected_prev_hash,
                    event.previous_event_hash,
                    None,
                    event.current_event_hash,
                )
                event_failed = True

            # 2. Verify monotonic sequence numbering (detects deletion, gaps, reordering)
            if not event_failed and event.sequence_number != expected_seq:
                if event.sequence_number > expected_seq:
                    reason = (
                        f"MISSING_OR_DELETED_EVENT: expected sequence {expected_seq}, "
                        f"found {event.sequence_number}"
                    )
                else:
                    reason = (
                        f"REORDERED_OR_DUPLICATE_SEQUENCE: expected sequence {expected_seq}, "
                        f"found {event.sequence_number}"
                    )
                _record_failure(
                    expected_seq,
                    reason,
                    expected_prev_hash,
                    event.previous_event_hash,
                    None,
                    event.current_event_hash,
                )
                event_failed = True

            # 3. Verify previous hash linkage (detects genesis spoofing, deletion, reordering)
            if not event_failed and event.previous_event_hash != expected_prev_hash:
                reason = (
                    "GENESIS_HASH_MISMATCH"
                    if expected_seq == 1
                    else "CHAIN_LINK_BREAK_OR_REORDERED_EVENT"
                )
                _record_failure(
                    event.sequence_number,
                    reason,
                    expected_prev_hash,
                    event.previous_event_hash,
                    None,
                    event.current_event_hash,
                )
                event_failed = True

            # 4. Verify payload canonical JSON and SHA-256 payload digest
            recomputed_payload_hash: str | None = None
            try:
                parsed_json = json.loads(event.canonical_payload_json)
                recanonicalized = canonicalize_json(parsed_json)
                if recanonicalized != event.canonical_payload_json and not event_failed:
                    _record_failure(
                        event.sequence_number,
                        "NON_CANONICAL_PAYLOAD_TAMPERED",
                        expected_prev_hash,
                        event.previous_event_hash,
                        None,
                        event.current_event_hash,
                    )
                    event_failed = True
                recomputed_payload_hash = compute_payload_hash(event.canonical_payload_json)
                if recomputed_payload_hash != event.payload_hash and not event_failed:
                    _record_failure(
                        event.sequence_number,
                        "PAYLOAD_HASH_MISMATCH",
                        expected_prev_hash,
                        event.previous_event_hash,
                        recomputed_payload_hash,
                        event.payload_hash,
                    )
                    event_failed = True
            except (json.JSONDecodeError, ValueError):
                if not event_failed:
                    _record_failure(
                        event.sequence_number,
                        "CORRUPTED_PAYLOAD_JSON",
                        expected_prev_hash,
                        event.previous_event_hash,
                        None,
                        event.current_event_hash,
                    )
                    event_failed = True

            # 5. Verify full envelope hash (detects timestamp, actor, event_type, seq, metadata edits)
            recomputed_event_hash = compute_event_hash(
                event_id=event.event_id,
                sequence_number=event.sequence_number,
                investigation_id=event.investigation_id,
                actor=event.actor,
                actor_role=event.actor_role,
                event_type=event.event_type,
                timestamp=event.timestamp,
                payload_hash=event.payload_hash,
                previous_event_hash=event.previous_event_hash,
                hash_algorithm=event.hash_algorithm or HASH_ALGORITHM,
                serialization_version=event.serialization_version or SERIALIZATION_VERSION,
                hash_construction_version=event.hash_construction_version
                or HASH_CONSTRUCTION_VERSION,
            )
            if recomputed_event_hash != event.current_event_hash and not event_failed:
                _record_failure(
                    event.sequence_number,
                    "EVENT_HASH_MISMATCH",
                    expected_prev_hash,
                    event.previous_event_hash,
                    recomputed_event_hash,
                    event.current_event_hash,
                )
                event_failed = True

            if not event_failed:
                verified_count += 1

            expected_seq = event.sequence_number + 1
            expected_prev_hash = event.current_event_hash

        # 6. Optional tail-truncation & expected-head checks against external anchor/checkpoint
        tail_hash = events[0].current_event_hash
        head_hash = events[-1].current_event_hash

        if expected_event_count is not None and total < expected_event_count:
            _record_failure(
                total + 1,
                f"TAIL_TRUNCATION_DETECTED: expected {expected_event_count} events, found {total}",
                head_hash,
                None,
                expected_head_hash,
                head_hash,
            )
        elif expected_head_hash is not None and head_hash != expected_head_hash:
            _record_failure(
                events[-1].sequence_number,
                "HEAD_HASH_MISMATCH",
                events[-1].previous_event_hash,
                events[-1].previous_event_hash,
                expected_head_hash,
                head_hash,
            )

        is_valid = failed_count == 0
        return AuditVerificationReport(
            investigation_id=investigation_id,
            status="VERIFIED" if is_valid else "TAMPERED",
            is_valid=is_valid,
            total_events_checked=total,
            verified_events=verified_count,
            failed_events=failed_count,
            first_broken_sequence_number=first_broken_seq,
            failure_reason=first_reason,
            expected_previous_hash=first_exp_prev,
            actual_previous_hash=first_act_prev,
            expected_event_hash=first_exp_hash,
            actual_event_hash=first_act_hash,
            head_hash=head_hash,
            tail_hash=tail_hash,
        )
