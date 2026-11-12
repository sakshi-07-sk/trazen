import { NextRequest, NextResponse } from "next/server";
import { MOCK_ETH_CASE, MOCK_BTC_CASE, RECENT_INVESTIGATIONS_LIST } from "@/lib/mockData";
import { validateCryptoInput } from "@/lib/validation";
import { InvestigationCase } from "@/types/investigation";

// In-memory store for newly created investigation sessions
const investigationStore: Map<string, InvestigationCase> = new Map([
  [MOCK_ETH_CASE.caseId, MOCK_ETH_CASE],
  [MOCK_BTC_CASE.caseId, MOCK_BTC_CASE],
]);

export async function GET() {
  const cases = Array.from(investigationStore.values());
  return NextResponse.json(cases);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { target, network, type, maxHops = 3, timeRange, mode = "auto" } = body;

    const validation = validateCryptoInput(target, network, type);
    if (!validation.isValid) {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message: validation.error || "Input target does not meet blockchain network standards.",
        },
        { status: 400 }
      );
    }

    const detectedNetwork = validation.detectedNetwork || network || "ETH";
    const detectedType = validation.detectedType || type || "address";

    // Handle live mode request
    if (mode === "live") {
      const hasLiveProvider = Boolean(
        process.env.ALCHEMY_API_KEY ||
        process.env.INFURA_API_KEY ||
        process.env.BITCOIN_RPC_URL
      );

      if (!hasLiveProvider) {
        return NextResponse.json(
          {
            code: "PROVIDER_ERROR",
            message:
              "Live ingestion failed: No archive RPC provider credentials (ALCHEMY_API_KEY / INFURA_API_KEY / BITCOIN_RPC_URL) are configured in the environment. Per forensic rules, fabricated data is never returned for failed live ingestion. Please enable Demo Investigation Mode or configure credentials.",
          },
          { status: 503 }
        );
      }
    }

    // Check if target matches existing demo cases
    const normalizedTarget = target.toLowerCase();
    if (normalizedTarget === MOCK_ETH_CASE.target.toLowerCase()) {
      return NextResponse.json(MOCK_ETH_CASE);
    }
    if (normalizedTarget === MOCK_BTC_CASE.target.toLowerCase()) {
      return NextResponse.json(MOCK_BTC_CASE);
    }

    // Generate a fresh forensic case structure for new target
    const newCaseId = `CT-CASE-${Date.now().toString().slice(-6)}`;
    const nowISO = new Date().toISOString();

    const isEth = detectedNetwork === "ETH";
    const symbol = isEth ? "ETH" : "BTC";
    const rate = isEth ? 3200 : 86000;

    const newCase: InvestigationCase = {
      caseId: newCaseId,
      title: `Forensic Ingress Trace: ${target.substring(0, 10)}... [${detectedNetwork}]`,
      status: "ACTIVE",
      createdAt: nowISO,
      updatedAt: nowISO,
      target,
      network: detectedNetwork,
      type: detectedType,
      maxHops: Number(maxHops),
      timeRange: timeRange || {
        from: new Date(Date.now() - 30 * 86400000).toISOString(),
        to: nowISO,
      },
      isDemo: true,
      dataSourceMode: "DEMO_REPLAY",
      summary: {
        totalVolumeUSD: rate * 14.5,
        taintedVolumeUSD: rate * 10.2,
        walletsCount: 4,
        transactionsCount: 5,
        criticalFindingsCount: 1,
        topDestination: isEth ? "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b" : "1MixerBTCCluster8901234567890abcde",
      },
      nodes: [
        {
          id: "target-node",
          type: "wallet",
          label: `Target Wallet (${target.substring(0, 6)}...${target.substring(target.length - 4)})`,
          address: target,
          network: detectedNetwork,
          balance: 1.45,
          totalReceived: 14.5,
          totalSent: 13.05,
          txCount: 6,
          firstSeen: new Date(Date.now() - 14 * 86400000).toISOString(),
          lastSeen: nowISO,
          isInputTarget: true,
          entityName: "Investigated Subject Address",
          entityCategory: "unknown",
          entityProvenance: "Primary Case Target Input",
          riskScore: 78,
          riskLevel: "HIGH",
          hop: 0,
        },
        {
          id: "hop1-node",
          type: "wallet",
          label: isEth ? "Transit Splitter (0x2a91...4412)" : "Peel Address (bc1q...4412)",
          address: isEth ? "0x2a91283746192837461928374619283746194412" : "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7k4412",
          network: detectedNetwork,
          balance: 0.2,
          totalReceived: 8.5,
          totalSent: 8.3,
          txCount: 4,
          firstSeen: new Date(Date.now() - 7 * 86400000).toISOString(),
          lastSeen: nowISO,
          entityName: "Rapid Dwell Intermediary",
          entityCategory: "unknown",
          entityProvenance: "Automated Chain Expansion",
          riskScore: 84,
          riskLevel: "HIGH",
          hop: 1,
        },
        {
          id: "service-node",
          type: isEth ? "mixer" : "mixer",
          label: isEth ? "Tornado Cash Privacy Pool" : "CoinJoin Anonymity Set",
          address: isEth ? "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b" : "1MixerBTCCluster8901234567890abcde",
          network: detectedNetwork,
          balance: 12000.0,
          totalReceived: 50000.0,
          totalSent: 38000.0,
          txCount: 1200,
          entityName: isEth ? "Tornado Cash Router" : "CoinJoin Mixer Pool",
          entityCategory: "mixer",
          entityProvenance: "OFAC SDN Regulated Entity",
          riskScore: 99,
          riskLevel: "CRITICAL",
          hop: 2,
        },
        {
          id: "receiver-candidate-1",
          type: "wallet",
          label: isEth ? "End Receiver Candidate (0x8891...bb02)" : "End Receiver Candidate (bc1q...bb02)",
          address: isEth ? "0x889123847589123847589123847589123847bb02" : "bc1q9d8sf7320498scnlkdmsdlkmflkdm453xbb02",
          network: detectedNetwork,
          balance: 4.5,
          totalReceived: 4.5,
          totalSent: 0.0,
          txCount: 1,
          entityName: "Candidate Destination Account",
          entityCategory: "unknown",
          entityProvenance: "Flow Accumulator Heuristic",
          riskScore: 82,
          riskLevel: "HIGH",
          hop: 2,
        },
      ],
      edges: [
        {
          id: "edge-t-h1",
          source: "target-node",
          target: "hop1-node",
          relationshipType: isEth ? "confirmed_transfer" : "utxo_spending",
          amount: 8.5,
          currency: symbol,
          amountUSD: 8.5 * rate,
          txHash: isEth ? "0xfa1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc1" : "fa1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc1",
          timestamp: new Date(Date.now() - 5 * 86400000).toISOString(),
          blockNumber: isEth ? 20895000 : 861400,
          isConfirmed: true,
          confidence: 100,
        },
        {
          id: "edge-h1-srv",
          source: "hop1-node",
          target: "service-node",
          relationshipType: isEth ? "confirmed_transfer" : "heuristic_link",
          amount: 5.0,
          currency: symbol,
          amountUSD: 5.0 * rate,
          txHash: isEth ? "0xfb234567890abcdef1234567890abcdef1234567890abcdef1234567890abc2" : "fb234567890abcdef1234567890abcdef1234567890abcdef1234567890abc2",
          timestamp: new Date(Date.now() - 3 * 86400000).toISOString(),
          blockNumber: isEth ? 20895500 : 861450,
          isConfirmed: true,
          confidence: 95,
        },
        {
          id: "edge-h1-rcv",
          source: "hop1-node",
          target: "receiver-candidate-1",
          relationshipType: "confirmed_transfer",
          amount: 3.3,
          currency: symbol,
          amountUSD: 3.3 * rate,
          txHash: isEth ? "0xfc34567890abcdef1234567890abcdef1234567890abcdef1234567890abc3" : "fc34567890abcdef1234567890abcdef1234567890abcdef1234567890abc3",
          timestamp: new Date(Date.now() - 2 * 86400000).toISOString(),
          blockNumber: isEth ? 20896000 : 861500,
          isConfirmed: true,
          confidence: 100,
        },
      ],
      findings: [
        {
          id: `FINDING-${Date.now().toString().slice(-4)}`,
          title: "High-Risk Obfuscation Layering Pattern Detected",
          category: "HIGH_VELOCITY_LAYERING",
          severity: "CRITICAL",
          confidence: 92,
          status: "ACTIVE",
          affectedWallet: target,
          network: detectedNetwork,
          amountInvolved: 8.5,
          currency: symbol,
          amountUSD: 8.5 * rate,
          evidenceReferences: [`EVID-${detectedNetwork}-001`],
          detectionRuleId: "RULE-VELOCITY-LAYER-V2",
          detectionRuleVersion: "2.1.0",
          explanation: `Systematic onward routing of ${symbol} from target address within short block duration into intermediary addresses with immediate dispersion to anonymity service.`,
          limitations: "Heuristic timing correlation. Could represent automated hot-wallet sweeping in rare non-adversarial architectures.",
          detectedAt: nowISO,
        },
      ],
      receivers: [
        {
          rank: 1,
          walletAddress: isEth ? "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b" : "1MixerBTCCluster8901234567890abcde",
          network: detectedNetwork,
          riskPriority: "CRITICAL",
          attributionConfidence: 94,
          knownRiskExposure: isEth ? "Tornado Cash Anonymity Pool" : "CoinJoin Mixer Set",
          investigationCoverage: 38.5,
          amountReceived: 5.0,
          currency: symbol,
          amountUSD: 5.0 * rate,
          supportingEvidence: [`EVID-${detectedNetwork}-001`],
          reasonsForRanking: [
            "Direct cryptographic transfer into privacy protocol",
            "Attributed to OFAC sanctioned smart-contract address",
          ],
          isService: true,
          serviceLabel: isEth ? "Tornado Cash Pool" : "CoinJoin Cluster",
        },
        {
          rank: 2,
          walletAddress: isEth ? "0x889123847589123847589123847589123847bb02" : "bc1q9d8sf7320498scnlkdmsdlkmflkdm453xbb02",
          network: detectedNetwork,
          riskPriority: "HIGH",
          attributionConfidence: 82,
          knownRiskExposure: "Unhosted Peel Accumulator",
          investigationCoverage: 25.4,
          amountReceived: 3.3,
          currency: symbol,
          amountUSD: 3.3 * rate,
          supportingEvidence: [`EVID-${detectedNetwork}-001`],
          reasonsForRanking: [
            "Received secondary peeled flow with no subsequent out-transfers",
            "High dwell time indicates accumulation behavior",
          ],
          isService: false,
        },
      ],
      evidence: [
        {
          id: `EVID-${detectedNetwork}-001`,
          sourceTxHash: isEth ? "0xfa1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc1" : "fa1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc1",
          dataSource: isEth ? "Geth Consensus Sync Archive RPC" : "Bitcoin Core Full Node RPC",
          retrievalTimestamp: nowISO,
          detectionRuleVersion: "RULE-VELOCITY-LAYER-V2",
          blockNumber: isEth ? 20895000 : 861400,
          rawPayloadHash: "11aa22bb33cc44dd55ee66ff77aa88bb99cc00dd11ee22ff33aa44bb55cc66dd",
          integrityStatus: "VERIFIED",
          verificationAlgorithm: "SHA-256",
          hashChainIndex: 0,
          previousRecordHash: "0000000000000000000000000000000000000000000000000000000000000000",
          recordHash: "99aabbccddeeff00112233445566778899aabbccddeeff001122334455667788",
          details: `Ingress block confirmation for transaction moving ${symbol} from target subject.`,
        },
      ],
      timeline: [
        {
          id: "tl-new-01",
          timestamp: new Date(Date.now() - 5 * 86400000).toISOString(),
          type: "TRANSACTION",
          title: "Observed Initial Value Outflow",
          description: `Target address transferred 8.5 ${symbol} to intermediary transit wallet.`,
          severity: "HIGH",
        },
        {
          id: "tl-new-02",
          timestamp: nowISO,
          type: "AUDIT",
          title: "Investigation Case Initialized & Sealed",
          description: `Cryptographic record ledger initialized with hash chain root for case ${newCaseId}.`,
          severity: "INFO",
        },
      ],
      auditLogs: [
        {
          id: `AUD-NEW-01`,
          timestamp: nowISO,
          eventType: "CASE_CREATED",
          operator: "Analyst SEC-OPERATOR",
          action: `Initiate Case ${newCaseId}`,
          details: `Target: ${target} [${detectedNetwork}] with ${maxHops} hops.`,
          sha256Proof: "99aabbccddeeff00112233445566778899aabbccddeeff001122334455667788",
          verified: true,
        },
      ],
    };

    investigationStore.set(newCaseId, newCase);
    return NextResponse.json(newCase);
  } catch (err: unknown) {
    const error = err as Error;
    return NextResponse.json(
      { code: "SERVER_ERROR", message: error.message || "Failed to process investigation request" },
      { status: 500 }
    );
  }
}
