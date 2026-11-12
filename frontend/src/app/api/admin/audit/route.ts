import { NextRequest, NextResponse } from "next/server";
import { requireRole } from "@/lib/auth/rbac";
import { listAuditLogs, listUsers } from "@/lib/auth/store";

export async function GET(req: NextRequest) {
  const auth = await requireRole(req, ["ADMIN"]);
  if (auth.errorResponse) return auth.errorResponse;

  const users = listUsers();
  return NextResponse.json({
    auditLogs: listAuditLogs(),
    metrics: {
      totalUsers: users.length,
      activeInvestigators: users.filter(
        (u) => u.role === "INVESTIGATOR" && u.status === "ACTIVE"
      ).length,
      activeAnalysts: users.filter(
        (u) => u.role === "ANALYST" && u.status === "ACTIVE"
      ).length,
      deactivatedUsers: users.filter((u) => u.status === "DEACTIVATED").length,
    },
  });
}
