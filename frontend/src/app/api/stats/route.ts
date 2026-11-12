import { NextResponse } from "next/server";
import { MOCK_STATS } from "@/lib/mockData";

export async function GET() {
  return NextResponse.json(MOCK_STATS);
}
