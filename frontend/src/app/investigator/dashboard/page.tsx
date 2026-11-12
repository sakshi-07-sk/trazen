"use client";

import React, { useMemo, useState } from "react";
import {
  LayoutDashboard,
  PlusCircle,
  Search,
  Network,
  AlertTriangle,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { RoleNavItem, RoleShell } from "@/components/layout/RoleShell";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";
import { CopyAddressButton } from "@/components/common/CopyAddressButton";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { NewInvestigationForm } from "@/features/investigations/NewInvestigationForm";
import { WalletDetailPanel } from "@/features/wallets/WalletDetailPanel";
import { SuspiciousFindingsView } from "@/features/findings/SuspiciousFindingsView";
import { EvidenceVaultView } from "@/features/audit/EvidenceVaultView";
import { InvestigationReportModal } from "@/features/reports/InvestigationReportModal";
import { useForensic } from "@/context/ForensicContext";
import {
  formatTimestamp,
  getCaseRiskScore,
  truncateAddress,
} from "@/lib/utils";
import { GraphNode, InvestigationCase } from "@/types/investigation";

const INVESTIGATOR_NAV: RoleNavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "new", label: "New Investigation", icon: PlusCircle },
  { id: "tracing", label: "Wallet Tracing", icon: Search },
  { id: "graph", label: "Transaction Graph", icon: Network },
  { id: "findings", label: "Findings", icon: AlertTriangle },
  { id: "evidence", label: "Evidence", icon: ShieldCheck },
  { id: "reports", label: "Reports", icon: FileText },
];

