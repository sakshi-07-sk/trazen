"""Exportable audit history manifest builder with optional Ed25519 digital signature."""

from __future__ import annotations

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from cryptotrace.schemas.audit import AuditExportManifest
from cryptotrace.services.audit.audit_hasher import (
    HASH_ALGORITHM,
    HASH_CONSTRUCTION_VERSION,
    SERIALIZATION_VERSION,
    canonicalize_json,
    compute_genesis_hash,
)
from cryptotrace.services.audit.audit_service import AuditService
from cryptotrace.services.audit.audit_verifier import AuditVerifier


def _manifest_signing_payload(manifest: AuditExportManifest) -> bytes:
    """Build deterministic signing bytes excluding the signature fields themselves."""
    payload = {
        "investigation_id": manifest.investigation_id,
        "exported_at": manifest.exported_at.isoformat(),
        "total_events": manifest.total_events,
        "genesis_hash": manifest.genesis_hash,
        "head_hash": manifest.head_hash,
        "tail_hash": manifest.tail_hash,
        "hash_algorithm": manifest.hash_algorithm,
        "serialization_version": manifest.serialization_version,
        "hash_construction_version": manifest.hash_construction_version,
        "verification_status": manifest.verification_status,
        "events": [ev.model_dump() for ev in manifest.events],
    }
    return canonicalize_json(payload).encode("utf-8")


class AuditExportService:
    """Exports self-contained, verifiable audit manifests with optional Ed25519 signing."""

    def __init__(
        self,
        audit_service: AuditService,
        audit_verifier: AuditVerifier,
        signing_private_key_pem: str | None = None,
    ) -> None:
        self.audit_service = audit_service
        self.audit_verifier = audit_verifier
        self._signing_private_key_pem = signing_private_key_pem

    async def export_investigation(self, investigation_id: str) -> AuditExportManifest:
        """Build and optionally sign an exportable forensic audit manifest."""
        events = await self.audit_service.get_all_events_ordered_by_insertion(investigation_id)
        report = self.audit_verifier.verify_events(investigation_id=investigation_id, events=events)

        manifest = AuditExportManifest(
            investigation_id=investigation_id,
            total_events=len(events),
            genesis_hash=compute_genesis_hash(investigation_id),
            head_hash=report.head_hash,
            tail_hash=report.tail_hash,
            hash_algorithm=HASH_ALGORITHM,
            serialization_version=SERIALIZATION_VERSION,
            hash_construction_version=HASH_CONSTRUCTION_VERSION,
            verification_status=report.status,
            events=events,
        )

        if self._signing_private_key_pem:
            key = serialization.load_pem_private_key(
                self._signing_private_key_pem.encode("utf-8"),
                password=None,
            )
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError("Audit export signing key must be an Ed25519 private key.")
            signature = key.sign(_manifest_signing_payload(manifest))
            pub_pem = (
                key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode("utf-8")
            )
            manifest.signature_algorithm = "Ed25519"
            manifest.signature_b64 = base64.b64encode(signature).decode("ascii")
            manifest.public_key_pem = pub_pem

        return manifest

    @staticmethod
    def verify_manifest_signature(
        manifest: AuditExportManifest,
        trusted_public_key_pem: str | None = None,
    ) -> bool:
        """Verify Ed25519 digital signature on an exported AuditExportManifest."""
        pem = trusted_public_key_pem or manifest.public_key_pem
        if not pem or not manifest.signature_b64 or manifest.signature_algorithm != "Ed25519":
            return False
        try:
            pub = serialization.load_pem_public_key(pem.encode("utf-8"))
            if not isinstance(pub, Ed25519PublicKey):
                return False
            sig = base64.b64decode(manifest.signature_b64.encode("ascii"), validate=True)
            pub.verify(sig, _manifest_signing_payload(manifest))
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False
