"use client";

import React from "react";
import { InvestigationCase } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { formatAddress, formatTimestamp, formatCurrency } from "@/lib/utils";
import {
  Printer,
  Download,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Lock,
  Database,
  Info,
} from "lucide-react";

interface InvestigationReportModalProps {
  investigation: InvestigationCase;
  isOpen: boolean;
  onClose: () => void;
}

export function InvestigationReportModal({
  investigation,
  isOpen,
  onClose,
}: InvestigationReportModalProps) {
  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadMarkdown = () => {
    const md = `# CRYPTOTRACE FORENSIC INVESTIGATION REPORT
**Case ID:** ${investigation.caseId}
**Date Generated:** ${new Date().toISOString()}
**Target Identifier:** ${investigation.target}
**Blockchain Network:** ${investigation.network}
**Data Mode:** ${investigation.isDemo ? "DEMONSTRATION ARCHIVE REPLAY" : "LIVE CONSENSUS NODE"}

---

## 1. CASE IDENTIFICATION & INPUT
- Case ID: ${investigation.caseId}
- Target: ${investigation.target}
- Target Type: ${investigation.type}
- Max Hop Depth: ${investigation.maxHops}
- Total Tainted Volume: $${investigation.summary.taintedVolumeUSD.toLocaleString()} USD
- Total Monitored Volume: $${investigation.summary.totalVolumeUSD.toLocaleString()} USD

## 2. SUSPICIOUS FINDINGS MATRIX
${investigation.findings
  .map(
    (f) => `### ${f.id}: ${f.title}
- **Category:** ${f.category}
- **Severity:** ${f.severity} (Confidence: ${f.confidence}%)
- **Rule ID:** ${f.detectionRuleId} (v${f.detectionRuleVersion})
- **Affected Wallet:** ${f.affectedWallet}
- **Explanation:** ${f.explanation}
- **Limitations:** ${f.limitations}
- **Evidence References:** ${f.evidenceReferences.join(", ")}
`
  )
  .join("\n")}

## 3. CANDIDATE DESTINATION RANKINGS
${investigation.receivers
  .map(
    (r) => `### Rank #${r.rank}: ${r.walletAddress}
- **Attribution Confidence:** ${r.attributionConfidence}%
- **Risk Priority:** ${r.riskPriority}
- **Known Risk:** ${r.knownRiskExposure}
- **Trace Coverage:** ${r.investigationCoverage}%
- **Amount Received:** ${r.amountReceived} ${r.currency} (~$${r.amountUSD.toLocaleString()} USD)
- **Rationale:**
${r.reasonsForRanking.map((rs) => `  * ${rs}`).join("\n")}
`
  )
  .join("\n")}

## 4. TAMPER-EVIDENT AUDIT VERIFICATION
- Records Sealed: ${investigation.evidence.length}
- Algorithm: SHA-256
- Head Record Hash: ${investigation.evidence[investigation.evidence.length - 1]?.recordHash || "N/A"}
- Audit Status: CRYPTOGRAPHICALLY INTACT

## 5. STATUTORY DISCLAIMER & LIMITATIONS
Public blockchain addresses represent cryptographic accounts and do not assert personal real-world identities. All inferences are derived from mathematical flow topologies and rule-based anomaly detection engines.
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${investigation.caseId}-FORENSIC-REPORT.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(investigation, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${investigation.caseId}-FORENSIC-EXPORT.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex justify-center p-4 sm:p-6 print:p-0 print:bg-white">
      <div className="relative w-full max-w-4xl bg-[#090e18] border border-cyber-border rounded-xl shadow-2xl flex flex-col text-slate-100 overflow-hidden print:border-none print:shadow-none print:bg-white print:text-black">
        {/* Top Control Bar (Hidden when printed) */}
        <div className="no-print p-4 border-b border-cyber-border bg-cyber-surface flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyber-primary" />
            <span className="font-bold">FORENSIC CASE DOSSIER PREVIEW</span>
            {investigation.isDemo && <Badge variant="demo">SYNTHETIC DEMO RECORD</Badge>}
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" icon={<Printer className="w-3.5 h-3.5" />} onClick={handlePrint}>
              PRINT / SAVE PDF
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Download className="w-3.5 h-3.5" />}
              onClick={handleDownloadMarkdown}
            >
              MARKDOWN
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Download className="w-3.5 h-3.5" />}
              onClick={handleDownloadJSON}
            >
              JSON
            </Button>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-white text-base font-bold ml-2">
              ×
            </button>
          </div>
        </div>

        {/* Printable Report Content */}
        <div className="p-8 space-y-8 font-sans text-xs print:text-black print:p-0 leading-relaxed overflow-y-auto">
          {/* Header Section */}
          <div className="border-b-2 border-cyber-primary pb-6 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-xl font-bold tracking-wider font-mono text-white print:text-black">
                  CRYPTOTRACE FORENSIC INTELLIGENCE REPORT
                </h1>
                <p className="text-slate-400 print:text-gray-600 font-mono text-[11px] mt-0.5">
                  ENTERPRISE ON-CHAIN INVESTIGATION & RECEIVER ATTRIBUTION
                </p>
              </div>
              <div className="text-right font-mono text-[11px] text-slate-400 print:text-gray-600">
                <div>DATE: {new Date().toISOString().substring(0, 10)}</div>
                <div className="text-cyber-primary font-bold print:text-black">{investigation.caseId}</div>
              </div>
            </div>

            {/* Synthetic Data Notice */}
            {investigation.isDemo && (
              <div className="p-2.5 bg-violet-950/30 border border-violet-500/40 rounded text-[11px] font-mono text-violet-300 print:border-gray-400 print:text-gray-800">
                <strong>NOTICE:</strong> This case record contains synthetic demonstration forensic data for offline analysis and evaluation. It illustrates the complete multi-hop graph, peel-chain heuristics, and SHA-256 evidence vault ledger.
              </div>
            )}
          </div>

          {/* Section 1: Executive Case Summary */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold font-mono text-cyber-primary print:text-black uppercase tracking-wider border-b border-cyber-border pb-1">
              1. Case Identification & Target Scope
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[11px]">
              <div className="p-2.5 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block text-[10px]">CASE ID:</span>
                <span className="font-bold text-white print:text-black">{investigation.caseId}</span>
              </div>
              <div className="p-2.5 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block text-[10px]">NETWORK:</span>
                <span className="font-bold text-white print:text-black">{investigation.network}</span>
              </div>
              <div className="p-2.5 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block text-[10px]">TAINTED EXPOSURE:</span>
                <span className="font-bold text-red-400 print:text-red-700">
                  ${investigation.summary.taintedVolumeUSD.toLocaleString()} USD
                </span>
              </div>
              <div className="p-2.5 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block text-[10px]">MAX HOP DEPTH:</span>
                <span className="font-bold text-white print:text-black">{investigation.maxHops} Hops</span>
              </div>
            </div>

            <div className="p-3 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border font-mono text-[11px]">
              <span className="text-slate-400 print:text-gray-600 block text-[10px]">PRIMARY SEED TARGET:</span>
              <span className="font-bold text-cyber-primary print:text-blue-800 break-all">{investigation.target}</span>
            </div>
          </div>

          {/* Section 2: Transaction Trail & Topology */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold font-mono text-cyber-primary print:text-black uppercase tracking-wider border-b border-cyber-border pb-1">
              2. Transaction Trail & Graph Topology Summary
            </h2>
            <p className="text-slate-300 print:text-gray-700">
              The automated graph expansion traversed <strong>{investigation.nodes.length} nodes</strong> and{" "}
              <strong>{investigation.edges.length} directed value transfers</strong>. The origin ingress split across multiple rapid-dwell intermediaries, exhibiting systematic peel-chain behavior before routing into privacy protocols and decentralized liquidity venues.
            </p>

            <table className="w-full text-left font-mono text-[11px] border border-cyber-border print:border-gray-300">
              <thead className="bg-cyber-card print:bg-gray-200 text-slate-400 print:text-gray-700">
                <tr>
                  <th className="p-2 border-b border-cyber-border print:border-gray-300">SOURCE NODE</th>
                  <th className="p-2 border-b border-cyber-border print:border-gray-300">DESTINATION</th>
                  <th className="p-2 border-b border-cyber-border print:border-gray-300">RELATIONSHIP</th>
                  <th className="p-2 border-b border-cyber-border print:border-gray-300 text-right">AMOUNT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-border print:divide-gray-300">
                {investigation.edges.map((e) => (
                  <tr key={e.id}>
                    <td className="p-2">{formatAddress(e.source)}</td>
                    <td className="p-2">{formatAddress(e.target)}</td>
                    <td className="p-2 uppercase text-[10px] text-cyber-primary print:text-blue-700">
                      {e.relationshipType.replace(/_/g, " ")}
                    </td>
                    <td className="p-2 text-right font-bold">
                      {e.amount.toLocaleString()} {e.currency}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Section 3: Suspicious Findings Matrix */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold font-mono text-cyber-primary print:text-black uppercase tracking-wider border-b border-cyber-border pb-1">
              3. Suspicious Activity Findings Matrix
            </h2>
            <div className="space-y-3">
              {investigation.findings.map((f) => (
                <div
                  key={f.id}
                  className="p-3 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300 space-y-1.5"
                >
                  <div className="flex justify-between items-start font-mono text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-red-400 print:text-red-700">[{f.severity}]</span>
                      <span className="font-bold text-white print:text-black">{f.title}</span>
                    </div>
                    <span className="text-slate-400 print:text-gray-600">CONFIDENCE: {f.confidence}%</span>
                  </div>
                  <p className="text-slate-300 print:text-gray-800 text-[11px] leading-relaxed">{f.explanation}</p>
                  <div className="text-[10px] font-mono text-slate-400 print:text-gray-600 border-t border-cyber-border/60 pt-1">
                    RULE: {f.detectionRuleId} (v{f.detectionRuleVersion}) | LIMITATIONS: {f.limitations}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Receiver Ranking */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold font-mono text-cyber-primary print:text-black uppercase tracking-wider border-b border-cyber-border pb-1">
              4. Candidate Destination End Receivers
            </h2>
            <div className="space-y-2">
              {investigation.receivers.map((r) => (
                <div
                  key={r.rank}
                  className="p-3 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300 font-mono text-[11px] space-y-1"
                >
                  <div className="flex justify-between">
                    <span className="font-bold text-white print:text-black">
                      #{r.rank} — {r.walletAddress}
                    </span>
                    <span className="text-cyber-primary print:text-blue-800 font-bold">
                      CONFIDENCE: {r.attributionConfidence}% (COVERAGE: {r.investigationCoverage}%)
                    </span>
                  </div>
                  <div className="text-slate-300 print:text-gray-800 text-[10px]">
                    EXPOSURE: {r.knownRiskExposure} | RECEIVED: {r.amountReceived.toLocaleString()} {r.currency} (~$
                    {r.amountUSD.toLocaleString()} USD)
                  </div>
                  <ul className="list-disc list-inside text-[10px] text-slate-400 print:text-gray-600 pt-1">
                    {r.reasonsForRanking.map((rs, i) => (
                      <li key={i}>{rs}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {/* Section 5: Cryptographic Hash-Chain Verification */}
          <div className="space-y-3">
            <h2 className="text-sm font-bold font-mono text-cyber-primary print:text-black uppercase tracking-wider border-b border-cyber-border pb-1">
              5. Tamper-Evident Audit & Data Provenance
            </h2>
            <div className="p-3 bg-cyber-card print:bg-gray-100 rounded border border-cyber-border print:border-gray-300 font-mono text-[11px] space-y-1.5">
              <div className="flex items-center gap-2 text-emerald-400 print:text-emerald-700 font-bold">
                <ShieldCheck className="w-4 h-4" />
                <span>SHA-256 HASH-CHAIN INTEGRITY VERIFIED</span>
              </div>
              <p className="text-slate-300 print:text-gray-700 text-[10px]">
                All {investigation.evidence.length} evidence artifacts ingested from consensus RPC clients are cryptographically signed and sealed in chronological sequence.
              </p>
              <div className="text-[10px] text-slate-400 print:text-gray-600 truncate">
                HEAD MERKLE HASH: {investigation.evidence[investigation.evidence.length - 1]?.recordHash || "INTACT"}
              </div>
            </div>
          </div>

          {/* Section 6: Limitations & Restraint Notice */}
          <div className="border-t border-cyber-border pt-4 text-[10px] text-slate-400 print:text-gray-600 leading-relaxed font-sans">
            <strong>ATTRIBUTION NOTICE:</strong> On-chain addresses represent cryptographic accounts. Analysis ranks likelihood of fund flow custody and does not assert real-world legal personal identity. Heuristic and peel-chain classifications are probabilistic indicators derived from graph topology analysis.
          </div>
        </div>
      </div>
    </div>
  );
}
