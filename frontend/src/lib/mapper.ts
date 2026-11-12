import {
  BlockchainNetwork,
  EdgeRelationshipType,
  FindingCategory,
  FindingSeverity,
  GraphEdge,
  GraphNode,
  InvestigationCase,
  InvestigationStats,
  NodeType,
  ReceiverCandidate,
  RiskLevel,
  SuspiciousFinding,
} from "@/types/investigation";

export const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export function getBackendHeaders(): HeadersInit {
  const apiKey =
    process.env.BACKEND_API_KEY ||
    (process.env.API_KEYS || "")
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean)[0] ||
    "";

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

interface BackendInvestigation {
  id: string;
  title: string;
  description?: string | null;
  blockchain: string;
  target_address: string;
  max_hops: number;
  status: string;
  total_transactions_ingested: number;
  total_nodes: number;
  total_edges: number;
  created_at: string;
  updated_at: string;
  parameters?: Record<string, unknown>;
}

interface BackendGraphNode {
  id: string;
  node_type: string;
  label: string;
  blockchain: string;
  properties?: Record<string, unknown>;
  first_seen?: string | null;
  last_seen?: string | null;
}

interface BackendGraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  is_confirmed?: boolean;
  is_heuristic?: boolean;
  amount: number | string;
  asset_symbol?: string;
  tx_hash: string;
  block_number?: number | null;
  timestamp?: string | null;
  evidence_reference?: string;
  properties?: Record<string, unknown>;
}

interface BackendGraph {
  root_node_id: string;
  max_hops: number;
  nodes: BackendGraphNode[];
  edges: BackendGraphEdge[];
}

interface BackendFinding {
  finding_id: string;
  rule_id: string;
  rule_version: string;
  title: string;
  category: string;
  severity: string;
  confidence: number;
  explanation: string;
  evidence_refs?: string[];
  limitations?: string[];
  affected_addresses?: string[];
}

interface BackendReceiver {
  rank: number;
  candidate_destination: string;
  entity_label?: string | null;
  value_received?: number;
  risk_priority?: number;
  attribution_confidence?: number;
  investigation_coverage?: number;
  supporting_finding_ids?: string[];
  limitations?: string[];
}

function mapNetwork(chain: string): BlockchainNetwork {
  return chain.toLowerCase() === "bitcoin" ? "BTC" : "ETH";
}

function mapNodeType(raw: string): NodeType {
  const norm = raw.toLowerCase();
  if (norm === "transaction" || norm === "tx") return "transaction";
  if (norm === "contract") return "contract";
  if (norm === "bridge") return "bridge";
  if (norm === "mixer") return "mixer";
  if (norm === "exchange") return "exchange";
  if (norm === "sanctioned") return "sanctioned";
  return "wallet";
}

function mapEdgeType(raw: string, isHeuristic?: boolean): EdgeRelationshipType {
  if (isHeuristic) return "heuristic_link";
  const norm = raw.toLowerCase();
  if (norm.includes("utxo")) return "utxo_spending";
  if (norm.includes("token")) return "token_transfer";
  if (norm.includes("bridge")) return "bridge_correlated";
  return "confirmed_transfer";
}

function mapFindingCategory(raw: string): FindingCategory {
  const norm = raw.toUpperCase();
  if (norm.includes("PEEL")) return "PEEL_CHAIN";
  if (norm.includes("MIXER")) return "MIXER_DEPOSIT";
  if (norm.includes("BRIDGE")) return "BRIDGE_HOPPING";
  if (norm.includes("FAN")) return "FAN_OUT";
  if (norm.includes("DORMANT")) return "RAPID_DORMANT_DRAIN";
  if (norm.includes("SANCTION")) return "SANCTIONED_INTERACTION";
  return "HIGH_VELOCITY_LAYERING";
}

function mapSeverity(raw: string | number): FindingSeverity {
  if (typeof raw === "number") {
    if (raw >= 0.85) return "CRITICAL";
    if (raw >= 0.65) return "HIGH";
    if (raw >= 0.35) return "MEDIUM";
    return "LOW";
  }
  const norm = raw.toUpperCase();
  if (norm === "CRITICAL" || norm === "HIGH" || norm === "MEDIUM" || norm === "LOW") {
    return norm;
  }
  return "MEDIUM";
}

