"use client";

import React, { useMemo, useState } from "react";
import { Download, FileCode, FileText, Printer } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { useForensic } from "@/context/ForensicContext";
import { InvestigationReportModal } from "@/features/reports/InvestigationReportModal";
import {
  formatTimestamp,
  getCaseConfidence,
  getCaseRiskScore,
} from "@/lib/utils";

export default function ReportsPage() {
  const { allCases, activeCase, selectCase, addToast } = useForensic();
  const [modalOpen, setModalOpen] = useState(false);

  const riskScore = getCaseRiskScore(activeCase);
  const confidenceScore = getCaseConfidence(activeCase);

  const markdownReport = useMemo(() => {
    const lines = [
      `# CryptoTrace Forensic Investigation Report`,
      `**Case ID:** ${activeCase.caseId}`,
      `**Title:** ${activeCase.title}`,
      `**Network:** ${activeCase.network}`,
      `**Target Address:** \`${activeCase.target}\``,
      `**Risk Score:** [ ${riskScore} / 100 ]`,
      `**Confidence:** ${confidenceScore}%`,
      `**Total Traced Volume:** $${activeCase.summary.totalVolumeUSD.toLocaleString()}`,
      `**Generated:** ${new Date().toISOString()}`,
      ``,
      `## Executive Summary`,
      `Multi-hop trace across ${activeCase.summary.walletsCount} wallets and ${activeCase.summary.transactionsCount} transactions.`,
      ``,
      `## Suspicious Findings (${activeCase.findings.length})`,
      ...activeCase.findings.map(
        (f) =>
          `- **[${f.severity}] ${f.title}** (${Math.round(
            f.confidence
          )}% confidence): ${f.explanation}`
      ),
      ``,
      `## Probable End-Receiver Candidates (${activeCase.receivers.length})`,
      ...activeCase.receivers.map(
        (r, i) =>
          `${i + 1}. \`${r.walletAddress}\` — ${
            r.serviceLabel || "Unlabeled"
          } (Score: ${Math.round(r.attributionConfidence)}/100)`
      ),
      ``,
      `## Evidence Vault (${activeCase.evidence.length} SHA-256 Records)`,
      ...activeCase.evidence.map(
        (e) => `- \`${e.id}\`: ${e.details} (SHA-256: \`${e.recordHash}\`)`
      ),
    ];
    return lines.join("\n");
  }, [activeCase, riskScore, confidenceScore]);

  const downloadFile = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    addToast({
      title: "Export Complete",
      description: `Downloaded ${filename}`,
      variant: "success",
    });
  };

  return (
    <SocShell
      title="Forensic Reports & Exports"
      subtitle={`Generate PDF, Markdown, and JSON dossiers for ${activeCase.caseId}`}
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
      {/* Export Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 print:hidden">
        <button
          type="button"
          onClick={() => window.print()}
          className="rounded border border-[#00E5FF]/40 bg-[#00E5FF]/10 p-5 text-left hover:bg-[#00E5FF]/15 transition-colors"
        >
          <Printer className="w-5 h-5 text-[#00E5FF] mb-2" />
          <p className="text-sm font-semibold text-[#F5F7FA]">Print / Save PDF</p>
          <p className="text-xs text-[#8A929E] mt-1">
            Formatted forensic dossier via browser print dialog
          </p>
        </button>

        <button
          type="button"
          onClick={() =>
            downloadFile(
              markdownReport,
              `${activeCase.caseId}-report.md`,
              "text/markdown;charset=utf-8"
            )
          }
          className="rounded border border-white/[0.1] bg-[#0E1217] p-5 text-left hover:border-[#00E5FF]/40 transition-colors"
        >
          <FileText className="w-5 h-5 text-[#00E5FF] mb-2" />
          <p className="text-sm font-semibold text-[#F5F7FA]">
            Export Markdown (.md)
          </p>
          <p className="text-xs text-[#8A929E] mt-1">
            Structured narrative with SHA-256 evidence references
          </p>
        </button>

        <button
          type="button"
          onClick={() =>
            downloadFile(
              JSON.stringify(activeCase, null, 2),
              `${activeCase.caseId}-bundle.json`,
              "application/json"
            )
          }
          className="rounded border border-white/[0.1] bg-[#0E1217] p-5 text-left hover:border-[#00E5FF]/40 transition-colors"
        >
          <FileCode className="w-5 h-5 text-[#00E5FF] mb-2" />
          <p className="text-sm font-semibold text-[#F5F7FA]">
            Export Evidence JSON (.json)
          </p>
          <p className="text-xs text-[#8A929E] mt-1">
            Complete machine-readable graph, findings & audit log
          </p>
        </button>
      </div>

      {/* Live Preview Dossier */}
      <article className="rounded border border-white/[0.08] bg-[#0E1217] p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-white/[0.08] pb-6">
          <div>
            <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#00E5FF]">
              CRYPTOTRACE FORENSIC DOSSIER // {activeCase.caseId}
            </p>
            <h2 className="text-2xl font-bold text-[#F5F7FA] mt-1">
              {activeCase.title}
            </h2>
            <p className="text-xs font-mono text-[#8A929E] mt-1">
              Target: {activeCase.target} · Updated{" "}
              {formatTimestamp(activeCase.updatedAt)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded border border-white/[0.12] text-xs font-mono text-[#F5F7FA] hover:border-[#00E5FF]/50 print:hidden"
          >
            <Download className="w-3.5 h-3.5 text-[#00E5FF]" />
            Modal View
          </button>
        </div>

        <p className="text-sm text-[#8A929E] leading-relaxed">
          Multi-hop forensic analysis covering {activeCase.summary.walletsCount}{" "}
          wallets and ${activeCase.summary.totalVolumeUSD.toLocaleString()} in traced
          volume.
        </p>

        <div>
          <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#8A929E] mb-3">
            Detected Findings ({activeCase.findings.length})
          </h3>
          <div className="space-y-2.5">
            {activeCase.findings.map((f) => (
              <div
                key={f.id}
                className="p-3.5 rounded bg-[#07090C] border border-white/[0.06] flex items-start justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={f.severity} />
                    <span className="text-xs font-semibold text-[#F5F7FA]">
                      {f.title}
                    </span>
                  </div>
                  <p className="text-xs text-[#8A929E] mt-1">{f.explanation}</p>
                </div>
                <span className="text-xs font-mono text-[#00E5FF] shrink-0">
                  {Math.round(f.confidence)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </article>

      <InvestigationReportModal
        investigation={activeCase}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </SocShell>
  );
}
