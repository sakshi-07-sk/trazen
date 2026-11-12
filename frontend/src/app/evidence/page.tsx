"use client";

import React from "react";
import { SocShell } from "@/components/layout/SocShell";
import { useForensic } from "@/context/ForensicContext";
import { EvidenceVaultView } from "@/features/audit/EvidenceVaultView";

export default function EvidenceVaultPage() {
  const { allCases, activeCase, selectCase } = useForensic();

  return (
    <SocShell
      title="Cryptographic Evidence Vault"
      subtitle={`SHA-256 hash-chain verification & immutable audit records for ${activeCase.caseId}`}
      actions={
        <select
          value={activeCase.caseId}
          onChange={(e) => selectCase(e.target.value)}
          className="h-9 px-3 rounded bg-[#0E1217] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
          aria-label="Select investigation case"
        >
          {allCases.map((c) => (
            <option key={c.caseId} value={c.caseId}>
              {c.caseId} · {c.network}
            </option>
          ))}
        </select>
      }
    >
      <EvidenceVaultView
        evidence={activeCase.evidence}
        auditLogs={activeCase.auditLogs}
        caseId={activeCase.caseId}
      />
    </SocShell>
  );
}
