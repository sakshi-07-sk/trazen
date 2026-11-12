"""Append-only, async concurrency-safe SHA-256 hash-chained audit service."""

from __future__ import annotations

import asyncio
import json
import threading
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cryptotrace.db.models.audit import AuditEventModel
from cryptotrace.schemas.audit import AuditEventCreate, AuditEventRecord
from cryptotrace.services.audit.audit_hasher import (
    HASH_ALGORITHM,
    HASH_CONSTRUCTION_VERSION,
    SERIALIZATION_VERSION,
    canonicalize_json,
    compute_event_hash,
    compute_genesis_hash,
    compute_payload_hash,
    sanitize_audit_payload,
)


class _AsyncInvestigationLockRegistry:
    """Per-investigation lock registry keyed by (event_loop_id, investigation_id)."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[tuple[int, str], asyncio.Lock] = {}

    def get(self, investigation_id: str) -> asyncio.Lock:
        loop_id = id(asyncio.get_running_loop())
        key = (loop_id, investigation_id)
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock


_LOCK_REGISTRY = _AsyncInvestigationLockRegistry()


def model_to_record(row: AuditEventModel) -> AuditEventRecord:
    """Convert SQLAlchemy AuditEventModel row to Pydantic AuditEventRecord."""
    try:
        parsed_payload = json.loads(row.canonical_payload_json)
        if not isinstance(parsed_payload, dict):
            parsed_payload = {"value": parsed_payload}
    except json.JSONDecodeError:
        parsed_payload = {"_raw_corrupted_json": row.canonical_payload_json}

    return AuditEventRecord(
        event_id=row.event_id,
        sequence_number=row.sequence_number,
        investigation_id=row.investigation_id,
        actor=row.actor,
        actor_role=row.actor_role,
        event_type=row.event_type,
        canonical_payload=parsed_payload,
        canonical_payload_json=row.canonical_payload_json,
        payload_hash=row.payload_hash,
        timestamp=row.timestamp,
        previous_event_hash=row.previous_event_hash,
        current_event_hash=row.current_event_hash,
        hash_algorithm=row.hash_algorithm,
        serialization_version=row.serialization_version,
        hash_construction_version=row.hash_construction_version,
    )


class AuditService:
    """Async append-only forensic audit trail manager using SQLAlchemy 2.0 and SHA-256 chaining."""

    def __init__(
        self,
        db: AsyncSession | async_sessionmaker[AsyncSession],
    ) -> None:
        if isinstance(db, AsyncSession):
            self._session: AsyncSession | None = db
            self._session_factory: async_sessionmaker[AsyncSession] | None = None
        else:
            self._session = None
            self._session_factory = db

    async def _append_in_session(
        self,
        session: AsyncSession,
        *,
        investigation_id: str,
        actor: str,
        actor_role: str,
        event_type: str,
        canonical_payload_json: str,
        payload_hash: str,
    ) -> AuditEventModel:
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else ""

        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.investigation_id == investigation_id)
            .order_by(AuditEventModel.sequence_number.desc(), AuditEventModel.id.desc())
            .limit(1)
        )
        if dialect != "sqlite":
            stmt = stmt.with_for_update()

        latest = (await session.execute(stmt)).scalar_one_or_none()
        if latest is None:
            next_seq = 1
            prev_hash = compute_genesis_hash(investigation_id)
        else:
            next_seq = latest.sequence_number + 1
            prev_hash = latest.current_event_hash

        event_id = str(uuid4())
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        current_hash = compute_event_hash(
            event_id=event_id,
            sequence_number=next_seq,
            investigation_id=investigation_id,
            actor=actor,
            actor_role=actor_role,
            event_type=event_type,
            timestamp=timestamp,
            payload_hash=payload_hash,
            previous_event_hash=prev_hash,
            hash_algorithm=HASH_ALGORITHM,
            serialization_version=SERIALIZATION_VERSION,
            hash_construction_version=HASH_CONSTRUCTION_VERSION,
        )

        row = AuditEventModel(
            event_id=event_id,
            sequence_number=next_seq,
            investigation_id=investigation_id,
            actor=actor,
            actor_role=actor_role,
            event_type=event_type,
            canonical_payload_json=canonical_payload_json,
            payload_hash=payload_hash,
            timestamp=timestamp,
            previous_event_hash=prev_hash,
            current_event_hash=current_hash,
            hash_algorithm=HASH_ALGORITHM,
            serialization_version=SERIALIZATION_VERSION,
            hash_construction_version=HASH_CONSTRUCTION_VERSION,
        )
        session.add(row)
        await session.flush()
        return row

    async def record_event(
        self,
        event_in: AuditEventCreate,
        *,
        actor_override: str | None = None,
        actor_role_override: str | None = None,
        max_retries: int = 12,
    ) -> AuditEventRecord:
        """Append a single tamper-evident event to an investigation's hash chain."""
        investigation_id = event_in.investigation_id.strip()
        actor = (actor_override or event_in.actor or "system").strip() or "system"
        actor_role = (actor_role_override or event_in.actor_role or "system").strip() or "system"
        event_type = event_in.event_type.strip()

        sanitized_payload = sanitize_audit_payload(event_in.payload)
        canonical_payload_json = canonicalize_json(sanitized_payload)
        payload_hash = compute_payload_hash(canonical_payload_json)

        inv_lock = _LOCK_REGISTRY.get(investigation_id)
        async with inv_lock:
            last_error: Exception | None = None

            if self._session is not None:
                # Shared request/unit-of-work AsyncSession: use SAVEPOINT retries so outer work is never rolled back.
                for attempt in range(max_retries):
                    try:
                        async with self._session.begin_nested():
                            row = await self._append_in_session(
                                self._session,
                                investigation_id=investigation_id,
                                actor=actor,
                                actor_role=actor_role,
                                event_type=event_type,
                                canonical_payload_json=canonical_payload_json,
                                payload_hash=payload_hash,
                            )
                        return model_to_record(row)
                    except (IntegrityError, OperationalError) as exc:
                        last_error = exc
                        await asyncio.sleep(0.01 * (attempt + 1))

                raise RuntimeError(
                    f"Failed to append audit event for '{investigation_id}' after {max_retries} savepoint retries"
                ) from last_error

            assert self._session_factory is not None
            for attempt in range(max_retries):
                async with self._session_factory() as session:
                    try:
                        row = await self._append_in_session(
                            session,
                            investigation_id=investigation_id,
                            actor=actor,
                            actor_role=actor_role,
                            event_type=event_type,
                            canonical_payload_json=canonical_payload_json,
                            payload_hash=payload_hash,
                        )
                        await session.commit()
                        await session.refresh(row)
                        return model_to_record(row)
                    except (IntegrityError, OperationalError) as exc:
                        await session.rollback()
                        last_error = exc
                        await asyncio.sleep(0.01 * (attempt + 1))
                    except Exception:
                        await session.rollback()
                        raise

            raise RuntimeError(
                f"Failed to append audit event for '{investigation_id}' after {max_retries} retries"
            ) from last_error

    async def list_events(
        self,
        investigation_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> list[AuditEventRecord]:
        """Retrieve ordered audit events for a single investigation."""
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.investigation_id == investigation_id)
            .order_by(AuditEventModel.id.asc())
            .offset(offset)
            .limit(limit)
        )
        if self._session is not None:
            rows = (await self._session.execute(stmt)).scalars().all()
            return [model_to_record(row) for row in rows]

        assert self._session_factory is not None
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [model_to_record(row) for row in rows]

    async def get_all_events_ordered_by_insertion(
        self, investigation_id: str
    ) -> list[AuditEventRecord]:
        """Retrieve complete event list ordered by physical insertion ID for integrity verification."""
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.investigation_id == investigation_id)
            .order_by(AuditEventModel.id.asc())
        )
        if self._session is not None:
            rows = (await self._session.execute(stmt)).scalars().all()
            return [model_to_record(row) for row in rows]

        assert self._session_factory is not None
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [model_to_record(row) for row in rows]
