"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  FileText,
  Network,
  AlertTriangle,
  Gauge,
  Target,
  Clock,
  ShieldCheck,
  Printer,
  ArrowLeft,
} from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { CopyAddressButton } from "@/components/common/CopyAddressButton";
import { RiskGauge } from "@/components/common/RiskGauge";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { useForensic } from "@/context/ForensicContext";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { WalletDetailPanel } from "@/features/wallets/WalletDetailPanel";
import { SuspiciousFindingsView } from "@/features/findings/SuspiciousFindingsView";
import { ReceiverIntelligenceView } from "@/features/intelligence/ReceiverIntelligenceView";
import { InvestigationTimelineView } from "@/features/investigations/InvestigationTimelineView";
import { EvidenceVaultView } from "@/features/audit/EvidenceVaultView";
import { InvestigationReportModal } from "@/features/reports/InvestigationReportModal";
import {
  formatTimestamp,
  truncateAddress,
  cn,
  getCaseRiskScore,
  getCaseConfidence,
} from "@/lib/utils";
import { GraphNode } from "@/types/investigation";

type DetailTab =
  | "overview"
  | "graph"
  | "findings"
  | "risk"
  | "candidates"
  | "timeline"
  | "evidence"
  | "report";

const TABS: {
  id: DetailTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "overview", label: "Overview", icon: FileText },
  { id: "graph", label: "Graph", icon: Network },
  { id: "findings", label: "Findings", icon: AlertTriangle },
  { id: "risk", label: "Risk", icon: Gauge },
  { id: "candidates", label: "Candidates", icon: Target },
  { id: "timeline", label: "Timeline", icon: Clock },
  { id: "evidence", label: "Evidence", icon: ShieldCheck },
  { id: "report", label: "Report", icon: Printer },
];

