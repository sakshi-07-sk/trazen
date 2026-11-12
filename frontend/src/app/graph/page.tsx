"use client";

import React, { useMemo, useState } from "react";
import { Network } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { WalletDetailPanel } from "@/features/wallets/WalletDetailPanel";
import { useForensic } from "@/context/ForensicContext";
import { GraphNode } from "@/types/investigation";

export default function GraphExplorerPage() {
  const { allCases, activeCase, selectCase } = useForensic();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const inspectedNode = useMemo(() => {
    if (selectedNode && activeCase.nodes.some((n) => n.id === selectedNode.id)) {
      return selectedNode;
    }
    return activeCase.nodes[0] || null;
  }, [selectedNode, activeCase]);

  const handleExploreMore = (address: string) => {
    const match = activeCase.nodes.find(
      (n) => (n.address || "").toLowerCase() === address.toLowerCase()
    );
    if (match) setSelectedNode(match);
  };

  return (
    <SocShell
      title="Interactive Graph Explorer"
      subtitle={`Multi-hop transaction topology for ${activeCase.caseId} (${activeCase.network})`}
      actions={
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-[#00E5FF]" />
          <select
            value={activeCase.caseId}
            onChange={(e) => {
              selectCase(e.target.value);
              setSelectedNode(null);
            }}
            className="h-9 px-3 rounded bg-[#0E1217] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
            aria-label="Select investigation case"
          >
            {allCases.map((c) => (
              <option key={c.caseId} value={c.caseId}>
                {c.caseId} · {c.network} · {c.title}
              </option>
            ))}
          </select>
        </div>
      }
    >
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-8">
          <CytoscapeGraph
            nodes={activeCase.nodes}
            edges={activeCase.edges}
            selectedNodeId={inspectedNode?.id}
            onSelectNode={(n) => setSelectedNode(n)}
            className="h-[680px]"
          />
        </div>
        <div className="xl:col-span-4">
          {inspectedNode && (
            <WalletDetailPanel
              node={inspectedNode}
              allEdges={activeCase.edges}
              allFindings={activeCase.findings}
              allEvidence={activeCase.evidence}
              onExploreMore={handleExploreMore}
            />
          )}
        </div>
      </div>
    </SocShell>
  );
}
