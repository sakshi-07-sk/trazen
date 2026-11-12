"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  FolderKanban,
  Gauge,
  Plus,
  Search,
  ShieldCheck,
  TrendingUp,
  Layers,
} from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { CopyAddressButton } from "@/components/common/CopyAddressButton";
import { useForensic } from "@/context/ForensicContext";
import { NewInvestigationForm } from "@/features/investigations/NewInvestigationForm";
import {
  formatTimestamp,
  truncateAddress,
  cn,
  getCaseRiskScore,
} from "@/lib/utils";
import { InvestigationCase } from "@/types/investigation";

type SortField = "updatedAt" | "riskScore" | "totalVolumeUsd";

export default function DashboardPage() {
  const router = useRouter();
  const {
    allCases,
    activeCase,
    stats,
    networkFilter,
    globalSearch,
    selectCase,
    addOrActivateCase,
    addToast,
  } = useForensic();

  const [localSearch, setLocalSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<SortField>("updatedAt");
  const [showNewModal, setShowNewModal] = useState(false);

  const combinedSearch = (localSearch || globalSearch).trim().toLowerCase();

  const filteredCases = useMemo(() => {
    return allCases
      .filter((c) => (networkFilter === "ALL" ? true : c.network === networkFilter))
      .filter((c) => (statusFilter === "ALL" ? true : c.status === statusFilter))
      .filter((c) => {
        if (!combinedSearch) return true;
        return (
          c.caseId.toLowerCase().includes(combinedSearch) ||
          c.title.toLowerCase().includes(combinedSearch) ||
          c.target.toLowerCase().includes(combinedSearch)
        );
      })
      .sort((a, b) => {
        if (sortBy === "riskScore") return getCaseRiskScore(b) - getCaseRiskScore(a);
        if (sortBy === "totalVolumeUsd")
          return b.summary.totalVolumeUSD - a.summary.totalVolumeUSD;
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      });
  }, [allCases, networkFilter, statusFilter, combinedSearch, sortBy]);

  const severityCounts = useMemo(() => {
    const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    allCases.forEach((c) => {
      c.findings.forEach((f) => {
        if (f.severity in counts) {
          counts[f.severity as keyof typeof counts] += 1;
        }
      });
    });
    return counts;
  }, [allCases]);

  const totalFindings =
    severityCounts.CRITICAL +
    severityCounts.HIGH +
    severityCounts.MEDIUM +
    severityCounts.LOW;

  const recentAlerts = useMemo(() => {
    return allCases
      .flatMap((c) =>
        c.findings.map((f) => ({
          ...f,
          caseId: c.caseId,
          network: c.network,
        }))
      )
      .slice(0, 5);
  }, [allCases]);

  const topRiskWallets = useMemo(() => {
    return [...activeCase.nodes]
      .sort((a, b) => b.riskScore - a.riskScore)
      .slice(0, 5);
  }, [activeCase]);

  const totalTracedUsd = useMemo(
    () => allCases.reduce((acc, c) => acc + c.summary.totalVolumeUSD, 0),
    [allCases]
  );

  const networkBreakdown = useMemo(() => {
    const ethCount = allCases.filter((c) => c.network === "ETH").length;
    const btcCount = allCases.filter((c) => c.network === "BTC").length;
    const ethVol = allCases
      .filter((c) => c.network === "ETH")
      .reduce((acc, c) => acc + c.summary.totalVolumeUSD, 0);
    const btcVol = allCases
      .filter((c) => c.network === "BTC")
      .reduce((acc, c) => acc + c.summary.totalVolumeUSD, 0);
    return { ethCount, btcCount, ethVol, btcVol };
  }, [allCases]);

  const handleCreated = (created: InvestigationCase) => {
    addOrActivateCase(created);
    setShowNewModal(false);
    addToast({
      title: "Investigation Created",
      description: `${created.caseId} initialized and activated.`,
      variant: "success",
    });
    router.push(`/investigations/${created.caseId}`);
  };

  return (
    <SocShell
      title="Forensic Command Center"
      subtitle="Real-time threat intelligence, case telemetry & deterministic anomaly triage"
      actions={
        <button
          type="button"
          onClick={() => setShowNewModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-mono font-semibold uppercase tracking-[0.14em] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Investigation
        </button>
      }
    >
      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
          <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
            <span>Active Investigations</span>
            <FolderKanban className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <p
            className="mt-3 text-4xl font-bold text-[#F1EEE6] tracking-tight"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            [ <AnimatedCounter value={allCases.length} /> ]
          </p>
          <p className="mt-1.5 text-xs text-[#A6A39A]">
            {stats.totalInvestigations} total tracked
          </p>
        </div>

        <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
          <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
            <span>High-Priority Cases</span>
            <AlertTriangle className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <p
            className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            [ <AnimatedCounter value={stats.highPriorityCases} /> ]
          </p>
          <p className="mt-1.5 text-xs text-[#A6A39A]">
            {stats.walletsAnalysed} wallets analysed
          </p>
        </div>

        <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
          <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
            <span>Traced Volume</span>
            <TrendingUp className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <p
            className="mt-3 text-4xl font-bold text-[#F1EEE6] tracking-tight"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            $<AnimatedCounter value={Math.round(totalTracedUsd / 1000)} />K
          </p>
          <p className="mt-1.5 text-xs text-[#A6A39A]">
            Across ETH & BTC ledgers
          </p>
        </div>

        <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
          <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
            <span>Evidence Integrity</span>
            <ShieldCheck className="w-4 h-4 text-[#22C55E]" />
          </div>
          <p
            className="mt-3 text-4xl font-bold text-[#22C55E] tracking-tight"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            [ <AnimatedCounter value={activeCase.evidence.length} /> ]
          </p>
          <p className="mt-1.5 text-xs text-[#A6A39A]">
            SHA-256 hash-chained records
          </p>
        </div>
      </div>

      {/* Middle Grid: Severity Distribution + Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-6">
        <section className="lg:col-span-5 rounded-sm border border-white/10 bg-[#151616] p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
                ANOMALY TELEMETRY
              </p>
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mt-0.5"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Severity Distribution
              </h2>
            </div>
            <span className="text-xs font-mono text-[#FF6A13]">
              [ {totalFindings} TOTAL ]
            </span>
          </div>

          <div className="space-y-3.5">
            {(
              [
                { key: "CRITICAL", label: "Critical", color: "#EF4444" },
                { key: "HIGH", label: "High", color: "#FF6A13" },
                { key: "MEDIUM", label: "Medium", color: "#F59E0B" },
                { key: "LOW", label: "Low", color: "#22C55E" },
              ] as const
            ).map((item) => {
              const count = severityCounts[item.key];
              const pct = totalFindings > 0 ? Math.round((count / totalFindings) * 100) : 0;
              return (
                <div key={item.key}>
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-[#F1EEE6]">{item.label}</span>
                    <span className="text-[#A6A39A]">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-sm bg-white/[0.06] overflow-hidden">
                    <div
                      className="h-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: item.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="lg:col-span-7 rounded-sm border border-white/10 bg-[#151616] p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
                LIVE TRIAGE FEED
              </p>
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mt-0.5"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Recent Forensic Alerts
              </h2>
            </div>
            <Link
              href="/findings"
              className="text-xs font-mono text-[#FF6A13] hover:text-[#FF812E] inline-flex items-center gap-1"
            >
              All Findings <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-white/[0.06]">
            {recentAlerts.map((alert) => (
              <div
                key={`${alert.caseId}-${alert.id}`}
                className="py-2.5 flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={alert.severity} />
                    <span className="text-xs font-medium text-[#F1EEE6] truncate">
                      {alert.title}
                    </span>
                  </div>
                  <p className="text-xs text-[#A6A39A] mt-1 line-clamp-1">
                    {alert.explanation}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    selectCase(alert.caseId);
                    router.push(`/investigations/${alert.caseId}`);
                  }}
                  className="shrink-0 text-[11px] font-mono text-[#FF6A13] hover:underline"
                >
                  {alert.caseId}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Investigation Repository */}
      <section className="rounded-sm border border-white/10 bg-[#151616] p-5 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
              CASE REPOSITORY
            </p>
            <h2
              className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mt-0.5"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Active & Archived Investigations
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#A6A39A] absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={localSearch}
                onChange={(e) => setLocalSearch(e.target.value)}
                placeholder="Filter cases..."
                className="h-8 pl-8 pr-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/60 focus:outline-none focus:border-[#FF6A13]"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 px-2.5 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
              aria-label="Filter by status"
            >
              <option value="ALL">Status: ALL</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="PENDING_REVIEW">PENDING_REVIEW</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortField)}
              className="h-8 px-2.5 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
              aria-label="Sort cases"
            >
              <option value="updatedAt">Sort: Recent</option>
              <option value="riskScore">Sort: Risk Score</option>
              <option value="totalVolumeUsd">Sort: Volume USD</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-[11px] font-mono uppercase tracking-wider text-[#A6A39A]">
                <th className="py-2.5 pr-4">Case ID</th>
                <th className="py-2.5 pr-4">Title</th>
                <th className="py-2.5 pr-4">Chain</th>
                <th className="py-2.5 pr-4">Target Address</th>
                <th className="py-2.5 pr-4">Risk</th>
                <th className="py-2.5 pr-4">Volume</th>
                <th className="py-2.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06] text-xs">
              {filteredCases.map((c) => {
                const risk = getCaseRiskScore(c);
                return (
                  <tr key={c.caseId} className="hover:bg-white/[0.02]">
                    <td className="py-3 pr-4 font-mono text-[#FF6A13]">{c.caseId}</td>
                    <td className="py-3 pr-4 text-[#F1EEE6] font-medium">{c.title}</td>
                    <td className="py-3 pr-4 font-mono text-[#A6A39A]">{c.network}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-1.5 font-mono text-[#A6A39A]">
                        <span>{truncateAddress(c.target, 6, 4)}</span>
                        <CopyAddressButton value={c.target} />
                      </div>
                    </td>
                    <td className="py-3 pr-4 font-mono">
                      <span
                        className={cn(
                          risk >= 80
                            ? "text-[#EF4444]"
                            : risk >= 60
                            ? "text-[#FF6A13]"
                            : "text-[#F59E0B]"
                        )}
                      >
                        [ {risk} / 100 ]
                      </span>
                    </td>
                    <td className="py-3 pr-4 font-mono text-[#F1EEE6]">
                      ${c.summary.totalVolumeUSD.toLocaleString()}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          selectCase(c.caseId);
                          router.push(`/investigations/${c.caseId}`);
                        }}
                        className="px-2.5 py-1 rounded-sm border border-white/15 hover:border-[#FF6A13] text-[11px] font-mono text-[#F1EEE6] hover:text-[#FF6A13] transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Bottom Grid: Wallet Risk Overview + Recent Forensic Activity + Network Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
              Wallet Risk Overview
            </h3>
            <Gauge className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <div className="space-y-2.5">
            {topRiskWallets.map((node) => (
              <div
                key={node.id}
                className="flex items-center justify-between p-2 rounded-sm bg-[#080909] border border-white/10"
              >
                <div className="min-w-0">
                  <p className="text-xs font-mono text-[#F1EEE6] truncate">
                    {node.entityName || truncateAddress(node.address || node.id, 6, 4)}
                  </p>
                  <p className="text-[11px] font-mono text-[#A6A39A]">{node.type}</p>
                </div>
                <span className="text-xs font-mono text-[#FF6A13]">
                  [ {node.riskScore} ]
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
              Recent Forensic Activity
            </h3>
            <Activity className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <div className="space-y-3">
            {activeCase.timeline.slice(0, 4).map((ev) => (
              <div key={ev.id} className="border-l border-[#FF6A13]/50 pl-3">
                <p className="text-xs font-medium text-[#F1EEE6]">{ev.title}</p>
                <p className="text-[11px] font-mono text-[#A6A39A] mt-0.5">
                  {formatTimestamp(ev.timestamp)}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-mono uppercase tracking-[0.16em] text-[#A6A39A]">
              Blockchain Network Activity
            </h3>
            <Layers className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <div className="space-y-3">
            <div className="p-3 rounded-sm bg-[#080909] border border-white/10">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#FF6A13]">ETH / ERC-20</span>
                <span className="text-[#F1EEE6]">{networkBreakdown.ethCount} Cases</span>
              </div>
              <p className="text-[11px] font-mono text-[#A6A39A] mt-1">
                Traced: ${networkBreakdown.ethVol.toLocaleString()}
              </p>
            </div>
            <div className="p-3 rounded-sm bg-[#080909] border border-white/10">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#FF6A13]">BTC / UTXO</span>
                <span className="text-[#F1EEE6]">{networkBreakdown.btcCount} Cases</span>
              </div>
              <p className="text-[11px] font-mono text-[#A6A39A] mt-1">
                Traced: ${networkBreakdown.btcVol.toLocaleString()}
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* New Investigation Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-sm border border-white/15 bg-[#151616] p-6 relative">
            <div className="flex items-center justify-between mb-4">
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Launch New Forensic Investigation
              </h2>
              <button
                type="button"
                onClick={() => setShowNewModal(false)}
                className="text-xs font-mono text-[#A6A39A] hover:text-[#F1EEE6]"
              >
                [ ESC ]
              </button>
            </div>
            <NewInvestigationForm onInvestigationCreated={handleCreated} />
          </div>
        </div>
      )}
    </SocShell>
  );
}
