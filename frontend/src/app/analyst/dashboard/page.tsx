"use client";

import React, { useMemo, useState } from "react";
import {
  LayoutDashboard,
  ShieldAlert,
  Wallet,
  Gauge,
  GitFork,
  Bell,
  FileText,
  ArrowRightLeft,
  Info,
} from "lucide-react";
import { RoleNavItem, RoleShell } from "@/components/layout/RoleShell";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";
import { RiskGauge } from "@/components/common/RiskGauge";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { CopyAddressButton } from "@/components/common/CopyAddressButton";
import { ReceiverIntelligenceView } from "@/features/intelligence/ReceiverIntelligenceView";
import { InvestigationReportModal } from "@/features/reports/InvestigationReportModal";
import { useForensic } from "@/context/ForensicContext";
import {
  formatTimestamp,
  getCaseConfidence,
  getCaseRiskScore,
  truncateAddress,
} from "@/lib/utils";

const ANALYST_NAV: RoleNavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "intel", label: "Threat Intelligence", icon: ShieldAlert },
  { id: "wallets", label: "Suspicious Wallets", icon: Wallet },
  { id: "risk", label: "Risk Analysis", icon: Gauge },
  { id: "patterns", label: "Transaction Patterns", icon: GitFork },
  { id: "alerts", label: "Alerts", icon: Bell },
  { id: "reports", label: "Reports", icon: FileText },
];

