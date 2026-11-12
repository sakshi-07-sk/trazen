import { NextRequest, NextResponse } from "next/server";
import { requireRole } from "@/lib/auth/rbac";
import {
  createUser,
  listUsers,
  recordAudit,
  sanitizeUser,
} from "@/lib/auth/store";
import { UserRole } from "@/lib/auth/types";

export async function GET(req: NextRequest) {
  const auth = await requireRole(req, ["ADMIN"]);
  if (auth.errorResponse) return auth.errorResponse;

  return NextResponse.json({ users: listUsers() });
}

export async function POST(req: NextRequest) {
  const auth = await requireRole(req, ["ADMIN"]);
  if (auth.errorResponse) return auth.errorResponse;

  try {
    const body = await req.json();
    const fullName = typeof body.fullName === "string" ? body.fullName.trim() : "";
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    const password = typeof body.password === "string" ? body.password : "";
    const organization =
      typeof body.organization === "string" ? body.organization.trim() : "";
    const role = (typeof body.role === "string" ? body.role.trim().toUpperCase() : "") as UserRole;

    if (!["ADMIN", "INVESTIGATOR", "ANALYST"].includes(role)) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Invalid role specified." },
        { status: 400 }
      );
    }

    if (!fullName || !email.includes("@") || password.length < 8 || !organization) {
      return NextResponse.json(
        {
          code: "VALIDATION_ERROR",
          message: "Full name, valid email, organization, and 8+ char password are required.",
        },
        { status: 400 }
      );
    }

    const created = createUser({ fullName, email, password, role, organization });
    recordAudit({
      actorEmail: auth.session.email,
      actorRole: "ADMIN",
      action: "ADMIN_USER_CREATED",
      target: created.email,
      details: `Provisioned ${created.role} account for ${created.organization}.`,
    });

    return NextResponse.json({ user: sanitizeUser(created) }, { status: 201 });
  } catch (err) {
    if (err instanceof Error && err.message === "EMAIL_EXISTS") {
      return NextResponse.json(
        { code: "EMAIL_EXISTS", message: "User with this email already exists." },
        { status: 409 }
      );
    }
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Failed to create user." },
      { status: 500 }
    );
  }
}
