"use client";

import React, { useState, useMemo } from "react";
import { SuspiciousFinding, FindingSeverity, FindingCategory, FindingStatus } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { formatAddress, formatCurrency, formatTimestamp, cn } from "@/lib/utils";
import {
  AlertTriangle,
  ShieldAlert,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  FileCheck,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

interface SuspiciousFindingsViewProps {
  findings: SuspiciousFinding[];
  onSelectFinding?: (finding: SuspiciousFinding) => void;
  onSelectWallet?: (address: string) => void;
}

export function SuspiciousFindingsView({
  findings,
  onSelectFinding,
  onSelectWallet,
}: SuspiciousFindingsViewProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const categories = useMemo(() => {
    const set = new Set(findings.map((f) => f.category));
    return Array.from(set);
  }, [findings]);

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (selectedSeverity !== "ALL" && f.severity !== selectedSeverity) return false;
      if (selectedCategory !== "ALL" && f.category !== selectedCategory) return false;
      if (selectedStatus !== "ALL" && f.status !== selectedStatus) return false;
      return true;
    });
  }, [findings, selectedSeverity, selectedCategory, selectedStatus]);

  return (
    <div className="space-y-4">
      {/* Filters Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-cyber-surface border border-cyber-border rounded-lg text-xs font-mono">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <span>FILTER BY:</span>
          </div>

          {/* Severity filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-cyber-card border border-cyber-border text-slate-200 rounded px-2.5 py-1 focus:outline-none focus:border-cyber-primary"
          >
            <option value="ALL">ALL SEVERITIES</option>
            <option value="CRITICAL">CRITICAL ONLY</option>
            <option value="HIGH">HIGH ONLY</option>
            <option value="MEDIUM">MEDIUM ONLY</option>
            <option value="LOW">LOW ONLY</option>
          </select>

          {/* Category filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-cyber-card border border-cyber-border text-slate-200 rounded px-2.5 py-1 focus:outline-none focus:border-cyber-primary"
          >
            <option value="ALL">ALL CATEGORIES</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.replace(/_/g, " ")}
              </option>
            ))}
          </select>

          {/* Status filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-cyber-card border border-cyber-border text-slate-200 rounded px-2.5 py-1 focus:outline-none focus:border-cyber-primary"
          >
            <option value="ALL">ALL STATUSES</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="TRIAGED">TRIAGED</option>
            <option value="DISMISSED">DISMISSED</option>
          </select>
        </div>

        <div className="text-slate-400 font-mono text-xs">
          SHOWING <strong className="text-white">{filteredFindings.length}</strong> OF {findings.length} FINDINGS
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3">
        {filteredFindings.map((finding) => {
          const isExpanded = expandedId === finding.id;

          return (
            <div
              key={finding.id}
              className={cn(
                "bg-cyber-surface border rounded-lg transition-all duration-150 overflow-hidden",
                finding.severity === "CRITICAL"
                  ? "border-red-500/30 hover:border-red-500/50"
                  : finding.severity === "HIGH"
                  ? "border-orange-500/30 hover:border-orange-500/50"
                  : "border-cyber-border hover:border-cyber-border-light"
              )}
            >
              {/* Finding Summary Bar */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : finding.id)}
                className="p-4 cursor-pointer flex items-start justify-between gap-4 hover:bg-cyber-card-hover/40 transition-colors"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div
                    className={cn(
                      "p-2 rounded mt-0.5 shrink-0",
                      finding.severity === "CRITICAL"
                        ? "bg-red-500/10 text-red-400"
                        : finding.severity === "HIGH"
                        ? "bg-orange-500/10 text-orange-400"
                        : "bg-amber-500/10 text-amber-400"
                    )}
                  >
                    <AlertTriangle className="w-4 h-4" />
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-cyber-primary font-bold">{finding.id}</span>
                      <Badge
                        variant={
                          finding.severity === "CRITICAL"
                            ? "critical"
                            : finding.severity === "HIGH"
                            ? "high"
                            : "medium"
                        }
                      >
                        {finding.severity}
                      </Badge>
                      <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                        CONFIDENCE: {finding.confidence}%
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        STATUS: <strong className="text-slate-200">{finding.status}</strong>
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100 tracking-wide">{finding.title}</h4>

                    <div className="flex flex-wrap items-center gap-4 mt-2 text-xs font-mono text-slate-400">
                      <span>
                        AFFECTED:{" "}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onSelectWallet) onSelectWallet(finding.affectedWallet);
                          }}
                          className="text-cyber-primary hover:underline"
                        >
                          {formatAddress(finding.affectedWallet)}
                        </button>
                      </span>
                      <span>
                        EXPOSURE:{" "}
                        <strong className="text-slate-200">
                          {finding.amountInvolved.toLocaleString()} {finding.currency} (~${finding.amountUSD.toLocaleString()})
                        </strong>
                      </span>
                      <span>DETECTED: {formatTimestamp(finding.detectedAt)}</span>
                    </div>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  <ChevronRight
                    className={cn("w-4 h-4 text-slate-400 transition-transform duration-200", {
                      "rotate-90 text-white": isExpanded,
                    })}
                  />
                </div>
              </div>

              {/* Expanded Detail Panel */}
              {isExpanded && (
                <div className="px-5 pb-5 pt-2 border-t border-cyber-border bg-[#090e18]/90 space-y-4 text-xs font-mono">
                  {/* Detailed Explanation */}
                  <div className="space-y-1">
                    <span className="text-slate-400 text-[11px] font-semibold tracking-wider">
                      FORENSIC DETAILED EXPLANATION:
                    </span>
                    <p className="text-slate-200 font-sans leading-relaxed text-sm bg-cyber-card p-3 rounded border border-cyber-border">
                      {finding.explanation}
                    </p>
                  </div>

                  {/* Limitations and Caveats */}
                  <div className="space-y-1">
                    <span className="text-amber-400 text-[11px] font-semibold tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      HEURISTIC LIMITATIONS & DEFENSIVE CAVEATS:
                    </span>
                    <p className="text-slate-300 font-sans leading-relaxed text-xs bg-amber-950/20 p-3 rounded border border-amber-500/30">
                      {finding.limitations}
                    </p>
                  </div>

                  {/* Detection Rule Specification */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300">
                    <div className="bg-cyber-card p-3 rounded border border-cyber-border space-y-1">
                      <span className="text-slate-400 text-[10px] block">SECURITY DETECTION RULE:</span>
                      <div className="font-bold text-cyber-primary text-sm">{finding.detectionRuleId}</div>
                      <div className="text-[11px] text-slate-400">ENGINE VERSION: {finding.detectionRuleVersion}</div>
                    </div>

                    <div className="bg-cyber-card p-3 rounded border border-cyber-border space-y-1">
                      <span className="text-slate-400 text-[10px] block">SUPPORTING EVIDENCE VAULT IDS:</span>
                      <div className="flex flex-wrap gap-1.5 pt-0.5">
                        {finding.evidenceReferences.map((evId) => (
                          <Badge key={evId} variant="verified">
                            {evId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredFindings.length === 0 && (
          <div className="p-12 text-center text-slate-500 font-mono text-xs border border-dashed border-cyber-border rounded-lg">
            No suspicious findings matched the current filter criteria.
          </div>
        )}
      </div>
    </div>
  );
}
