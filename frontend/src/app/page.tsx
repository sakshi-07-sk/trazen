"use client";

import React, { useState, useEffect } from "react";
import {
  InvestigationCase,
  InvestigationStats,
  GraphNode,
  GraphEdge,
} from "@/types/investigation";
import { MOCK_ETH_CASE, MOCK_BTC_CASE, MOCK_STATS } from "@/lib/mockData";
import { investigationApi } from "@/services/api/investigationApi";
import { AppNavbar, ActiveTab } from "@/components/layout/AppNavbar";
import { CommandCenterView } from "@/features/investigations/CommandCenterView";
import { NewInvestigationForm } from "@/features/investigations/NewInvestigationForm";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { WalletDetailPanel } from "@/features/wallets/WalletDetailPanel";
import { SuspiciousFindingsView } from "@/features/findings/SuspiciousFindingsView";
import { ReceiverIntelligenceView } from "@/features/intelligence/ReceiverIntelligenceView";
import { InvestigationTimelineView } from "@/features/investigations/InvestigationTimelineView";
import { EvidenceVaultView } from "@/features/audit/EvidenceVaultView";
import { TraceAICopilotPanel } from "@/features/copilot/TraceAICopilotPanel";
import { InvestigationReportModal } from "@/features/reports/InvestigationReportModal";
import { formatAddress, formatCurrency } from "@/lib/utils";
import { Badge } from "@/components/common/Badge";
import { AlertTriangle, Layers, Info } from "lucide-react";

