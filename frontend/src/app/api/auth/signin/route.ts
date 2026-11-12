import { NextRequest, NextResponse } from "next/server";
import { verifyPassword } from "@/lib/auth/password";
import {
  getDashboardPathForRole,
  SESSION_COOKIE_NAME,
  signSessionToken,
} from "@/lib/auth/session";
import {
  findUserByEmail,
  recordAudit,
  sanitizeUser,
  updateUserById,
} from "@/lib/auth/store";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    const password = typeof body.password === "string" ? body.password : "";
    const rememberMe = Boolean(body.rememberMe);

    if (!email || !password) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Email and password are required." },
        { status: 400 }
      );
    }

    const user = findUserByEmail(email);
    if (!user || !verifyPassword(password, user.passwordHash)) {
      recordAudit({
        actorEmail: email || "unknown",
        actorRole: "PUBLIC",
        action: "SIGNIN_FAILED",
        target: email,
        details: "Invalid email or password attempt.",
      });
      return NextResponse.json(
        { code: "INVALID_CREDENTIALS", message: "Invalid email or password." },
        { status: 401 }
      );
    }

    if (user.status !== "ACTIVE") {
      return NextResponse.json(
        {
          code: "ACCOUNT_DEACTIVATED",
          message: "This account has been deactivated by an administrator.",
        },
        { status: 403 }
      );
    }

    const ttlSeconds = rememberMe ? 60 * 60 * 24 * 7 : 60 * 60 * 12;
    const token = await signSessionToken(
      {
        userId: user.id,
        email: user.email,
        fullName: user.fullName,
        role: user.role,
        organization: user.organization,
      },
      ttlSeconds
    );

    updateUserById(user.id, { lastLoginAt: new Date().toISOString() });
    recordAudit({
      actorEmail: user.email,
      actorRole: user.role,
      action: "SIGNIN_SUCCESS",
      target: user.id,
      details: `Authenticated session established (${rememberMe ? "7d" : "12h"}).`,
    });

    const res = NextResponse.json({
      user: sanitizeUser(user),
      redirectTo: getDashboardPathForRole(user.role),
    });

    res.cookies.set(SESSION_COOKIE_NAME, token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: ttlSeconds,
    });

    return res;
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Unable to process sign-in request." },
      { status: 500 }
    );
  }
}
