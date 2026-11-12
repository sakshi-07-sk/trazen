"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Network } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EmptyState } from "@/components/common/States";
import { useForensic } from "@/context/ForensicContext";
import { SuspiciousFindingsView } from "@/features/findings/SuspiciousFindingsView";
import { cn } from "@/lib/utils";

const CATEGORIES = [
  { id: "ALL", label: "All Categories" },
  { id: "peel_chain", label: "Peel-Chain" },
  { id: "mixer_exposure", label: "Mixer Exposure" },
  { id: "structuring", label: "Structuring" },
  { id: "dormancy", label: "Wallet Dormancy" },
  { id: "cross_case", label: "Cross-Case Infrastructure" },
] as const;

export default function FindingsPage() {
  const router = useRouter();
  const { allCases, activeCase, selectCase } = useForensic();
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  const filteredFindings = useMemo(() => {
    return activeCase.findings.filter((f) => {
      const matchCat =
        categoryFilter === "ALL" ||
        f.category.toLowerCase().includes(categoryFilter.replace("_", " ")) ||
        f.category.toLowerCase() === categoryFilter;
      const matchSev =
        severityFilter === "ALL" || f.severity.toUpperCase() === severityFilter;
      return matchCat && matchSev;
    });
  }, [activeCase.findings, categoryFilter, severityFilter]);

  return (
    <SocShell
      title="Forensic Findings & Anomaly Intelligence"
      subtitle={`Deterministic pattern detections for ${activeCase.caseId} (${activeCase.network})`}
      actions={
        <div className="flex items-center gap-2">
          <select
            value={activeCase.caseId}
            onChange={(e) => selectCase(e.target.value)}
            className="h-9 px-3 rounded bg-[#0E1217] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
            aria-label="Select case for findings"
          >
            {allCases.map((c) => (
              <option key={c.caseId} value={c.caseId}>
                {c.caseId} · {c.network}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => router.push("/graph")}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase"
          >
            <Network className="w-3.5 h-3.5" />
            Highlight on Graph
          </button>
        </div>
      }
    >
      {/* Category & Severity Filter Bar */}
      <div className="rounded border border-white/[0.08] bg-[#0E1217] p-4 mb-6 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setCategoryFilter(cat.id)}
              className={cn(
                "px-3 py-1.5 rounded text-[11px] font-mono uppercase border transition-colors",
                categoryFilter === cat.id
                  ? "bg-[#00E5FF]/15 border-[#00E5FF]/40 text-[#00E5FF]"
                  : "bg-[#07090C] border-white/[0.08] text-[#8A929E] hover:text-[#F5F7FA]"
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5">
          {(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              className={cn(
                "px-2.5 py-1 rounded text-[11px] font-mono uppercase border transition-colors",
                severityFilter === sev
                  ? "bg-white/[0.1] border-white/[0.25] text-[#F5F7FA]"
                  : "bg-[#07090C] border-white/[0.08] text-[#8A929E]"
              )}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => {
          const count = activeCase.findings.filter((f) => f.severity === sev).length;
          return (
            <div
              key={sev}
              className="rounded border border-white/[0.08] bg-[#0E1217] p-3.5 flex items-center justify-between"
            >
              <SeverityBadge severity={sev} />
              <span className="text-lg font-mono font-bold text-[#F5F7FA]">
                [ {count} ]
              </span>
            </div>
          );
        })}
      </div>

      {filteredFindings.length === 0 ? (
        <EmptyState
          title="No findings match current filter"
          description="Try resetting the category or severity filter to view all forensic detections."
          action={
            <button
              type="button"
              onClick={() => {
                setCategoryFilter("ALL");
                setSeverityFilter("ALL");
              }}
              className="px-4 py-2 rounded border border-[#00E5FF]/40 text-xs font-mono text-[#00E5FF]"
            >
              Reset Filters
            </button>
          }
        />
      ) : (
        <SuspiciousFindingsView
          findings={filteredFindings}
          onSelectWallet={() => router.push("/graph")}
          onSelectFinding={() => router.push("/graph")}
        />
      )}
    </SocShell>
  );
}
