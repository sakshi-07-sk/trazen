import { NextRequest, NextResponse } from "next/server";
import {
  getDashboardPathForRole,
  SESSION_COOKIE_NAME,
  signSessionToken,
} from "@/lib/auth/session";
import { createUser, recordAudit, sanitizeUser } from "@/lib/auth/store";
import { PublicSignupRole } from "@/lib/auth/types";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const fullName = typeof body.fullName === "string" ? body.fullName.trim() : "";
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    const password = typeof body.password === "string" ? body.password : "";
    const confirmPassword =
      typeof body.confirmPassword === "string" ? body.confirmPassword : "";
    const organization =
      typeof body.organization === "string" ? body.organization.trim() : "";
    const rawRole = typeof body.role === "string" ? body.role.trim().toUpperCase() : "";
    const termsAccepted = Boolean(body.termsAccepted);

    // Security rule: Never allow public users to register as ADMIN
    if (rawRole === "ADMIN") {
      recordAudit({
        actorEmail: email || "unknown",
        actorRole: "PUBLIC",
        action: "PRIVILEGE_ESCALATION_BLOCKED",
        target: "ADMIN_ROLE",
        details: "Blocked public sign-up attempt requesting ADMIN role.",
      });
      return NextResponse.json(
        {
          code: "FORBIDDEN_ROLE",
          message:
            "Admin accounts cannot be created via public sign-up. Contact an authorized administrator.",
        },
        { status: 403 }
      );
    }

    if (rawRole !== "INVESTIGATOR" && rawRole !== "ANALYST") {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message: "Role must be either INVESTIGATOR or ANALYST.",
        },
        { status: 400 }
      );
    }

    if (!fullName || fullName.length < 2) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Full name is required." },
        { status: 400 }
      );
    }

    if (!EMAIL_RE.test(email)) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Valid email address is required." },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message: "Password must be at least 8 characters long.",
        },
        { status: 400 }
      );
    }

    if (password !== confirmPassword) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Passwords do not match." },
        { status: 400 }
      );
    }

    if (!organization) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Organization is required." },
        { status: 400 }
      );
    }

    if (!termsAccepted) {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message: "You must accept the terms and conditions.",
        },
        { status: 400 }
      );
    }

    const role: PublicSignupRole = rawRole;
    const user = createUser({
      fullName,
      email,
      password,
      role,
      organization,
    });

    const ttlSeconds = 60 * 60 * 12;
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

    recordAudit({
      actorEmail: user.email,
      actorRole: user.role,
      action: "ACCOUNT_REGISTERED",
      target: user.id,
      details: `Registered ${user.role} account for ${user.organization}.`,
    });

    const res = NextResponse.json(
      {
        user: sanitizeUser(user),
        redirectTo: getDashboardPathForRole(user.role),
      },
      { status: 201 }
    );

    res.cookies.set(SESSION_COOKIE_NAME, token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: ttlSeconds,
    });

    return res;
  } catch (err) {
    if (err instanceof Error && err.message === "EMAIL_EXISTS") {
      return NextResponse.json(
        {
          code: "EMAIL_EXISTS",
          message: "An account with this email address already exists.",
        },
        { status: 409 }
      );
    }
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Unable to create account." },
      { status: 500 }
    );
  }
}
