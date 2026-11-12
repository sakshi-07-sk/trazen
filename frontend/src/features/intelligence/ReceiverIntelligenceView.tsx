"use client";

import React, { useState } from "react";
import { ReceiverCandidate, BlockchainNetwork } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { formatAddress, formatTimestamp, cn } from "@/lib/utils";
import {
  Target,
  ShieldCheck,
  AlertTriangle,
  Info,
  ExternalLink,
  Copy,
  Check,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface ReceiverIntelligenceViewProps {
  receivers: ReceiverCandidate[];
  network: BlockchainNetwork;
  onSelectCandidate?: (address: string) => void;
}

export function ReceiverIntelligenceView({
  receivers,
  network,
  onSelectCandidate,
}: ReceiverIntelligenceViewProps) {
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null);

  const handleCopy = (address: string) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(address);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Forensic Intelligence Disclaimer Banner */}
      <div className="p-3.5 bg-blue-950/20 border border-blue-500/30 rounded-lg flex items-start gap-3 text-xs">
        <Info className="w-4 h-4 text-cyber-primary shrink-0 mt-0.5" />
        <div className="space-y-1 text-slate-300">
          <div className="font-mono font-semibold text-slate-100 flex items-center gap-2">
            <span>FORENSIC ATTRIBUTION METHODOLOGY & RESTRAINT PRINCIPLE</span>
            <span className="text-[10px] text-cyber-primary px-1.5 py-0.5 bg-cyber-primary/10 rounded">
              STANDARD COMPLIANCE
            </span>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400">
            Public blockchain addresses represent cryptographic public-key hashes. Candidate receiver scoring calculates mathematical flow concentration and terminal clustering heuristics. <strong>CryptoTrace does not claim to identify the real-world legal person behind any unhosted address.</strong> Entity tags reflect on-chain protocol registries and formal sanction designations (e.g. OFAC SDN).
          </p>
        </div>
      </div>

      {/* Receiver Rankings Grid / List */}
      <div className="space-y-4">
        {receivers.map((candidate) => {
          const isCopied = copiedAddress === candidate.walletAddress;

          return (
            <div
              key={candidate.rank}
              className={cn(
                "bg-cyber-surface border rounded-lg p-5 transition-all duration-150 relative overflow-hidden",
                candidate.riskPriority === "CRITICAL"
                  ? "border-red-500/40 shadow-glow-rose"
                  : candidate.riskPriority === "HIGH"
                  ? "border-orange-500/30"
                  : "border-cyber-border"
              )}
            >
              {/* Top Row: Rank Badge, Address, Risk Score */}
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-cyber-border/70 pb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-8 h-8 rounded font-mono font-bold flex items-center justify-center text-sm shrink-0",
                      candidate.rank === 1
                        ? "bg-red-500 text-white shadow-lg"
                        : candidate.rank === 2
                        ? "bg-orange-500/80 text-white"
                        : "bg-slate-800 text-slate-300"
                    )}
                  >
                    #{candidate.rank}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-400">CANDIDATE DESTINATION:</span>
                      <span className="font-mono text-sm font-bold text-slate-100 select-all">
                        {candidate.walletAddress}
                      </span>
                      <button
                        onClick={() => handleCopy(candidate.walletAddress)}
                        className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition-colors"
                        title="Copy Address"
                      >
                        {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 mt-1.5">
                      <Badge
                        variant={
                          candidate.riskPriority === "CRITICAL"
                            ? "critical"
                            : candidate.riskPriority === "HIGH"
                            ? "high"
                            : "medium"
                        }
                      >
                        {candidate.riskPriority} RISK
                      </Badge>
                      {candidate.isService && (
                        <span className="text-[11px] font-mono text-amber-300 bg-amber-950/40 border border-amber-500/30 px-2 py-0.5 rounded">
                          SERVICE: {candidate.serviceLabel}
                        </span>
                      )}
                      <span className="text-[11px] font-mono text-slate-400">
                        NETWORK: <strong className="text-slate-200">{network}</strong>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Attribution Metrics Badges */}
                <div className="flex items-center gap-4 text-xs font-mono">
                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block">ATTRIBUTION CONFIDENCE</span>
                    <span className="text-cyber-primary font-bold text-base">
                      {candidate.attributionConfidence}%
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block">TRACE FLOW COVERAGE</span>
                    <span className="text-emerald-400 font-bold text-base">
                      {candidate.investigationCoverage}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Middle Section: Flow Exposure & Rationale */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-4 text-xs">
                {/* Flow volume & exposure */}
                <div className="bg-cyber-card p-3 rounded border border-cyber-border space-y-2 font-mono">
                  <span className="text-slate-400 text-[11px] font-semibold">IDENTIFIED FLOW EXPOSURE:</span>
                  <div className="text-base font-bold text-slate-100">
                    {candidate.amountReceived.toLocaleString()} {candidate.currency}{" "}
                    <span className="text-xs text-slate-400 font-normal">
                      (~${candidate.amountUSD.toLocaleString()} USD)
                    </span>
                  </div>
                  <div className="text-[11px] text-amber-400">
                    <strong>KNOWN RISK:</strong> {candidate.knownRiskExposure}
                  </div>
                </div>

                {/* Evidence references */}
                <div className="bg-cyber-card p-3 rounded border border-cyber-border space-y-2 font-mono">
                  <span className="text-slate-400 text-[11px] font-semibold">SUPPORTING EVIDENCE VAULT:</span>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {candidate.supportingEvidence.map((evId) => (
                      <Badge key={evId} variant="verified">
                        {evId}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Action button */}
                <div className="flex flex-col justify-center">
                  {onSelectCandidate && (
                    <button
                      onClick={() => onSelectCandidate(candidate.walletAddress)}
                      className="w-full py-2.5 px-3 bg-cyber-card hover:bg-cyber-card-hover border border-cyber-border hover:border-cyber-primary text-slate-200 hover:text-white rounded font-mono text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
                    >
                      <span>INSPECT WALLET IN GRAPH</span>
                      <ArrowRight className="w-3.5 h-3.5 text-cyber-primary" />
                    </button>
                  )}
                </div>
              </div>

              {/* Reasons for Ranking */}
              <div className="mt-4 pt-3 border-t border-cyber-border/60">
                <span className="text-slate-400 text-[11px] font-mono font-semibold block mb-2">
                  HEURISTIC RANKING RATIONALE:
                </span>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {candidate.reasonsForRanking.map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-cyber-primary shrink-0 mt-0.5">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
