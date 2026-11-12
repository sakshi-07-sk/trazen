import { NextResponse } from "next/server";
import { MOCK_STATS } from "@/lib/mockData";
import {
  BACKEND_URL,
  buildStatsFromCases,
  getBackendHeaders,
  mapBackendToInvestigationCase,
} from "@/lib/mapper";

const USE_MOCK = process.env.USE_MOCK === "true";

export async function GET() {
  if (USE_MOCK) {
    return NextResponse.json(MOCK_STATS);
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/investigations`, {
      headers: getBackendHeaders(),
      cache: "no-store",
    });

    if (res.status === 404 || res.status === 405) {
      return NextResponse.json(
        buildStatsFromCases([])
      );
    }
    if (!res.ok) {
      return NextResponse.json(
        { code: "BACKEND_ERROR", message: "Failed to fetch statistics" },
        { status: res.status }
      );
    }

    const payload = await res.json();
    const items = Array.isArray(payload) ? payload : payload.items || [];
    const cases = items.map((inv: Parameters<typeof mapBackendToInvestigationCase>[0]) =>
      mapBackendToInvestigationCase(inv)
    );
    return NextResponse.json(buildStatsFromCases(cases));
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Unable to reach statistics backend" },
      { status: 502 }
    );
  }
}
