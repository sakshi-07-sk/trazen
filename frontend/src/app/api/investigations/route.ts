import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { MOCK_ETH_CASE, MOCK_BTC_CASE } from "@/lib/mockData";
import { validateCryptoInput } from "@/lib/validation";
import {
  BACKEND_URL,
  getBackendHeaders,
  mapBackendToInvestigationCase,
} from "@/lib/mapper";
import { getSessionFromRequest } from "@/lib/auth/rbac";
import { InvestigationCase } from "@/types/investigation";

const USE_MOCK = process.env.USE_MOCK === "true";

const mockStore: Map<string, InvestigationCase> = new Map([
  [MOCK_ETH_CASE.caseId, MOCK_ETH_CASE],
  [MOCK_BTC_CASE.caseId, MOCK_BTC_CASE],
]);

export async function GET() {
  if (USE_MOCK) {
    return NextResponse.json(Array.from(mockStore.values()));
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/investigations`, {
      headers: getBackendHeaders(),
      cache: "no-store",
    });

    if (res.status === 404 || res.status === 405) {
      return NextResponse.json([]);
    }
    if (!res.ok) {
      return NextResponse.json(
        { code: "BACKEND_ERROR", message: "Failed to fetch investigations" },
        { status: res.status }
      );
    }

    const payload = await res.json();
    const items = Array.isArray(payload) ? payload : payload.items || [];
    const mapped = items.map((inv: Parameters<typeof mapBackendToInvestigationCase>[0]) =>
      mapBackendToInvestigationCase(inv)
    );
    return NextResponse.json(mapped);
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Unable to reach investigation backend" },
      { status: 502 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const session = await getSessionFromRequest(req);
    if (session && session.role === "ANALYST") {
      return NextResponse.json(
        {
          code: "FORBIDDEN",
          message:
            "Analysts have threat intelligence and risk analysis access only. Creating investigations requires Investigator or Admin clearance.",
        },
        { status: 403 }
      );
    }

    const body = await req.json();
    const { target, network, type, maxHops = 3, timeRange, mode = "auto" } = body;

    const validation = validateCryptoInput(target, network, type);
    if (!validation.isValid) {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message:
            validation.error ||
            "Input target does not meet blockchain network standards.",
        },
        { status: 400 }
      );
    }

    const detectedNetwork = validation.detectedNetwork || network || "ETH";
    const detectedType = validation.detectedType || type || "address";

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
              "Live ingestion failed: No archive RPC provider credentials are configured in the environment.",
          },
          { status: 503 }
        );
      }
    }

    if (USE_MOCK) {
      const normalizedTarget = target.toLowerCase();
      if (normalizedTarget === MOCK_ETH_CASE.target.toLowerCase()) {
        return NextResponse.json(MOCK_ETH_CASE);
      }
      if (normalizedTarget === MOCK_BTC_CASE.target.toLowerCase()) {
        return NextResponse.json(MOCK_BTC_CASE);
      }

      const newCaseId = `CT-CASE-${crypto.randomUUID()}`;
      const nowISO = new Date().toISOString();
      const newCase: InvestigationCase = {
        ...MOCK_ETH_CASE,
        caseId: newCaseId,
        title: `Forensic Ingress Trace: ${target.substring(0, 10)}... [${detectedNetwork}]`,
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
      };
      mockStore.set(newCaseId, newCase);
      return NextResponse.json(newCase);
    }

    const blockchain = detectedNetwork === "BTC" ? "bitcoin" : "ethereum";
    const clampedHops = Math.min(3, Math.max(1, Number(maxHops) || 2));
    const backendPayload = {
      title: `Forensic Trace: ${target.substring(0, 12)} [${detectedNetwork}]`,
      description: `Automated ingress trace (${detectedType})`,
      blockchain,
      target_address: target,
      max_hops: clampedHops,
      start_time: timeRange?.from || null,
      end_time: timeRange?.to || null,
      tags: [detectedNetwork.toLowerCase(), detectedType],
    };

    const createRes = await fetch(`${BACKEND_URL}/api/v1/investigations`, {
      method: "POST",
      headers: getBackendHeaders(),
      body: JSON.stringify(backendPayload),
    });

    if (!createRes.ok) {
      return NextResponse.json(
        { code: "BACKEND_ERROR", message: "Failed to create investigation" },
        { status: createRes.status }
      );
    }

    const inv = await createRes.json();
    const graphRes = await fetch(
      `${BACKEND_URL}/api/v1/investigations/${encodeURIComponent(inv.id)}/graph`,
      { headers: getBackendHeaders(), cache: "no-store" }
    );
    const graph = graphRes.ok ? await graphRes.json() : null;

    return NextResponse.json(mapBackendToInvestigationCase(inv, graph));
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Failed to process investigation request" },
      { status: 500 }
    );
  }
}
