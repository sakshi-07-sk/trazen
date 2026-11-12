"use client";

import React, { useState } from "react";
import { GraphNode, GraphEdge, SuspiciousFinding, EvidenceVaultItem } from "@/types/investigation";
import { formatAddress, formatCurrency, formatTimestamp, cn } from "@/lib/utils";
import { RiskMeter } from "@/components/common/RiskMeter";
import { Badge } from "@/components/common/Badge";
import {
  ShieldAlert,
  ExternalLink,
  Copy,
  Check,
  ArrowDownLeft,
  ArrowUpRight,
  Database,
  Tag,
  AlertTriangle,
  FileText,
  Clock,
  Layers,
} from "lucide-react";

interface WalletDetailPanelProps {
  node: GraphNode;
  allEdges: GraphEdge[];
  allFindings: SuspiciousFinding[];
  allEvidence: EvidenceVaultItem[];
  onClose?: () => void;
  onExploreMore?: (address: string) => void;
}

export function WalletDetailPanel({
  node,
  allEdges,
  allFindings,
  allEvidence,
  onClose,
  onExploreMore,
}: WalletDetailPanelProps) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "flows" | "findings" | "evidence">("overview");

  const address = node.address || node.id;

  const handleCopy = () => {
    if (address) {
      navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Compute incoming and outgoing edges for this node
  const incomingEdges = allEdges.filter((e) => e.target === node.id);
  const outgoingEdges = allEdges.filter((e) => e.source === node.id);

  // Compute findings related to this wallet
  const nodeFindings = allFindings.filter(
    (f) =>
      f.affectedWallet.toLowerCase() === address.toLowerCase() ||
      (node.isInputTarget && f.affectedWallet.toLowerCase() === node.id.toLowerCase())
  );

  // Evidence matching node findings
  const evidenceIds = new Set(nodeFindings.flatMap((f) => f.evidenceReferences));
  const nodeEvidence = allEvidence.filter((e) => evidenceIds.has(e.id));

  const totalIn = incomingEdges.reduce((sum, e) => sum + e.amount, 0);
  const totalOut = outgoingEdges.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="flex flex-col h-full bg-cyber-surface border-l border-cyber-border text-slate-200">
      {/* Header */}
      <div className="p-4 border-b border-cyber-border bg-[#090e18]/80 flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={node.isInputTarget ? "demo" : node.riskScore >= 90 ? "critical" : "info"}>
              {node.isInputTarget ? "TARGET WALLET" : `${node.type.toUpperCase()}`}
            </Badge>
            <span className="text-[11px] font-mono text-slate-400">HOP {node.hop}</span>
            <span className="text-[11px] font-mono text-cyber-primary">{node.network}</span>
          </div>

          <div className="flex items-center gap-2 group">
            <span className="font-mono text-xs font-semibold text-slate-100 break-all select-all">
              {address}
            </span>
            <button
              onClick={handleCopy}
              className="text-slate-400 hover:text-slate-200 shrink-0 p-1 rounded hover:bg-slate-800 transition-colors"
              title="Copy Address"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>

          {node.entityName && (
            <div className="mt-2 text-xs font-mono text-amber-400 flex items-center gap-1.5">
              <Tag className="w-3 h-3 shrink-0" />
              <span>{node.entityName}</span>
            </div>
          )}
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 p-1 text-sm font-mono"
            title="Close Panel"
          >
            ×
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-cyber-border text-xs font-mono bg-cyber-bg/50">
        {(
          [
            ["overview", "OVERVIEW"],
            ["flows", `FLOWS (${incomingEdges.length + outgoingEdges.length})`],
            ["findings", `FINDINGS (${nodeFindings.length})`],
            ["evidence", `EVIDENCE (${nodeEvidence.length})`],
          ] as const
        ).map(([tabKey, label]) => (
          <button
            key={tabKey}
            onClick={() => setActiveTab(tabKey)}
            className={cn(
              "px-3 py-2 border-b-2 transition-colors flex-1 text-center font-medium",
              activeTab === tabKey
                ? "border-cyber-primary text-cyber-primary bg-cyber-primary/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === "overview" && (
          <div className="space-y-4">
            {/* Threat Meter */}
            <div className="bg-cyber-card p-3 rounded border border-cyber-border">
              <RiskMeter score={node.riskScore} />
            </div>

            {/* Direct Observations vs Inferred Relationships Warning */}
            <div className="p-3 bg-blue-950/20 border border-blue-500/30 rounded text-xs space-y-1.5">
              <div className="flex items-center gap-1.5 text-blue-400 font-semibold font-mono">
                <Database className="w-3.5 h-3.5" />
                <span>DATA PROVENANCE & OBSERVABILITY</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                <strong className="text-white">Direct On-Chain Observations:</strong> Account state, transaction balance, nonces, and timestamp receipts directly verified via consensus node RPC.
              </p>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                <strong className="text-white">Inferred Cluster Logic:</strong> Entity label <em className="text-amber-300 font-mono">&ldquo;{node.entityName || "Unknown"}&rdquo;</em> derived from: {node.entityProvenance || "Automated heuristics"}.
              </p>
            </div>

            {/* Wallet Activity Metrics */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="bg-cyber-card p-2.5 rounded border border-cyber-border">
                <span className="text-slate-400 text-[10px] block">CURRENT BALANCE</span>
                <span className="text-slate-100 font-bold text-sm">
                  {node.balance !== undefined ? `${node.balance.toLocaleString()} ${node.network}` : "N/A"}
                </span>
              </div>
              <div className="bg-cyber-card p-2.5 rounded border border-cyber-border">
                <span className="text-slate-400 text-[10px] block">LIFETIME TRANSACTIONS</span>
                <span className="text-slate-100 font-bold text-sm">{node.txCount || "N/A"}</span>
              </div>
              <div className="bg-cyber-card p-2.5 rounded border border-cyber-border">
                <span className="text-slate-400 text-[10px] block">TOTAL INGRESS</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {node.totalReceived !== undefined ? `${node.totalReceived.toLocaleString()} ${node.network}` : `${totalIn} ${node.network}`}
                </span>
              </div>
              <div className="bg-cyber-card p-2.5 rounded border border-cyber-border">
                <span className="text-slate-400 text-[10px] block">TOTAL EGRESS</span>
                <span className="text-rose-400 font-bold text-sm">
                  {node.totalSent !== undefined ? `${node.totalSent.toLocaleString()} ${node.network}` : `${totalOut} ${node.network}`}
                </span>
              </div>
            </div>

            {/* Activity Timestamps */}
            <div className="bg-cyber-card p-3 rounded border border-cyber-border text-xs space-y-2 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">FIRST OBSERVED:</span>
                <span className="text-slate-200">{node.firstSeen ? formatTimestamp(node.firstSeen) : "Recent Ingestion"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">LAST ACTIVE:</span>
                <span className="text-slate-200">{node.lastSeen ? formatTimestamp(node.lastSeen) : "Recent Ingestion"}</span>
              </div>
            </div>

            {/* Action buttons */}
            {onExploreMore && (
              <button
                onClick={() => onExploreMore(address)}
                className="w-full py-2 px-3 bg-cyber-primary hover:bg-blue-600 text-white rounded font-mono text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-glow"
              >
                <span>PIVOT INVESTIGATION TO THIS WALLET</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {activeTab === "flows" && (
          <div className="space-y-3 font-mono text-xs">
            <h4 className="text-slate-400 text-[11px] font-semibold tracking-wider">
              DIRECT INGESTED CONNECTIONS ({incomingEdges.length} IN / {outgoingEdges.length} OUT)
            </h4>

            {incomingEdges.length > 0 && (
              <div className="space-y-2">
                <span className="text-emerald-400 text-[11px] flex items-center gap-1">
                  <ArrowDownLeft className="w-3.5 h-3.5" /> INCOMING FLOWS
                </span>
                {incomingEdges.map((e) => (
                  <div key={e.id} className="p-2.5 bg-cyber-card border border-cyber-border rounded space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400 font-mono">FROM: {formatAddress(e.source)}</span>
                      <span className="text-emerald-400 font-bold">{e.amount} {e.currency}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 flex justify-between">
                      <span>TYPE: {e.relationshipType}</span>
                      <span>CONF: {e.confidence}%</span>
                    </div>
                    <div className="text-[10px] text-slate-500 truncate">TX: {e.txHash}</div>
                  </div>
                ))}
              </div>
            )}

            {outgoingEdges.length > 0 && (
              <div className="space-y-2">
                <span className="text-rose-400 text-[11px] flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5" /> OUTGOING FLOWS
                </span>
                {outgoingEdges.map((e) => (
                  <div key={e.id} className="p-2.5 bg-cyber-card border border-cyber-border rounded space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400 font-mono">TO: {formatAddress(e.target)}</span>
                      <span className="text-rose-400 font-bold">{e.amount} {e.currency}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 flex justify-between">
                      <span>TYPE: {e.relationshipType}</span>
                      <span>CONF: {e.confidence}%</span>
                    </div>
                    {e.heuristicExplanation && (
                      <div className="text-[10px] text-amber-400/90 italic">
                        {e.heuristicExplanation}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-500 truncate">TX: {e.txHash}</div>
                  </div>
                ))}
              </div>
            )}

            {incomingEdges.length === 0 && outgoingEdges.length === 0 && (
              <p className="text-slate-500 text-center py-4">No direct edges loaded for this entity.</p>
            )}
          </div>
        )}

        {activeTab === "findings" && (
          <div className="space-y-3">
            {nodeFindings.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs font-mono">
                No active suspicious findings flagged directly on this address.
              </div>
            ) : (
              nodeFindings.map((finding) => (
                <div
                  key={finding.id}
                  className="p-3 bg-cyber-card border border-red-500/30 rounded space-y-2 text-xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <span className="font-semibold text-slate-100">{finding.title}</span>
                    </div>
                    <Badge variant={finding.severity === "CRITICAL" ? "critical" : "high"}>
                      {finding.severity}
                    </Badge>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">{finding.explanation}</p>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 border-t border-cyber-border/60 pt-2">
                    <span>RULE: {finding.detectionRuleId}</span>
                    <span>CONFIDENCE: {finding.confidence}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "evidence" && (
          <div className="space-y-3">
            {nodeEvidence.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs font-mono">
                No cryptographic evidence records directly linked to this wallet.
              </div>
            ) : (
              nodeEvidence.map((ev) => (
                <div
                  key={ev.id}
                  className="p-3 bg-cyber-card border border-cyber-border rounded space-y-2 text-xs font-mono"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-cyber-primary font-bold">{ev.id}</span>
                    <Badge variant="verified">{ev.integrityStatus}</Badge>
                  </div>
                  <div className="text-[11px] text-slate-300">{ev.details}</div>
                  <div className="text-[10px] text-slate-400 space-y-0.5 border-t border-cyber-border/60 pt-2">
                    <div>BLOCK: #{ev.blockNumber.toLocaleString()}</div>
                    <div className="truncate">SOURCE: {ev.dataSource}</div>
                    <div className="truncate">RECORD HASH: {ev.recordHash}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