export default function Home() {
  const [stats, setStats] = useState<InvestigationStats>(MOCK_STATS);
  const [allCases, setAllCases] = useState<InvestigationCase[]>([
    MOCK_ETH_CASE,
    MOCK_BTC_CASE,
  ]);
  const [activeCase, setActiveCase] = useState<InvestigationCase>(MOCK_ETH_CASE);
  const [activeTab, setActiveTab] = useState<ActiveTab>("command");

  // Selection states
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);

  // Modals & Drawers
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Fetch initial cases/stats if API is available
  useEffect(() => {
    investigationApi
      .getStats()
      .then((s) => setStats(s))
      .catch((err) => console.log("Using local mock stats"));

    investigationApi
      .getInvestigations()
      .then((cases) => {
        if (cases && cases.length > 0) {
          setAllCases(cases);
        }
      })
      .catch((err) => console.log("Using local mock investigations"));
  }, []);

  const handleSelectCase = (caseId: string) => {
    const found = allCases.find((c) => c.caseId === caseId);
    if (found) {
      setActiveCase(found);
      setSelectedNode(null);
      setSelectedEdge(null);
    }
  };

  const handleInvestigationCreated = (newCase: InvestigationCase) => {
    setAllCases((prev) => [newCase, ...prev.filter((c) => c.caseId !== newCase.caseId)]);
    setActiveCase(newCase);
    setSelectedNode(null);
    setSelectedEdge(null);
    setActiveTab("trace");
  };

  const handleSelectWallet = (address: string) => {
    // Find node matching address in active case
    const node = activeCase.nodes.find(
      (n) => n.address?.toLowerCase() === address.toLowerCase() || n.id === address
    );
    if (node) {
      setSelectedNode(node);
      setActiveTab("trace");
    } else {
      setActiveTab("wallet");
    }
  };

  return (
    <div className="min-h-screen bg-cyber-bg text-slate-100 flex flex-col font-sans selection:bg-cyber-primary selection:text-white">
      {/* Primary Application Navigation Bar */}
      <AppNavbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        activeCase={activeCase}
        allCases={allCases}
        onSelectCase={handleSelectCase}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onOpenReport={() => setIsReportModalOpen(true)}
        isCopilotOpen={isCopilotOpen}
      />

      {/* Main Workspace Body */}
      <main className="flex-1 p-4 lg:p-6 max-w-[1720px] w-full mx-auto">
        {/* TAB 1: Command Center */}
        {activeTab === "command" && (
          <CommandCenterView
            stats={stats}
            onOpenCase={(id) => {
              handleSelectCase(id);
              setActiveTab("trace");
            }}
            onNewInvestigation={() => setActiveTab("new")}
            onOpenTrace={(id) => {
              handleSelectCase(id);
              setActiveTab("trace");
            }}
          />
        )}

        {/* TAB 2: Interactive Trace Explorer (Cytoscape.js) */}
        {activeTab === "trace" && (
          <div className="space-y-4">
            {/* Header info bar */}
            <div className="p-3 bg-cyber-surface border border-cyber-border rounded-lg flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center gap-2.5">
                <Badge variant={activeCase.isDemo ? "demo" : "verified"}>
                  {activeCase.dataSourceMode}
                </Badge>
                <span className="font-bold text-slate-100">CASE: {activeCase.caseId}</span>
                <span className="text-slate-400">|</span>
                <span className="text-slate-300">TARGET: {formatAddress(activeCase.target)}</span>
                <span className="text-cyber-primary font-bold">[{activeCase.network}]</span>
              </div>

              <div className="flex items-center gap-4 text-slate-400">
                <span>
                  TAINT: <strong className="text-red-400">${activeCase.summary.taintedVolumeUSD.toLocaleString()}</strong>
                </span>
                <span>
                  DEPTH: <strong className="text-white">{activeCase.maxHops} Hops</strong>
                </span>
              </div>
            </div>

            {/* Split Screen: Cytoscape Graph + Wallet Detail Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[680px]">
              <div className={selectedNode ? "lg:col-span-2 h-full" : "lg:col-span-3 h-full"}>
                <CytoscapeGraph
                  nodes={activeCase.nodes}
                  edges={activeCase.edges}
                  selectedNodeId={selectedNode?.id}
                  onSelectNode={(node) => setSelectedNode(node)}
                  onSelectEdge={(edge) => setSelectedEdge(edge)}
                  className="h-full"
                />
              </div>

              {/* Side Wallet Intelligence Panel when node selected */}
              {selectedNode && (
                <div className="lg:col-span-1 h-full rounded-lg overflow-hidden shadow-2xl border border-cyber-border">
                  <WalletDetailPanel
                    node={selectedNode}
                    allEdges={activeCase.edges}
                    allFindings={activeCase.findings}
                    allEvidence={activeCase.evidence}
                    onClose={() => setSelectedNode(null)}
                    onExploreMore={(address) => handleSelectWallet(address)}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: Wallet Intelligence View (Full Screen) */}
        {activeTab === "wallet" && (
          <div className="space-y-4">
            <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg flex items-center justify-between font-mono text-xs">
              <span className="font-bold text-slate-200">
                WALLET INTELLIGENCE DIRECTORY ({activeCase.nodes.length} WALLETS ANALYSED)
              </span>
              <span className="text-slate-400">CASE: {activeCase.caseId}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeCase.nodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => {
                    setSelectedNode(node);
                    setActiveTab("trace");
                  }}
                  className="p-4 bg-cyber-surface border border-cyber-border hover:border-cyber-primary rounded-lg cursor-pointer transition-all space-y-3 font-mono text-xs"
                >
                  <div className="flex justify-between items-start">
                    <Badge variant={node.isInputTarget ? "demo" : node.riskScore >= 90 ? "critical" : "info"}>
                      {node.type.toUpperCase()}
                    </Badge>
                    <span className="font-bold text-cyber-primary">HOP {node.hop}</span>
                  </div>

                  <div>
                    <div className="font-bold text-slate-100 truncate">{node.label}</div>
                    <div className="text-[11px] text-slate-400 break-all">{node.address || node.id}</div>
                  </div>

                  {node.entityName && (
                    <div className="text-[11px] text-amber-400 truncate">
                      ENTITY: {node.entityName}
                    </div>
                  )}

                  <div className="pt-2 border-t border-cyber-border flex justify-between items-center text-[11px]">
                    <span className="text-slate-400">RISK: {node.riskScore}/100</span>
                    <span className="text-cyber-primary font-semibold hover:underline">
                      INSPECT IN GRAPH →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: Suspicious Activity Findings Dashboard */}
        {activeTab === "findings" && (
          <SuspiciousFindingsView
            findings={activeCase.findings}
            onSelectWallet={handleSelectWallet}
          />
        )}

        {/* TAB 5: Receiver Intelligence */}
        {activeTab === "receivers" && (
          <ReceiverIntelligenceView
            receivers={activeCase.receivers}
            network={activeCase.network}
            onSelectCandidate={handleSelectWallet}
          />
        )}

        {/* TAB 6: Chronological Timeline */}
        {activeTab === "timeline" && (
          <InvestigationTimelineView timeline={activeCase.timeline} />
        )}

        {/* TAB 7: Evidence Vault & Tamper-Evident Audit Verification */}
        {activeTab === "evidence" && (
          <EvidenceVaultView
            evidence={activeCase.evidence}
            auditLogs={activeCase.auditLogs}
            caseId={activeCase.caseId}
          />
        )}

        {/* TAB 8: New Investigation Form */}
        {activeTab === "new" && (
          <NewInvestigationForm onInvestigationCreated={handleInvestigationCreated} />
        )}
      </main>

      {/* TraceAI Copilot Slide-over Drawer */}
      <TraceAICopilotPanel
        investigation={activeCase}
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSelectEvidence={(evId) => setActiveTab("evidence")}
        onSelectFinding={(fId) => setActiveTab("findings")}
      />

      {/* Forensic Report Modal / Print View */}
      <InvestigationReportModal
        investigation={activeCase}
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
      />
    </div>
  );
}