export default function InvestigatorDashboardPage() {
  const { allCases, activeCase, selectCase, addOrActivateCase, addToast } =
    useForensic();

  const [section, setSection] = useState("dashboard");
  const [traceQuery, setTraceQuery] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  const inspectedNode = useMemo(() => {
    if (selectedNode && activeCase.nodes.some((n) => n.id === selectedNode.id)) {
      return selectedNode;
    }
    return activeCase.nodes[0] || null;
  }, [selectedNode, activeCase]);

  const matchedNodes = useMemo(() => {
    const q = traceQuery.trim().toLowerCase();
    if (!q) return activeCase.nodes;
    return activeCase.nodes.filter(
      (n) =>
        (n.address || "").toLowerCase().includes(q) ||
        (n.entityName || "").toLowerCase().includes(q) ||
        n.id.toLowerCase().includes(q)
    );
  }, [activeCase.nodes, traceQuery]);

  const handleCreated = (created: InvestigationCase) => {
    addOrActivateCase(created);
    addToast({
      title: "Investigation Launched",
      description: `${created.caseId} (${created.network}) is now active.`,
      variant: "success",
    });
    setSection("graph");
  };

  return (
    <RoleShell
      role="INVESTIGATOR"
      navItems={INVESTIGATOR_NAV}
      activeSection={section}
      onSelectSection={setSection}
      title="Investigator Forensic Workspace"
      subtitle={`Active Case: ${activeCase.caseId} (${activeCase.network}) · Target ${truncateAddress(
        activeCase.target,
        8,
        6
      )}`}
      actions={
        <select
          value={activeCase.caseId}
          onChange={(e) => {
            selectCase(e.target.value);
            setSelectedNode(null);
          }}
          className="h-9 px-3 rounded-sm bg-[#151616] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
          aria-label="Select investigation case"
        >
          {allCases.map((c) => (
            <option key={c.caseId} value={c.caseId}>
              {c.caseId} · {c.network} · {c.title}
            </option>
          ))}
        </select>
      }
    >
      {section === "dashboard" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Investigation History
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#F1EEE6] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={allCases.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">BTC & ETH case dossiers</p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Clustered Wallets
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={activeCase.nodes.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Up to {activeCase.maxHops}-hop depth
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Suspicious Detections
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={activeCase.findings.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Peel-chain, mixer & clustering
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Evidence Records
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#22C55E] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={activeCase.evidence.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">SHA-256 hash-chained</p>
            </div>
          </div>

          <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
            <div className="flex items-center justify-between mb-4">
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Investigation History
              </h2>
              <button
                type="button"
                onClick={() => setSection("new")}
                className="px-3.5 py-2 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-mono font-semibold uppercase tracking-[0.12em] transition-colors"
              >
                + New Trace
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-[11px] font-mono uppercase text-[#A6A39A]">
                    <th className="py-2.5 pr-4">Case ID</th>
                    <th className="py-2.5 pr-4">Title</th>
                    <th className="py-2.5 pr-4">Target</th>
                    <th className="py-2.5 pr-4">Risk</th>
                    <th className="py-2.5 pr-4">Updated</th>
                    <th className="py-2.5 text-right">Graph</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06] text-xs">
                  {allCases.map((c) => (
                    <tr key={c.caseId}>
                      <td className="py-3 pr-4 font-mono text-[#FF6A13]">{c.caseId}</td>
                      <td className="py-3 pr-4 text-[#F1EEE6]">{c.title}</td>
                      <td className="py-3 pr-4 font-mono text-[#A6A39A]">
                        <div className="flex items-center gap-1.5">
                          <span>{truncateAddress(c.target, 6, 4)}</span>
                          <CopyAddressButton value={c.target} />
                        </div>
                      </td>
                      <td className="py-3 pr-4 font-mono text-[#FF6A13]">
                        [ {getCaseRiskScore(c)} / 100 ]
                      </td>
                      <td className="py-3 pr-4 font-mono text-[#A6A39A]">
                        {formatTimestamp(c.updatedAt)}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            selectCase(c.caseId);
                            setSection("graph");
                          }}
                          className="px-2.5 py-1 rounded-sm border border-[#FF6A13]/45 text-[#FF6A13] hover:bg-[#FF6A13]/15 text-[11px] font-mono transition-colors"
                        >
                          Open Graph
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {section === "new" && (
        <div className="max-w-2xl rounded-sm border border-white/10 bg-[#151616] p-6">
          <h2
            className="text-xl font-bold uppercase tracking-wide text-[#F1EEE6] mb-1"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            Create New Multi-Hop Investigation
          </h2>
          <p className="text-xs text-[#A6A39A] mb-5">
            Enter a Bitcoin or Ethereum wallet address or transaction hash to trace up
            to 3 hops.
          </p>
          <NewInvestigationForm onInvestigationCreated={handleCreated} />
        </div>
      )}

      {section === "tracing" && (
        <div className="space-y-4">
          <div className="rounded-sm border border-white/10 bg-[#151616] p-4 flex items-center gap-3">
            <Search className="w-4 h-4 text-[#FF6A13]" />
            <input
              type="text"
              value={traceQuery}
              onChange={(e) => setTraceQuery(e.target.value)}
              placeholder="Search Bitcoin/Ethereum wallet address, cluster label, or tx node..."
              className="flex-1 bg-transparent text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/60 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {matchedNodes.map((n) => (
              <div
                key={n.id}
                className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-4 space-y-2 transition-colors"
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#FF6A13] uppercase">{n.type}</span>
                  <span className="text-[#FF6A13]">Risk [ {n.riskScore} ]</span>
                </div>
                <p className="text-sm font-medium text-[#F1EEE6]">
                  {n.entityName || "Unlabeled Wallet"}
                </p>
                <div className="flex items-center justify-between text-xs font-mono text-[#A6A39A]">
                  <span>{truncateAddress(n.address || n.id, 8, 6)}</span>
                  <CopyAddressButton value={n.address || n.id} />
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedNode(n);
                    setSection("graph");
                  }}
                  className="w-full mt-2 py-1.5 rounded-sm border border-white/15 hover:border-[#FF6A13] text-[11px] font-mono text-[#F1EEE6] transition-colors"
                >
                  Inspect on Graph
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {section === "graph" && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          <div className="xl:col-span-8">
            <CytoscapeGraph
              nodes={activeCase.nodes}
              edges={activeCase.edges}
              selectedNodeId={inspectedNode?.id}
              onSelectNode={(n) => setSelectedNode(n)}
              className="h-[640px]"
            />
          </div>
          <div className="xl:col-span-4">
            {inspectedNode && (
              <WalletDetailPanel
                node={inspectedNode}
                allEdges={activeCase.edges}
                allFindings={activeCase.findings}
                allEvidence={activeCase.evidence}
                onExploreMore={(addr) => {
                  const match = activeCase.nodes.find(
                    (n) => (n.address || "").toLowerCase() === addr.toLowerCase()
                  );
                  if (match) setSelectedNode(match);
                }}
              />
            )}
          </div>
        </div>
      )}

      {section === "findings" && (
        <SuspiciousFindingsView
          findings={activeCase.findings}
          onSelectWallet={() => setSection("graph")}
          onSelectFinding={() => setSection("graph")}
        />
      )}

      {section === "evidence" && (
        <EvidenceVaultView
          evidence={activeCase.evidence}
          auditLogs={activeCase.auditLogs}
          caseId={activeCase.caseId}
        />
      )}

      {section === "reports" && (
        <div className="rounded-sm border border-white/10 bg-[#151616] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Generate Investigation Report
              </h2>
              <p className="text-xs text-[#A6A39A] mt-1">
                Export PDF, Markdown, or JSON evidence bundles for {activeCase.caseId}.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setReportModalOpen(true)}
              className="px-4 py-2 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-mono font-semibold uppercase tracking-[0.12em] transition-colors"
            >
              Open Report Builder
            </button>
          </div>
        </div>
      )}

      <InvestigationReportModal
        investigation={activeCase}
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
      />
    </RoleShell>
  );
}
