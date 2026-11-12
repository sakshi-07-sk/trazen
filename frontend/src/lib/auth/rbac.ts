import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "./session";
import { SessionPayload, UserRole } from "./types";

export async function getSessionFromRequest(
  req: NextRequest
): Promise<SessionPayload | null> {
  const token = req.cookies.get(SESSION_COOKIE_NAME)?.value;
  return verifySessionToken(token);
}

export async function requireRole(
  req: NextRequest,
  allowedRoles?: UserRole[]
): Promise<
  | { session: SessionPayload; errorResponse?: never }
  | { session?: never; errorResponse: NextResponse }
> {
  const session = await getSessionFromRequest(req);
  if (!session) {
    return {
      errorResponse: NextResponse.json(
        { code: "UNAUTHORIZED", message: "Authentication required." },
        { status: 401 }
      ),
    };
  }

  if (allowedRoles && !allowedRoles.includes(session.role)) {
    return {
      errorResponse: NextResponse.json(
        {
          code: "FORBIDDEN",
          message: `Access denied. Required role: ${allowedRoles.join(" or ")}.`,
        },
        { status: 403 }
      ),
    };
  }

  return { session };
}
