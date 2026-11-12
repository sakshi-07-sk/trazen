import { NextRequest, NextResponse } from "next/server";
import { MOCK_ETH_CASE, MOCK_BTC_CASE } from "@/lib/mockData";
import { InvestigationCase } from "@/types/investigation";

export async function POST(req: NextRequest) {
  try {
    const { caseId, query } = await req.json();

    // Select case context
    let activeCase: InvestigationCase = MOCK_ETH_CASE;
    if (caseId === MOCK_BTC_CASE.caseId || caseId?.includes("BTC")) {
      activeCase = MOCK_BTC_CASE;
    }

    const q = (query || "").toLowerCase();
    let responseText = "";
    const evidenceIds: string[] = [];
    const findings: string[] = [];

    // Deterministic Forensic Rule Grounding Engine
    if (q.includes("why is this wallet suspicious") || q.includes("suspicious")) {
      const topFinding = activeCase.findings[0];
      findings.push(topFinding.id);
      evidenceIds.push(...topFinding.evidenceReferences);

      responseText = `Based on forensic detection rule **${topFinding.detectionRuleId} (v${topFinding.detectionRuleVersion})**, wallet \`${activeCase.target}\` exhibits **${topFinding.severity} severity** risk (Confidence: ${topFinding.confidence}%).\n\n**Key Factors:**\n- **Category:** ${topFinding.category.replace(/_/g, " ")}\n- **Forensic Explanation:** ${topFinding.explanation}\n- **Direct Amount Tainted:** ${topFinding.amountInvolved.toLocaleString()} ${topFinding.currency} (~$${topFinding.amountUSD.toLocaleString()})\n\n**Methodology Limitations:**\n${topFinding.limitations}`;
    } else if (q.includes("peel") || q.includes("peel-chain")) {
      const peelFinding = activeCase.findings.find((f) => f.category === "PEEL_CHAIN") || activeCase.findings[0];
      findings.push(peelFinding.id);
      evidenceIds.push(...peelFinding.evidenceReferences);

      responseText = `**Peel Chain Forensic Breakdown:**\n\nThe detection engine flagged rule **${peelFinding.detectionRuleId}** on node \`${peelFinding.affectedWallet}\`.\n\n- **Mechanism:** In an automated peeling structure, the actor incrementally deducts a specific tranche while sweeping the remaining unspent/change balance to an ephemeral intermediate address with zero prior history.\n- **Confidence:** ${peelFinding.confidence}%\n- **Volume:** ${peelFinding.amountInvolved} ${peelFinding.currency} (~$${peelFinding.amountUSD.toLocaleString()})\n- **Limitations:** ${peelFinding.limitations}`;
    } else if (q.includes("hop") || q.includes("three-hop") || q.includes("trace")) {
      const hopCount = activeCase.nodes.reduce((max, n) => Math.max(max, n.hop), 0);
      findings.push(...activeCase.findings.map((f) => f.id));
      evidenceIds.push(...activeCase.evidence.map((e) => e.id));

      responseText = `**Trace Topology Summary (${hopCount}-Hop Expansion):**\n\n1. **Hop 0 (Target Ingress):** Ingress funded at target \`${activeCase.target}\`.\n2. **Hop 1 (Dispersion & Split):** Immediate multi-directional fan-out to rapid-transit intermediate nodes.\n3. **Hop 2 (Cross-Protocol & Peel):** Routing into obfuscation conduits (e.g. liquidity bridges and ephemeral peel nodes).\n4. **Hop 3 (Terminal Horizon):** Funds partitioned into mixer pools and suspected OTC liquidity desks.\n\nTotal traced tainted volume: **$${activeCase.summary.taintedVolumeUSD.toLocaleString()} USD** across **${activeCase.summary.walletsCount} wallets** and **${activeCase.summary.transactionsCount} transactions**.`;
    } else if (q.includes("receiver") || q.includes("strongest evidence")) {
      const topReceiver = activeCase.receivers[0];
      findings.push(activeCase.findings[0].id);
      evidenceIds.push(...topReceiver.supportingEvidence);

      responseText = `**Rank #1 Candidate Destination Analysis:**\n\n- **Address:** \`${topReceiver.walletAddress}\`\n- **Entity Attribution:** ${topReceiver.knownRiskExposure}\n- **Attribution Confidence:** ${topReceiver.attributionConfidence}%\n- **Investigation Flow Coverage:** ${topReceiver.investigationCoverage}%\n- **Amount Received:** ${topReceiver.amountReceived.toLocaleString()} ${topReceiver.currency} (~$${topReceiver.amountUSD.toLocaleString()})\n\n**Supporting Forensics:**\n${topReceiver.reasonsForRanking.map((r) => `• ${r}`).join("\n")}\n\n*Notice: On-chain addresses represent cryptographic accounts. Analysis models fund likelihood and does not assert personal legal identity.*`;
    } else if (q.includes("uncertain") || q.includes("limitation")) {
      responseText = `**Uncertainty & Forensic Limitations Analysis:**\n\n1. **Mixer Ingress Barrier:** Transactions entering anonymity sets (e.g. Tornado Cash 100 ETH pool) terminate deterministic graph continuity. Unmixing requires temporal deposit-withdrawal statistical correlation.\n2. **Bridge Relay Correlation:** Cross-chain transfers are heuristic correlations based on block timestamps, input/output volumes, and bridge protocol contract calls; not cryptographic atomic linkages.\n3. **Change-Output Disambiguation:** In UTXO analysis, peeling heuristics assume standard BIP-69 ordering; proprietary wallet sorting algorithms could introduce false-positive change misidentifications.`;
    } else if (q.includes("report") || q.includes("summarize") || q.includes("summary")) {
      findings.push(...activeCase.findings.slice(0, 3).map((f) => f.id));
      evidenceIds.push(...activeCase.evidence.slice(0, 3).map((e) => e.id));

      responseText = `**Executive Forensic Summary: ${activeCase.caseId}**\n\n- **Subject:** \`${activeCase.target}\` [${activeCase.network}]\n- **Case Status:** ${activeCase.status} | **Severity:** CRITICAL\n- **Total Monitored Volume:** $${activeCase.summary.totalVolumeUSD.toLocaleString()} USD\n- **Identified Taint Exposure:** $${activeCase.summary.taintedVolumeUSD.toLocaleString()} USD\n- **Critical Findings:** ${activeCase.findings.length} registered by detection engine\n- **Primary Terminal Conduit:** \`${activeCase.summary.topDestination}\`\n- **Evidence Vault Status:** Sealed with SHA-256 hash-chain verification intact.`;
    } else {
      findings.push(activeCase.findings[0]?.id || "FINDING-001");
      evidenceIds.push(activeCase.evidence[0]?.id || "EVID-001");

      responseText = `**TraceAI Forensic Response:**\n\nInvestigation \`${activeCase.caseId}\` is actively monitoring **${activeCase.nodes.length} nodes** and **${activeCase.edges.length} directed transfer edges**.\n\n- **Primary Finding:** ${activeCase.findings[0]?.title}\n- **Associated Evidence Record:** ${activeCase.evidence[0]?.id} (verified via ${activeCase.evidence[0]?.dataSource})\n- **Audit Status:** SHA-256 chain verified.\n\nYou can ask about specific hop structures, receiver candidate rankings, peel chains, or evidence hashes.`;
    }

    return NextResponse.json({
      message: responseText,
      evidenceIds,
      findings,
      isOffline: true,
    });
  } catch (err: unknown) {
    const error = err as Error;
    return NextResponse.json(
      { code: "COPILOT_ERROR", message: error.message || "Failed to execute copilot query" },
      { status: 500 }
    );
  }
}
