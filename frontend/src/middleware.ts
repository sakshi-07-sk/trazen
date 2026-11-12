import { NextRequest, NextResponse } from "next/server";
import {
  getDashboardPathForRole,
  SESSION_COOKIE_NAME,
  verifySessionToken,
} from "@/lib/auth/session";

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const token = req.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = await verifySessionToken(token);

  const isAdminRoute = pathname.startsWith("/admin");
  const isInvestigatorRoute = pathname.startsWith("/investigator");
  const isAnalystRoute = pathname.startsWith("/analyst");
  const isProtectedRoleRoute = isAdminRoute || isInvestigatorRoute || isAnalystRoute;

  if (isProtectedRoleRoute) {
    if (!session) {
      const signinUrl = new URL("/signin", req.url);
      signinUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(signinUrl);
    }

    if (isAdminRoute && session.role !== "ADMIN") {
      const redirectUrl = new URL(getDashboardPathForRole(session.role), req.url);
      redirectUrl.searchParams.set("unauthorized", "1");
      return NextResponse.redirect(redirectUrl);
    }

    if (isInvestigatorRoute && session.role !== "INVESTIGATOR") {
      const redirectUrl = new URL(getDashboardPathForRole(session.role), req.url);
      redirectUrl.searchParams.set("unauthorized", "1");
      return NextResponse.redirect(redirectUrl);
    }

    if (isAnalystRoute && session.role !== "ANALYST") {
      const redirectUrl = new URL(getDashboardPathForRole(session.role), req.url);
      redirectUrl.searchParams.set("unauthorized", "1");
      return NextResponse.redirect(redirectUrl);
    }
  }

  if ((pathname === "/signin" || pathname === "/signup") && session) {
    return NextResponse.redirect(new URL(getDashboardPathForRole(session.role), req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/admin/:path*",
    "/investigator/:path*",
    "/analyst/:path*",
    "/signin",
    "/signup",
  ],
};
