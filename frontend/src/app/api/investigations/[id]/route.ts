import { NextRequest, NextResponse } from "next/server";
import { MOCK_ETH_CASE, MOCK_BTC_CASE } from "@/lib/mockData";
import {
  BACKEND_URL,
  getBackendHeaders,
  mapBackendToInvestigationCase,
} from "@/lib/mapper";

const USE_MOCK = process.env.USE_MOCK === "true";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const caseId = decodeURIComponent(params.id);

  if (USE_MOCK) {
    if (
      caseId === MOCK_BTC_CASE.caseId ||
      caseId.includes("0428") ||
      caseId.toLowerCase() === "demo-btc"
    ) {
      return NextResponse.json(MOCK_BTC_CASE);
    }
    return NextResponse.json(MOCK_ETH_CASE);
  }

  try {
    const headers = getBackendHeaders();
    const invRes = await fetch(
      `${BACKEND_URL}/api/v1/investigations/${encodeURIComponent(caseId)}`,
      { headers, cache: "no-store" }
    );
    if (!invRes.ok) {
      return NextResponse.json(
        { code: "NOT_FOUND", message: "Investigation not found" },
        { status: invRes.status }
      );
    }

    const inv = await invRes.json();
    const [graphRes, findingsRes, riskRes] = await Promise.all([
      fetch(
        `${BACKEND_URL}/api/v1/investigations/${encodeURIComponent(caseId)}/graph`,
        { headers, cache: "no-store" }
      ),
      fetch(
        `${BACKEND_URL}/api/v1/investigations/${encodeURIComponent(caseId)}/findings`,
        { headers, cache: "no-store" }
      ),
      fetch(
        `${BACKEND_URL}/api/v1/investigations/${encodeURIComponent(caseId)}/risk`,
        { headers, cache: "no-store" }
      ),
    ]);

    const graph = graphRes.ok ? await graphRes.json() : null;
    const findings = findingsRes.ok ? await findingsRes.json() : null;
    const risk = riskRes.ok ? await riskRes.json() : null;

    return NextResponse.json(
      mapBackendToInvestigationCase(inv, graph, findings, risk)
    );
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Failed to retrieve investigation details" },
      { status: 502 }
    );
  }
}
