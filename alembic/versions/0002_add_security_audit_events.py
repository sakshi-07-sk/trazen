"""Add security_audit_events table for Role 3 tamper-evident forensic audit logging.

Revision ID: 0002_add_security_audit_events
Revises: 0001_initial_crypto_trace_schema
Create Date: 2026-11-12 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_security_audit_events"
down_revision: Union[str, None] = "0001_initial_crypto_trace_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "security_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.String(length=128), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("actor_role", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("canonical_payload_json", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.String(length=64), nullable=False),
        sa.Column("previous_event_hash", sa.String(length=64), nullable=False),
        sa.Column("current_event_hash", sa.String(length=64), nullable=False),
        sa.Column("hash_algorithm", sa.String(length=32), nullable=False),
        sa.Column("serialization_version", sa.String(length=64), nullable=False),
        sa.Column("hash_construction_version", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("event_id"),
        sa.UniqueConstraint("current_event_hash"),
        sa.UniqueConstraint("investigation_id", "sequence_number", name="uq_sec_audit_inv_seq"),
        sa.UniqueConstraint(
            "investigation_id", "previous_event_hash", name="uq_sec_audit_inv_prev_hash"
        ),
    )
    op.create_index("ix_security_audit_events_event_id", "security_audit_events", ["event_id"])
    op.create_index(
        "ix_security_audit_events_investigation_id",
        "security_audit_events",
        ["investigation_id"],
    )
    op.create_index("ix_security_audit_events_event_type", "security_audit_events", ["event_type"])
    op.create_index(
        "ix_sec_audit_inv_seq",
        "security_audit_events",
        ["investigation_id", "sequence_number"],
    )


def downgrade() -> None:
    op.drop_index("ix_sec_audit_inv_seq", table_name="security_audit_events")
    op.drop_index("ix_security_audit_events_event_type", table_name="security_audit_events")
    op.drop_index("ix_security_audit_events_investigation_id", table_name="security_audit_events")
    op.drop_index("ix_security_audit_events_event_id", table_name="security_audit_events")
    op.drop_table("security_audit_events")

