export type BlockchainNetwork = "ETH" | "BTC";
export type TargetType = "address" | "transaction";

export type NodeType =
  | "wallet"
  | "transaction"
  | "contract"
  | "bridge"
  | "mixer"
  | "exchange"
  | "sanctioned";

export type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "CLEAN";

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  address?: string;
  txHash?: string;
  network: BlockchainNetwork;
  balance?: number;
  totalReceived?: number;
  totalSent?: number;
  txCount?: number;
  firstSeen?: string;
  lastSeen?: string;
  isInputTarget?: boolean;
  entityName?: string;
  entityCategory?: "exchange" | "mixer" | "illicit" | "defi" | "bridge" | "unknown";
  entityProvenance?: string;
  riskScore: number; // 0 - 100
  riskLevel: RiskLevel;
  hop: number;
}

export type EdgeRelationshipType =
  | "confirmed_transfer"
  | "utxo_spending"
  | "token_transfer"
  | "bridge_correlated"
  | "heuristic_link";

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationshipType: EdgeRelationshipType;
  amount: number;
  currency: string;
  amountUSD: number;
  txHash: string;
  timestamp: string;
  blockNumber?: number;
  isConfirmed: boolean;
  confidence: number; // 0 - 100%
  heuristicExplanation?: string;
}

export type FindingCategory =
  | "PEEL_CHAIN"
  | "HIGH_VELOCITY_LAYERING"
  | "MIXER_DEPOSIT"
  | "BRIDGE_HOPPING"
  | "FAN_OUT"
  | "RAPID_DORMANT_DRAIN"
  | "SANCTIONED_INTERACTION";

export type FindingSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type FindingStatus = "ACTIVE" | "TRIAGED" | "DISMISSED";

export interface SuspiciousFinding {
  id: string;
  title: string;
  category: FindingCategory;
  severity: FindingSeverity;
  confidence: number; // 0 - 100
  status: FindingStatus;
  affectedWallet: string;
  network: BlockchainNetwork;
  amountInvolved: number;
  currency: string;
  amountUSD: number;
  evidenceReferences: string[];
  detectionRuleId: string;
  detectionRuleVersion: string;
  explanation: string;
  limitations: string;
  detectedAt: string;
}

export interface ReceiverCandidate {
  rank: number;
  walletAddress: string;
  network: BlockchainNetwork;
  riskPriority: FindingSeverity;
  attributionConfidence: number; // 0 - 100
  knownRiskExposure: string;
  investigationCoverage: number; // percentage of tainted flow
  amountReceived: number;
  currency: string;
  amountUSD: number;
  supportingEvidence: string[];
  reasonsForRanking: string[];
  isService: boolean;
  serviceLabel?: string;
}

export interface EvidenceVaultItem {
  id: string;
  sourceTxHash: string;
  dataSource: string;
  retrievalTimestamp: string;
  detectionRuleVersion: string;
  blockNumber: number;
  rawPayloadHash: string;
  integrityStatus: "VERIFIED" | "PENDING" | "MISMATCH";
  verificationAlgorithm: "SHA-256";
  hashChainIndex: number;
  previousRecordHash: string;
  recordHash: string;
  details: string;
}

export type TimelineEventType = "TRANSACTION" | "BRIDGE" | "FINDING" | "ANALYST" | "AUDIT";

export interface InvestigationTimelineEvent {
  id: string;
  timestamp: string;
  type: TimelineEventType;
  title: string;
  description: string;
  severity?: FindingSeverity | "INFO";
  relatedHash?: string;
  relatedAddress?: string;
  metadata?: Record<string, unknown>;
}

export interface AuditLogEvent {
  id: string;
  timestamp: string;
  eventType:
    | "CASE_CREATED"
    | "RPC_QUERY_EXECUTED"
    | "DETECTION_RULE_FIRED"
    | "ANALYST_TAG_ADDED"
    | "HASH_CHAIN_SEALED"
    | "REPORT_GENERATED";
  operator: string;
  action: string;
  details: string;
  sha256Proof: string;
  verified: boolean;
}

export interface CopilotMessage {
  id: string;
  sender: "user" | "copilot";
  timestamp: string;
  text: string;
  groundedFindings?: string[];
  findings?: string[];
  evidenceIds?: string[];
  isGenerating?: boolean;
  isOfflineFallback?: boolean;
}

export interface InvestigationCase {
  caseId: string;
  title: string;
  status: "ACTIVE" | "ARCHIVED" | "PENDING_REVIEW";
  createdAt: string;
  updatedAt: string;
  target: string;
  network: BlockchainNetwork;
  type: TargetType;
  maxHops: number;
  timeRange?: { from?: string; to?: string };
  isDemo: boolean;
  dataSourceMode: "LIVE_RPC" | "DEMO_REPLAY";
  nodes: GraphNode[];
  edges: GraphEdge[];
  findings: SuspiciousFinding[];
  receivers: ReceiverCandidate[];
  timeline: InvestigationTimelineEvent[];
  evidence: EvidenceVaultItem[];
  auditLogs: AuditLogEvent[];
  summary: {
    totalVolumeUSD: number;
    taintedVolumeUSD: number;
    walletsCount: number;
    transactionsCount: number;
    criticalFindingsCount: number;
    topDestination?: string;
  };
}

export interface InvestigationStats {
  totalInvestigations: number;
  walletsAnalysed: number;
  transactionsTraced: number;
  suspiciousFindings: number;
  highPriorityCases: number;
  recentActivityCount: number;
}
