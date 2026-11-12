import { NextRequest, NextResponse } from "next/server";
import { MOCK_ETH_CASE, MOCK_BTC_CASE } from "@/lib/mockData";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const caseId = decodeURIComponent(params.id);

  if (caseId === MOCK_ETH_CASE.caseId || caseId.includes("8841") || caseId.toLowerCase() === "demo-eth") {
    return NextResponse.json(MOCK_ETH_CASE);
  }

  if (caseId === MOCK_BTC_CASE.caseId || caseId.includes("0428") || caseId.toLowerCase() === "demo-btc") {
    return NextResponse.json(MOCK_BTC_CASE);
  }

  // Fallback default demo if case not found
  return NextResponse.json(MOCK_ETH_CASE);
}