export default function InvestigationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { allCases, activeCase, selectCase } = useForensic();

  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  const investigation = useMemo(() => {
    return allCases.find((c) => c.caseId === params?.id) || activeCase;
  }, [allCases, params?.id, activeCase]);

  useEffect(() => {
    if (params?.id && allCases.some((c) => c.caseId === params.id)) {
      selectCase(params.id);
    }
  }, [params?.id, allCases, selectCase]);

  const currentNode = selectedNode || investigation.nodes[0] || null;
  const riskScore = getCaseRiskScore(investigation);
  const confidenceScore = getCaseConfidence(investigation);

  const handleSelectWalletByAddress = (address: string) => {
    const match = investigation.nodes.find(
      (n) => (n.address || "").toLowerCase() === address.toLowerCase()
    );
    if (match) {
      setSelectedNode(match);
    }
    setActiveTab("graph");
  };

  return (
    <SocShell
      title={`${investigation.caseId} — ${investigation.title}`}
      subtitle={`Target ${investigation.target} · ${investigation.network} · Updated ${formatTimestamp(
        investigation.updatedAt
      )}`}
      actions={
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => router.push("/investigations")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-white/[0.1] text-xs font-mono text-[#8A929E] hover:text-[#F5F7FA]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            All Cases
          </button>
          <button
            type="button"
            onClick={() => setReportModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase"
          >
            <Printer className="w-3.5 h-3.5" />
            Export Report
          </button>
        </div>
      }
    >
      {/* 8 Detail Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-6 border-b border-white/[0.08]">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "inline-flex items-center gap-2 px-3.5 py-2 rounded text-xs font-mono uppercase tracking-wider whitespace-nowrap border transition-colors",
                active
                  ? "bg-[#00E5FF]/12 border-[#00E5FF]/40 text-[#00E5FF]"
                  : "bg-transparent border-transparent text-[#8A929E] hover:text-[#F5F7FA] hover:bg-white/[0.04]"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <div className="rounded border border-white/[0.08] bg-[#0E1217] p-6">
              <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-[#00E5FF]">
                EXECUTIVE CASE SUMMARY
              </p>
              <h2 className="text-lg font-semibold text-[#F5F7FA] mt-1">
                {investigation.title}
              </h2>
              <p className="text-sm text-[#8A929E] mt-2 leading-relaxed">
                Multi-hop forensic trace across {investigation.summary.walletsCount} wallets
                and {investigation.summary.transactionsCount} transactions ({investigation.dataSourceMode}).
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-5 border-t border-white/[0.08]">
                <div>
                  <p className="text-[10px] font-mono uppercase text-[#8A929E]">
                    Risk Index
                  </p>
                  <p className="text-lg font-mono font-bold text-[#EF4444] mt-1">
                    [ {riskScore} / 100 ]
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-mono uppercase text-[#8A929E]">
                    Confidence
                  </p>
                  <p className="text-lg font-mono font-bold text-[#00E5FF] mt-1">
                    {confidenceScore}%
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-mono uppercase text-[#8A929E]">
                    Total Volume
                  </p>
                  <p className="text-lg font-mono font-bold text-[#F5F7FA] mt-1">
                    ${investigation.summary.totalVolumeUSD.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-mono uppercase text-[#8A929E]">
                    Hop Depth
                  </p>
                  <p className="text-lg font-mono font-bold text-[#F5F7FA] mt-1">
                    {investigation.maxHops} Hops
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded border border-white/[0.08] bg-[#0E1217] p-6">
              <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#8A929E] mb-4">
                Key Forensic Findings ({investigation.findings.length})
              </h3>
              <div className="space-y-3">
                {investigation.findings.map((f) => (
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
                      <p className="text-xs text-[#8A929E] mt-1">
                        {f.explanation}
                      </p>
                    </div>
                    <span className="text-[11px] font-mono text-[#00E5FF] shrink-0">
                      {Math.round(f.confidence)}% conf
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-4 space-y-6">
            <div className="rounded border border-white/[0.08] bg-[#0E1217] p-5">
              <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#8A929E] mb-3">
                Target Seed Address
              </h3>
              <div className="p-3 rounded bg-[#07090C] border border-white/[0.06] flex items-center justify-between gap-2">
                <span className="text-xs font-mono text-[#F5F7FA] break-all">
                  {investigation.target}
                </span>
                <CopyAddressButton value={investigation.target} />
              </div>
              <div className="mt-4 space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-[#8A929E]">Status</span>
                  <span className="text-[#00E5FF]">{investigation.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A929E]">Nodes / Edges</span>
                  <span className="text-[#F5F7FA]">
                    {investigation.nodes.length} / {investigation.edges.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A929E]">Evidence Items</span>
                  <span className="text-[#22C55E]">
                    {investigation.evidence.length}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded border border-white/[0.08] bg-[#0E1217] p-5">
              <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#8A929E] mb-3">
                Top Receiver Candidate
              </h3>
              {investigation.receivers[0] ? (
                <div className="p-3 rounded bg-[#07090C] border border-white/[0.06]">
                  <p className="text-xs font-mono text-[#00E5FF]">
                    {truncateAddress(investigation.receivers[0].walletAddress, 8, 6)}
                  </p>
                  <p className="text-xs text-[#F5F7FA] mt-1">
                    {investigation.receivers[0].serviceLabel || "Unlabeled Destination"}
                  </p>
                  <p className="text-[11px] font-mono text-[#8A929E] mt-2">
                    Score: [ {Math.round(investigation.receivers[0].attributionConfidence)} / 100 ]
                  </p>
                </div>
              ) : (
                <p className="text-xs text-[#8A929E]">No receiver candidates ranked.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === "graph" && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-8">
            <CytoscapeGraph
              nodes={investigation.nodes}
              edges={investigation.edges}
              selectedNodeId={currentNode?.id}
              onSelectNode={(n) => setSelectedNode(n)}
              className="h-[620px]"
            />
          </div>
          <div className="xl:col-span-4">
            {currentNode && (
              <WalletDetailPanel
                node={currentNode}
                allEdges={investigation.edges}
                allFindings={investigation.findings}
                allEvidence={investigation.evidence}
                onExploreMore={(addr) => handleSelectWalletByAddress(addr)}
              />
            )}
          </div>
        </div>
      )}

      {activeTab === "findings" && (
        <SuspiciousFindingsView
          findings={investigation.findings}
          onSelectWallet={handleSelectWalletByAddress}
        />
      )}

      {activeTab === "risk" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <RiskGauge
              label="Risk Priority"
              score={riskScore}
              subtitle="Composite severity urgency"
            />
            <RiskGauge
              label="Attribution Confidence"
              score={confidenceScore}
              subtitle="Capped if mixer ambiguity exists"
            />
            <RiskGauge
              label="Known Risk Exposure"
              score={Math.min(100, investigation.findings.length * 22 + 20)}
              subtitle="Sanctioned / illicit hops"
            />
            <RiskGauge
              label="Investigation Coverage"
              score={Math.min(
                100,
                Math.round(
                  (investigation.evidence.length / Math.max(1, investigation.nodes.length)) * 100
                )
              )}
              subtitle="Evidence-backed node ratio"
            />
          </div>
          <div className="rounded border border-[#F59E0B]/30 bg-[#F59E0B]/10 p-4 text-xs font-mono text-[#F59E0B]">
            IDENTITY RESTRAINT NOTICE: Graph proximity and heuristic clustering do not
            constitute legal proof of real-world ownership. Attribution confidence is
            automatically capped when CoinJoin or mixer ambiguity is detected.
          </div>
        </div>
      )}

      {activeTab === "candidates" && (
        <ReceiverIntelligenceView
          receivers={investigation.receivers}
          network={investigation.network}
          onSelectCandidate={handleSelectWalletByAddress}
        />
      )}

      {activeTab === "timeline" && (
        <InvestigationTimelineView timeline={investigation.timeline} />
      )}

      {activeTab === "evidence" && (
        <EvidenceVaultView
          evidence={investigation.evidence}
          auditLogs={investigation.auditLogs}
          caseId={investigation.caseId}
        />
      )}

      {activeTab === "report" && (
        <div className="rounded border border-white/[0.08] bg-[#0E1217] p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <div>
              <h2 className="text-base font-semibold text-[#F5F7FA]">
                Forensic Investigation Dossier
              </h2>
              <p className="text-xs font-mono text-[#8A929E] mt-1">
                Ready for PDF print, Markdown export, or JSON archival.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setReportModalOpen(true)}
              className="px-4 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase"
            >
              Open Full Report Preview
            </button>
          </div>
          <pre className="p-4 rounded bg-[#07090C] border border-white/[0.06] text-xs font-mono text-[#8A929E] overflow-x-auto">
            {JSON.stringify(
              {
                caseId: investigation.caseId,
                network: investigation.network,
                target: investigation.target,
                riskScore,
                findingsCount: investigation.findings.length,
                evidenceCount: investigation.evidence.length,
              },
              null,
              2
            )}
          </pre>
        </div>
      )}

      <InvestigationReportModal
        investigation={investigation}
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
      />
    </SocShell>
  );
}