export default function AnalystDashboardPage() {
  const { allCases, activeCase, selectCase, settings } = useForensic();
  const [section, setSection] = useState("dashboard");
  const [reportOpen, setReportOpen] = useState(false);

  const highRiskWallets = useMemo(() => {
    return allCases
      .flatMap((c) =>
        c.nodes.map((n) => ({
          ...n,
          caseId: c.caseId,
          network: c.network,
        }))
      )
      .filter((n) => n.riskScore >= settings.highRiskThreshold)
      .sort((a, b) => b.riskScore - a.riskScore);
  }, [allCases, settings.highRiskThreshold]);

  const patternFindings = useMemo(() => {
    return allCases.flatMap((c) =>
      c.findings.map((f) => ({ ...f, caseId: c.caseId }))
    );
  }, [allCases]);

  const crossChainEdges = useMemo(() => {
    return allCases.flatMap((c) =>
      c.edges
        .filter((e) => e.relationshipType === "bridge_correlated")
        .map((e) => ({ ...e, caseId: c.caseId, network: c.network }))
    );
  }, [allCases]);

  const hasMixer = activeCase.findings.some((f) =>
    f.category.toLowerCase().includes("mixer")
  );
  const rawConf = getCaseConfidence(activeCase);
  const attributionConf = hasMixer ? Math.min(rawConf, 65) : rawConf;
  const riskScore = getCaseRiskScore(activeCase);

  return (
    <RoleShell
      role="ANALYST"
      navItems={ANALYST_NAV}
      activeSection={section}
      onSelectSection={setSection}
      title="Threat Intelligence & Risk Analysis"
      subtitle={`Monitoring ${highRiskWallets.length} high-risk wallets · Active Case ${activeCase.caseId}`}
      actions={
        <select
          value={activeCase.caseId}
          onChange={(e) => selectCase(e.target.value)}
          className="h-9 px-3 rounded-sm bg-[#151616] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
          aria-label="Select investigation case"
        >
          {allCases.map((c) => (
            <option key={c.caseId} value={c.caseId}>
              {c.caseId} · {c.network} · {c.title}
            </option>
          ))}
        </select>
      }
    >
      {section === "dashboard" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                High-Risk Wallets
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#EF4444] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={highRiskWallets.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Risk ≥ {settings.highRiskThreshold}/100
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Pattern Detections
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={patternFindings.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Peel-chain, mixer & layering
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Cross-Chain Movements
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#22C55E] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={crossChainEdges.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Bridge-correlated transfers
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Active Case Risk
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={riskScore} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Attribution {attributionConf}%
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mb-4"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                High-Risk Wallet Watchlist
              </h2>
              <div className="space-y-2.5">
                {highRiskWallets.slice(0, 5).map((w) => (
                  <div
                    key={`${w.caseId}-${w.id}`}
                    className="p-3 rounded-sm bg-[#080909] border border-white/10 flex items-center justify-between gap-2 text-xs"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-[#F1EEE6] truncate">
                        {w.entityName || truncateAddress(w.address || w.id, 8, 6)}
                      </p>
                      <p className="text-[11px] font-mono text-[#A6A39A]">
                        {w.network} · {w.type} · {w.caseId}
                      </p>
                    </div>
                    <span className="font-mono text-[#EF4444] shrink-0">
                      [ {w.riskScore} / 100 ]
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mb-4"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Recent Threat Alerts
              </h2>
              <div className="space-y-2.5">
                {patternFindings.slice(0, 5).map((f) => (
                  <div
                    key={`${f.caseId}-${f.id}`}
                    className="p-3 rounded-sm bg-[#080909] border border-white/10 text-xs"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <SeverityBadge severity={f.severity} />
                        <span className="font-medium text-[#F1EEE6]">{f.title}</span>
                      </div>
                      <span className="font-mono text-[#FF6A13]">{f.caseId}</span>
                    </div>
                    <p className="text-[#A6A39A] mt-1 line-clamp-2">{f.explanation}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}

      {section === "intel" && (
        <div className="space-y-6">
          <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
            <div className="flex items-center gap-2 text-xs font-mono text-[#FF6A13] mb-3">
              <ArrowRightLeft className="w-4 h-4" />
              CROSS-CHAIN MOVEMENT MONITORING
            </div>
            {crossChainEdges.length === 0 ? (
              <p className="text-xs text-[#A6A39A]">
                No bridge-correlated cross-chain edges detected in current cases.
              </p>
            ) : (
              <div className="space-y-2.5">
                {crossChainEdges.map((edge) => (
                  <div
                    key={`${edge.caseId}-${edge.id}`}
                    className="p-3.5 rounded-sm bg-[#080909] border border-white/10 flex flex-wrap items-center justify-between gap-2 text-xs font-mono"
                  >
                    <span className="text-[#F1EEE6]">
                      {truncateAddress(edge.source, 6, 4)} →{" "}
                      {truncateAddress(edge.target, 6, 4)}
                    </span>
                    <span className="text-[#22C55E]">
                      {edge.amount.toLocaleString()} {edge.currency}
                    </span>
                    <span className="text-[#A6A39A]">{edge.caseId}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          <ReceiverIntelligenceView
            receivers={activeCase.receivers}
            network={activeCase.network}
          />
        </div>
      )}

      {section === "wallets" && (
        <section className="rounded-sm border border-white/10 bg-[#151616] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 bg-[#101111] text-[11px] font-mono uppercase text-[#A6A39A]">
                  <th className="py-3 px-4">Wallet / Entity</th>
                  <th className="py-3 px-4">Chain</th>
                  <th className="py-3 px-4">Behavior Type</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">Case</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-xs">
                {highRiskWallets.map((w) => (
                  <tr key={`${w.caseId}-${w.id}`}>
                    <td className="py-3 px-4">
                      <p className="font-medium text-[#F1EEE6]">
                        {w.entityName || "Unlabeled Wallet"}
                      </p>
                      <div className="flex items-center gap-1.5 font-mono text-[11px] text-[#A6A39A]">
                        <span>{truncateAddress(w.address || w.id, 8, 6)}</span>
                        <CopyAddressButton value={w.address || w.id} />
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[#A6A39A]">{w.network}</td>
                    <td className="py-3 px-4 font-mono text-[#FF6A13] uppercase">
                      {w.type}
                    </td>
                    <td className="py-3 px-4 font-mono text-[#EF4444]">
                      [ {w.riskScore} / 100 ]
                    </td>
                    <td className="py-3 px-4 font-mono text-[#A6A39A]">{w.caseId}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {section === "risk" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <RiskGauge
              label="Risk Priority"
              score={riskScore}
              subtitle="Composite severity"
            />
            <RiskGauge
              label="Attribution Confidence"
              score={attributionConf}
              subtitle={
                hasMixer ? "Capped due to mixer exposure" : "Evidence-backed"
              }
            />
            <RiskGauge
              label="Known Risk Exposure"
              score={Math.min(100, activeCase.findings.length * 24 + 18)}
              subtitle="Sanctioned / illicit hops"
            />
            <RiskGauge
              label="Investigation Coverage"
              score={Math.min(
                100,
                Math.round(
                  (activeCase.evidence.length / Math.max(1, activeCase.nodes.length)) *
                    100
                )
              )}
              subtitle="Evidence-to-node ratio"
            />
          </div>
          <div className="rounded-sm border border-[#FF6A13]/30 bg-[#FF6A13]/5 p-4 flex items-start gap-3 text-xs">
            <Info className="w-4 h-4 text-[#FF6A13] shrink-0 mt-0.5" />
            <p className="text-[#A6A39A]">
              Analyst Identity Restraint: Attribution scores quantify behavioral and
              topological correlation across peel chains, mixers, and clustering
              heuristics; they do not establish legal ownership on their own.
            </p>
          </div>
        </div>
      )}

      {section === "patterns" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patternFindings.map((f) => (
            <div
              key={`${f.caseId}-${f.id}`}
              className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 space-y-2 transition-colors"
            >
              <div className="flex items-center justify-between">
                <SeverityBadge severity={f.severity} />
                <span className="text-[11px] font-mono text-[#FF6A13]">
                  {f.category}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-[#F1EEE6]">{f.title}</h3>
              <p className="text-xs text-[#A6A39A]">{f.explanation}</p>
              <p className="text-[11px] font-mono text-[#F59E0B] pt-1">
                Limitation: {f.limitations}
              </p>
            </div>
          ))}
        </div>
      )}

      {section === "alerts" && (
        <div className="space-y-3">
          {patternFindings.map((f) => (
            <div
              key={`${f.caseId}-${f.id}`}
              className="rounded-sm border border-white/10 bg-[#151616] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div>
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={f.severity} />
                  <span className="text-xs font-semibold text-[#F1EEE6]">
                    {f.title}
                  </span>
                </div>
                <p className="text-xs text-[#A6A39A] mt-1">{f.explanation}</p>
              </div>
              <div className="text-right font-mono text-[11px] text-[#A6A39A] shrink-0">
                <p className="text-[#FF6A13]">{f.caseId}</p>
                <p>{formatTimestamp(f.detectedAt)}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {section === "reports" && (
        <div className="rounded-sm border border-white/10 bg-[#151616] p-6 flex items-center justify-between">
          <div>
            <h2
              className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Risk Analysis Report — {activeCase.caseId}
            </h2>
            <p className="text-xs text-[#A6A39A] mt-1">
              Export 4D risk breakdown, receiver rankings, and pattern findings.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setReportOpen(true)}
            className="px-4 py-2 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-mono font-semibold uppercase tracking-[0.12em] transition-colors"
          >
            Preview & Export
          </button>
        </div>
      )}

      <InvestigationReportModal
        investigation={activeCase}
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
      />
    </RoleShell>
  );
}
