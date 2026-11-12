"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, Info } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { RiskGauge } from "@/components/common/RiskGauge";
import { useForensic } from "@/context/ForensicContext";
import { ReceiverIntelligenceView } from "@/features/intelligence/ReceiverIntelligenceView";
import { getCaseConfidence, getCaseRiskScore } from "@/lib/utils";

export default function RiskIntelligencePage() {
  const router = useRouter();
  const { allCases, activeCase, selectCase } = useForensic();

  const hasMixerExposure = activeCase.findings.some((f) =>
    f.category.toLowerCase().includes("mixer")
  );
  const rawConfidence = getCaseConfidence(activeCase);
  const attributionConfidence = hasMixerExposure
    ? Math.min(rawConfidence, 65)
    : rawConfidence;

  const knownRiskExposure = Math.min(
    100,
    Math.round(
      activeCase.findings.reduce((acc, f) => acc + (f.severity === "CRITICAL" ? 30 : 18), 15)
    )
  );
  const investigationCoverage = Math.min(
    100,
    Math.round(
      (activeCase.evidence.length / Math.max(1, activeCase.nodes.length)) * 100
    )
  );

  return (
    <SocShell
      title="Four-Dimensional Risk & Attribution Intelligence"
      subtitle={`Calibrated scoring & probable end-receiver ranking for ${activeCase.caseId}`}
      actions={
        <select
          value={activeCase.caseId}
          onChange={(e) => selectCase(e.target.value)}
          className="h-9 px-3 rounded bg-[#0E1217] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
          aria-label="Select investigation case"
        >
          {allCases.map((c) => (
            <option key={c.caseId} value={c.caseId}>
              {c.caseId} · {c.network}
            </option>
          ))}
        </select>
      }
    >
      {/* 4 Risk Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <RiskGauge
          label="Risk Priority"
          score={getCaseRiskScore(activeCase)}
          subtitle="Composite triage urgency"
        />
        <RiskGauge
          label="Attribution Confidence"
          score={attributionConfidence}
          subtitle={
            hasMixerExposure
              ? "Capped due to mixer ambiguity"
              : "Evidence-backed attribution"
          }
        />
        <RiskGauge
          label="Known Risk Exposure"
          score={knownRiskExposure}
          subtitle="Sanctioned / illicit entity hops"
        />
        <RiskGauge
          label="Investigation Coverage"
          score={investigationCoverage}
          subtitle="Verified evidence-to-node ratio"
        />
      </div>

      {/* Mixer Exposure Cap Note & Identity Restraint Disclaimer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="rounded border border-[#00E5FF]/25 bg-[#00E5FF]/5 p-4 flex items-start gap-3">
          <Info className="w-4 h-4 text-[#00E5FF] shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <p className="font-mono uppercase text-[#00E5FF] mb-1">
              Mixer-Exposure Confidence Cap
            </p>
            <p className="text-[#8A929E]">
              When mixer fan-in/fan-out or CoinJoin collaborative transactions are
              detected on-path, Attribution Confidence is bounded to prevent false
              attribution across pooled anonymity sets.
            </p>
          </div>
        </div>

        <div className="rounded border border-[#F59E0B]/30 bg-[#F59E0B]/10 p-4 flex items-start gap-3">
          <ShieldAlert className="w-4 h-4 text-[#F59E0B] shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <p className="font-mono uppercase text-[#F59E0B] mb-1">
              Identity Restraint Disclaimer
            </p>
            <p className="text-[#F5F7FA]/85">
              Probable end-receiver rankings reflect deterministic flow, timing, and
              clustering heuristics—not proof of real-world legal ownership.
            </p>
          </div>
        </div>
      </div>

      {/* Probable End-Receiver Candidates */}
      <ReceiverIntelligenceView
        receivers={activeCase.receivers}
        network={activeCase.network}
        onSelectCandidate={() => router.push("/graph")}
      />
    </SocShell>
  );
}
