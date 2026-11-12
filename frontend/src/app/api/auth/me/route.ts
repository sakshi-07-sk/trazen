import { NextRequest, NextResponse } from "next/server";
import { requireRole } from "@/lib/auth/rbac";
import { findUserById, sanitizeUser } from "@/lib/auth/store";

export async function GET(req: NextRequest) {
  const auth = await requireRole(req);
  if (auth.errorResponse) return auth.errorResponse;

  const user = findUserById(auth.session.userId);
  if (!user || user.status !== "ACTIVE") {
    return NextResponse.json(
      { code: "UNAUTHORIZED", message: "Session is no longer active." },
      { status: 401 }
    );
  }

  return NextResponse.json({ user: sanitizeUser(user) });
}
