"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, ArrowRight } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { CopyAddressButton } from "@/components/common/CopyAddressButton";
import { EmptyState } from "@/components/common/States";
import { useForensic } from "@/context/ForensicContext";
import { NewInvestigationForm } from "@/features/investigations/NewInvestigationForm";
import {
  formatTimestamp,
  truncateAddress,
  cn,
  getCaseRiskScore,
} from "@/lib/utils";
import { InvestigationCase } from "@/types/investigation";

export default function InvestigationsPage() {
  const router = useRouter();
  const {
    allCases,
    networkFilter,
    globalSearch,
    selectCase,
    addOrActivateCase,
    addToast,
  } = useForensic();

  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [showNewModal, setShowNewModal] = useState(false);

  const effectiveQuery = (query || globalSearch).trim().toLowerCase();

  const cases = useMemo(() => {
    return allCases
      .filter((c) => (networkFilter === "ALL" ? true : c.network === networkFilter))
      .filter((c) => (statusFilter === "ALL" ? true : c.status === statusFilter))
      .filter((c) => {
        if (!effectiveQuery) return true;
        return (
          c.caseId.toLowerCase().includes(effectiveQuery) ||
          c.title.toLowerCase().includes(effectiveQuery) ||
          c.target.toLowerCase().includes(effectiveQuery)
        );
      });
  }, [allCases, networkFilter, statusFilter, effectiveQuery]);

  const handleCreated = (created: InvestigationCase) => {
    addOrActivateCase(created);
    setShowNewModal(false);
    addToast({
      title: "Case Created",
      description: `${created.caseId} added to active repository.`,
      variant: "success",
    });
    router.push(`/investigations/${created.caseId}`);
  };

  return (
    <SocShell
      title="Investigations Repository"
      subtitle="Manage multi-hop blockchain tracing cases across Ethereum & Bitcoin"
      actions={
        <button
          type="button"
          onClick={() => setShowNewModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase tracking-wider hover:bg-[#33ECFF] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Investigation
        </button>
      }
    >
      {/* Filters Bar */}
      <div className="rounded border border-white/[0.08] bg-[#0E1217] p-4 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 text-[#8A929E] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Case ID, wallet address, or title..."
            className="w-full h-9 pl-9 pr-3 rounded bg-[#07090C] border border-white/[0.08] text-xs font-mono text-[#F5F7FA] placeholder:text-[#8A929E]/60 focus:outline-none focus:border-[#00E5FF]/50"
          />
        </div>

        <div className="flex items-center gap-2">
          {(["ALL", "ACTIVE", "PENDING_REVIEW", "ARCHIVED"] as const).map(
            (status) => (
              <button
                key={status}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={cn(
                  "px-2.5 py-1.5 rounded text-[11px] font-mono uppercase border transition-colors",
                  statusFilter === status
                    ? "bg-[#00E5FF]/15 border-[#00E5FF]/40 text-[#00E5FF]"
                    : "bg-[#07090C] border-white/[0.08] text-[#8A929E] hover:text-[#F5F7FA]"
                )}
              >
                {status}
              </button>
            )
          )}
        </div>
      </div>

      {/* Cases Table */}
      {cases.length === 0 ? (
        <EmptyState
          title="No matching investigations"
          description="Adjust your search query or launch a new forensic trace."
          action={
            <button
              type="button"
              onClick={() => setShowNewModal(true)}
              className="px-4 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase"
            >
              Create Investigation
            </button>
          }
        />
      ) : (
        <div className="rounded border border-white/[0.08] bg-[#0E1217] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] bg-[#0A0D12] text-[11px] font-mono uppercase tracking-wider text-[#8A929E]">
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Investigation Title</th>
                  <th className="py-3 px-4">Chain</th>
                  <th className="py-3 px-4">Target Wallet</th>
                  <th className="py-3 px-4">Risk Index</th>
                  <th className="py-3 px-4">Findings</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Updated</th>
                  <th className="py-3 px-4 text-right">Open</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-xs">
                {cases.map((c) => {
                  const risk = getCaseRiskScore(c);
                  return (
                    <tr
                      key={c.caseId}
                      className="hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono text-[#00E5FF]">
                        {c.caseId}
                      </td>
                      <td className="py-3.5 px-4">
                        <p className="font-medium text-[#F5F7FA]">{c.title}</p>
                        <p className="text-[11px] text-[#8A929E]">
                          {c.summary.walletsCount} wallets · $
                          {c.summary.totalVolumeUSD.toLocaleString()}
                        </p>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[#8A929E]">
                        {c.network}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 font-mono text-[#8A929E]">
                          <span>{truncateAddress(c.target, 6, 4)}</span>
                          <CopyAddressButton value={c.target} />
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        <span
                          className={cn(
                            risk >= 80
                              ? "text-[#EF4444]"
                              : risk >= 60
                              ? "text-[#F97316]"
                              : "text-[#F59E0B]"
                          )}
                        >
                          [ {risk} / 100 ]
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[#F5F7FA]">
                        {c.findings.length}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/[0.1] text-[#F5F7FA]">
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-[#8A929E]">
                        {formatTimestamp(c.updatedAt)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            selectCase(c.caseId);
                            router.push(`/investigations/${c.caseId}`);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded border border-[#00E5FF]/30 bg-[#00E5FF]/10 text-[#00E5FF] text-[11px] font-mono hover:bg-[#00E5FF]/20 transition-colors"
                        >
                          Open <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded border border-white/[0.12] bg-[#0E1217] p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-[#F5F7FA]">
                Launch New Forensic Investigation
              </h2>
              <button
                type="button"
                onClick={() => setShowNewModal(false)}
                className="text-xs font-mono text-[#8A929E] hover:text-[#F5F7FA]"
              >
                [ CLOSE ]
              </button>
            </div>
            <NewInvestigationForm onInvestigationCreated={handleCreated} />
          </div>
        </div>
      )}
    </SocShell>
  );
}
