"use client";

import React from "react";
import { InvestigationStats, InvestigationCase } from "@/types/investigation";
import { RECENT_INVESTIGATIONS_LIST } from "@/lib/mockData";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { formatAddress, formatTimestamp, formatUSD } from "@/lib/utils";
import {
  ShieldAlert,
  Search,
  Activity,
  Layers,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Database,
  Radio,
  FileText,
  Clock,
  CheckCircle2,
} from "lucide-react";

interface CommandCenterViewProps {
  stats: InvestigationStats;
  onOpenCase: (caseId: string) => void;
  onNewInvestigation: () => void;
  onOpenTrace: (caseId: string) => void;
}

export function CommandCenterView({
  stats,
  onOpenCase,
  onNewInvestigation,
  onOpenTrace,
}: CommandCenterViewProps) {
  return (
    <div className="space-y-6">
      {/* Top SOC Status & Mode Indicator Banner */}
      <div className="p-4 bg-cyber-surface border border-cyber-border rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="w-3 h-3 rounded-full bg-emerald-400 block animate-ping" />
            <span className="w-3 h-3 rounded-full bg-emerald-500 block absolute inset-0" />
          </div>
          <div>
            <div className="flex items-center gap-2 font-mono text-xs font-bold text-slate-100">
              <span>CYBERTRACE FORENSIC COMMAND CENTER</span>
              <span className="text-slate-500">•</span>
              <span className="text-emerald-400">SOC READY</span>
              <Badge variant="demo">DEMO FORENSIC DATASET</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-sans">
              Consensus ingestion pipeline synced. Detection rules v4.2 active across Ethereum & Bitcoin.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            icon={<Search className="w-3.5 h-3.5" />}
            onClick={onNewInvestigation}
          >
            NEW INVESTIGATION
          </Button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">INVESTIGATIONS</span>
          <div className="text-2xl font-bold text-white">{stats.totalInvestigations}</div>
          <span className="text-[10px] text-cyber-primary">Active Cases</span>
        </div>

        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">WALLETS ANALYZED</span>
          <div className="text-2xl font-bold text-slate-100">{stats.walletsAnalysed.toLocaleString()}</div>
          <span className="text-[10px] text-emerald-400">+142 this week</span>
        </div>

        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">TRANSACTIONS TRACED</span>
          <div className="text-2xl font-bold text-slate-100">{stats.transactionsTraced.toLocaleString()}</div>
          <span className="text-[10px] text-blue-400">Multi-Hop Receipts</span>
        </div>

        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">SUSPICIOUS FINDINGS</span>
          <div className="text-2xl font-bold text-red-400">{stats.suspiciousFindings}</div>
          <span className="text-[10px] text-red-400 font-bold">Rule Anomaly Hits</span>
        </div>

        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">HIGH PRIORITY CASES</span>
          <div className="text-2xl font-bold text-amber-400">{stats.highPriorityCases}</div>
          <span className="text-[10px] text-amber-300">Requires Triage</span>
        </div>

        <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-1 font-mono">
          <span className="text-slate-400 text-[10px] block font-semibold">AUDIT CHAIN STATUS</span>
          <div className="text-base font-bold text-emerald-400 flex items-center gap-1.5 mt-1">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>SEALED</span>
          </div>
          <span className="text-[10px] text-slate-400">SHA-256 Ledger</span>
        </div>
      </div>

      {/* Main Split: Recent Investigations & Latest Threat Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Investigations Table (2 spans) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyber-primary" />
              RECENT FORENSIC INVESTIGATIONS
            </h3>
            <span className="text-xs font-mono text-slate-500">LIVE CASE REPOSITORY</span>
          </div>

          <div className="bg-cyber-surface border border-cyber-border rounded-xl overflow-hidden shadow-lg">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#090e18] text-slate-400 border-b border-cyber-border text-[11px]">
                <tr>
                  <th className="p-3">CASE ID & TITLE</th>
                  <th className="p-3">TARGET</th>
                  <th className="p-3">RISK</th>
                  <th className="p-3 text-right">EXPOSURE</th>
                  <th className="p-3 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-border/60">
                {RECENT_INVESTIGATIONS_LIST.map((item) => (
                  <tr
                    key={item.caseId}
                    onClick={() => onOpenCase(item.caseId)}
                    className="hover:bg-cyber-card-hover/50 cursor-pointer transition-colors"
                  >
                    <td className="p-3">
                      <div className="font-bold text-slate-100 flex items-center gap-1.5">
                        <span className="text-cyber-primary">{item.caseId}</span>
                        {item.isDemo && <Badge variant="demo">DEMO</Badge>}
                      </div>
                      <div className="text-[11px] text-slate-400 font-sans mt-0.5 truncate max-w-[240px]">
                        {item.title}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-slate-400 font-bold">{item.network}</span>
                        <code className="text-slate-300 font-mono text-[11px]">{formatAddress(item.target)}</code>
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge
                        variant={
                          item.riskLevel === "CRITICAL"
                            ? "critical"
                            : item.riskLevel === "HIGH"
                            ? "high"
                            : "medium"
                        }
                      >
                        {item.riskLevel}
                      </Badge>
                    </td>
                    <td className="p-3 text-right font-bold text-slate-200">
                      {formatUSD(item.volumeUSD)}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenTrace(item.caseId);
                        }}
                        className="px-2 py-1 bg-cyber-card hover:bg-cyber-primary hover:text-white text-cyber-primary border border-cyber-border rounded text-[11px] font-semibold transition-colors"
                      >
                        OPEN TRACE
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Latest Alerts & Forensics Feed (1 span) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              FORENSIC THREAT ALERTS
            </h3>
            <span className="text-[10px] font-mono text-slate-500">REAL-TIME ANOMALIES</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3.5 bg-cyber-surface border border-red-500/30 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-red-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                  OFAC SANCTION MATCH
                </span>
                <span className="text-[10px] text-slate-400">2 min ago</span>
              </div>
              <p className="text-slate-300 font-sans text-xs">
                Direct deterministic link detected between Lazarus associated cluster and Tornado Cash privacy pool.
              </p>
              <div className="text-[10px] text-slate-400 pt-1 border-t border-cyber-border/60 flex justify-between">
                <span>CASE: CT-CASE-2024-8841</span>
                <button
                  onClick={() => onOpenCase("CT-CASE-2024-8841")}
                  className="text-cyber-primary hover:underline"
                >
                  VIEW CASE →
                </button>
              </div>
            </div>

            <div className="p-3.5 bg-cyber-surface border border-orange-500/30 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-orange-400 font-bold">PEEL-CHAIN DETECTED</span>
                <span className="text-[10px] text-slate-400">14 min ago</span>
              </div>
              <p className="text-slate-300 font-sans text-xs">
                Systematic 45.0 BTC peel transaction identified on Bitcoin UTXO chain destined for CoinJoin coordinator.
              </p>
              <div className="text-[10px] text-slate-400 pt-1 border-t border-cyber-border/60 flex justify-between">
                <span>CASE: CT-CASE-2024-BTC-0428</span>
                <button
                  onClick={() => onOpenCase("CT-CASE-2024-BTC-0428")}
                  className="text-cyber-primary hover:underline"
                >
                  VIEW CASE →
                </button>
              </div>
            </div>

            <div className="p-3.5 bg-cyber-surface border border-cyber-border rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-violet-400 font-bold">CROSS-CHAIN BRIDGE RELAY</span>
                <span className="text-[10px] text-slate-400">1 hr ago</span>
              </div>
              <p className="text-slate-300 font-sans text-xs">
                Stargate router correlated transfer: 1,200 ETH deposited with counterpart claim on secondary EVM network.
              </p>
              <div className="text-[10px] text-slate-400 pt-1 border-t border-cyber-border/60">
                <span>STATUS: VERIFIED IN EVIDENCE VAULT</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
