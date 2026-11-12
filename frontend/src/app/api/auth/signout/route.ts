import { NextRequest, NextResponse } from "next/server";
import { getSessionFromRequest } from "@/lib/auth/rbac";
import { SESSION_COOKIE_NAME } from "@/lib/auth/session";
import { recordAudit } from "@/lib/auth/store";

export async function POST(req: NextRequest) {
  const session = await getSessionFromRequest(req);
  if (session) {
    recordAudit({
      actorEmail: session.email,
      actorRole: session.role,
      action: "SIGNOUT",
      target: session.userId,
      details: "User terminated active session.",
    });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return res;
}