export function mapBackendToInvestigationCase(
  inv: BackendInvestigation,
  graph?: BackendGraph | null,
  findingsData?: { findings?: BackendFinding[] } | null,
  riskData?: { probable_end_receivers?: BackendReceiver[] } | null
): InvestigationCase {
  const network = mapNetwork(inv.blockchain);
  const symbol = network === "BTC" ? "BTC" : "ETH";
  const usdRate = network === "BTC" ? 86000 : 3200;

  const nodes: GraphNode[] = (graph?.nodes || []).map((n) => {
    const props = n.properties || {};
    const riskScore = Number(props.risk_score ?? (n.id === inv.target_address ? 50 : 20));
    const riskLevel: RiskLevel =
      riskScore >= 85
        ? "CRITICAL"
        : riskScore >= 65
          ? "HIGH"
          : riskScore >= 35
            ? "MEDIUM"
            : riskScore >= 15
              ? "LOW"
              : "CLEAN";

    return {
      id: n.id,
      type: mapNodeType(n.node_type),
      label: n.label || n.id,
      address: n.id,
      network,
      balance: Number(props.balance ?? 0),
      totalReceived: Number(props.total_received ?? 0),
      totalSent: Number(props.total_sent ?? 0),
      txCount: Number(props.tx_count ?? 0),
      firstSeen: n.first_seen || inv.created_at,
      lastSeen: n.last_seen || inv.updated_at,
      isInputTarget: n.id.toLowerCase() === inv.target_address.toLowerCase(),
      riskScore,
      riskLevel,
      hop: Number(props.hop ?? (n.id.toLowerCase() === inv.target_address.toLowerCase() ? 0 : 1)),
    };
  });

  const edges: GraphEdge[] = (graph?.edges || []).map((e) => {
    const amount = Number(e.amount ?? 0);
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      relationshipType: mapEdgeType(e.edge_type, e.is_heuristic),
      amount,
      currency: e.asset_symbol || symbol,
      amountUSD: amount * usdRate,
      txHash: e.tx_hash,
      timestamp: e.timestamp || inv.created_at,
      blockNumber: e.block_number ?? undefined,
      isConfirmed: e.is_confirmed ?? true,
      confidence: e.is_heuristic ? 70 : 100,
      heuristicExplanation: e.is_heuristic ? e.evidence_reference : undefined,
    };
  });

  const findings: SuspiciousFinding[] = (findingsData?.findings || []).map((f) => ({
    id: f.finding_id,
    title: f.title,
    category: mapFindingCategory(f.rule_id || f.category),
    severity: mapSeverity(f.severity),
    confidence: Math.round((f.confidence <= 1 ? f.confidence * 100 : f.confidence)),
    status: "ACTIVE",
    affectedWallet: f.affected_addresses?.[0] || inv.target_address,
    network,
    amountInvolved: 0,
    currency: symbol,
    amountUSD: 0,
    evidenceReferences: f.evidence_refs || [],
    detectionRuleId: f.rule_id,
    detectionRuleVersion: f.rule_version,
    explanation: f.explanation,
    limitations: (f.limitations || []).join(" "),
    detectedAt: inv.updated_at,
  }));

  const receivers: ReceiverCandidate[] = (riskData?.probable_end_receivers || []).map((r) => ({
    rank: r.rank,
    walletAddress: r.candidate_destination,
    network,
    riskPriority: mapSeverity(r.risk_priority ?? 0.5),
    attributionConfidence: Math.round((r.attribution_confidence ?? 0.5) * 100),
    knownRiskExposure: r.entity_label || "Unlabelled destination",
    investigationCoverage: Math.round((r.investigation_coverage ?? 0.5) * 100),
    amountReceived: Number(r.value_received ?? 0),
    currency: symbol,
    amountUSD: Number(r.value_received ?? 0) * usdRate,
    supportingEvidence: r.supporting_finding_ids || [],
    reasonsForRanking: r.limitations || [],
    isService: Boolean(r.entity_label),
    serviceLabel: r.entity_label || undefined,
  }));

  const totalVolumeUSD = edges.reduce((acc, e) => acc + e.amountUSD, 0);
  const criticalFindingsCount = findings.filter(
    (f) => f.severity === "CRITICAL" || f.severity === "HIGH"
  ).length;

  return {
    caseId: inv.id,
    title: inv.title,
    status: inv.status === "archived" ? "ARCHIVED" : "ACTIVE",
    createdAt: inv.created_at,
    updatedAt: inv.updated_at,
    target: inv.target_address,
    network,
    type: "address",
    maxHops: inv.max_hops,
    isDemo: true,
    dataSourceMode: "DEMO_REPLAY",
    nodes,
    edges,
    findings,
    receivers,
    timeline: [],
    evidence: [],
    auditLogs: [],
    summary: {
      totalVolumeUSD,
      taintedVolumeUSD: totalVolumeUSD,
      walletsCount: inv.total_nodes || nodes.length,
      transactionsCount: inv.total_transactions_ingested || edges.length,
      criticalFindingsCount,
      topDestination: receivers[0]?.walletAddress || edges[0]?.target,
    },
  };
}

export function buildStatsFromCases(cases: InvestigationCase[]): InvestigationStats {
  return {
    totalInvestigations: cases.length,
    walletsAnalysed: cases.reduce((acc, c) => acc + c.summary.walletsCount, 0),
    transactionsTraced: cases.reduce((acc, c) => acc + c.summary.transactionsCount, 0),
    suspiciousFindings: cases.reduce((acc, c) => acc + c.findings.length, 0),
    highPriorityCases: cases.filter((c) => c.summary.criticalFindingsCount > 0).length,
    recentActivityCount: cases.length,
  };
}
