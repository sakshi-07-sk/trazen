"use client";

import React from "react";
import { InvestigationCase } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { formatAddress } from "@/lib/utils";
import {
  ShieldCheck,
  Search,
  Bot,
  FileText,
  Activity,
  Layers,
  Share2,
  AlertTriangle,
  Target,
  Clock,
  Lock,
} from "lucide-react";

export type ActiveTab =
  | "command"
  | "trace"
  | "wallet"
  | "findings"
  | "receivers"
  | "timeline"
  | "evidence"
  | "new";

interface AppNavbarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  activeCase: InvestigationCase;
  allCases: InvestigationCase[];
  onSelectCase: (caseId: string) => void;
  onOpenCopilot: () => void;
  onOpenReport: () => void;
  isCopilotOpen: boolean;
}

export function AppNavbar({
  activeTab,
  onSelectTab,
  activeCase,
  allCases,
  onSelectCase,
  onOpenCopilot,
  onOpenReport,
  isCopilotOpen,
}: AppNavbarProps) {
  return (
    <header className="bg-[#070b14] border-b border-cyber-border sticky top-0 z-40 select-none">
      {/* Top Bar: Brand, Case Selector, Actions */}
      <div className="px-4 py-2.5 flex flex-wrap items-center justify-between gap-4 border-b border-cyber-border/60">
        {/* Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => onSelectTab("command")}>
            <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white font-mono font-bold shadow-glow text-sm">
              CT
            </div>
            <div>
              <span className="font-mono text-sm font-bold tracking-widest text-slate-100 flex items-center gap-1.5">
                CRYPTOTRACE
                <span className="text-[10px] text-cyber-primary bg-cyber-primary/15 border border-cyber-primary/30 px-1 rounded">
                  FORENSIC SOC
                </span>
              </span>
              <span className="text-[10px] text-slate-400 block font-mono">
                BLOCKCHAIN INVESTIGATION COMMAND CENTER
              </span>
            </div>
          </div>

          <div className="hidden lg:block h-5 w-px bg-cyber-border mx-2" />

          {/* Active Case Selector Dropdown */}
          <div className="hidden sm:flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">ACTIVE CASE:</span>
            <select
              value={activeCase.caseId}
              onChange={(e) => onSelectCase(e.target.value)}
              className="bg-cyber-surface border border-cyber-border text-slate-100 rounded px-2.5 py-1 text-xs font-mono focus:outline-none focus:border-cyber-primary cursor-pointer hover:border-slate-500"
            >
              {allCases.map((c) => (
                <option key={c.caseId} value={c.caseId}>
                  {c.caseId} [{c.network}] — {c.title.substring(0, 32)}...
                </option>
              ))}
            </select>
            {activeCase.isDemo && <Badge variant="demo">DEMO DATA</Badge>}
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant={activeTab === "new" ? "primary" : "secondary"}
            size="sm"
            icon={<Search className="w-3.5 h-3.5" />}
            onClick={() => onSelectTab("new")}
          >
            NEW INVESTIGATION
          </Button>

          <Button
            variant={isCopilotOpen ? "primary" : "secondary"}
            size="sm"
            icon={<Bot className="w-3.5 h-3.5 text-cyber-primary" />}
            onClick={onOpenCopilot}
          >
            TraceAI COPILOT
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={<FileText className="w-3.5 h-3.5" />}
            onClick={onOpenReport}
          >
            DOSSIER REPORT
          </Button>
        </div>
      </div>

      {/* Bottom Sub-Navigation Tabs */}
      <div className="px-4 flex items-center gap-1 overflow-x-auto text-xs font-mono bg-cyber-bg/90">
        {(
          [
            ["command", "COMMAND CENTER", Activity],
            ["trace", "INTERACTIVE TRACE GRAPH", Share2],
            ["wallet", "WALLET INTELLIGENCE", Layers],
            ["findings", `SUSPICIOUS FINDINGS (${activeCase.findings.length})`, AlertTriangle],
            ["receivers", `RECEIVER INTELLIGENCE (${activeCase.receivers.length})`, Target],
            ["timeline", `TIMELINE (${activeCase.timeline.length})`, Clock],
            ["evidence", `EVIDENCE VAULT (${activeCase.evidence.length})`, Lock],
          ] as const
        ).map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => onSelectTab(key as ActiveTab)}
            className={`flex items-center gap-2 px-3 py-2 border-b-2 font-medium transition-colors shrink-0 ${
              activeTab === key
                ? "border-cyber-primary text-cyber-primary bg-cyber-primary/5 font-bold"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </header>
  );
}
