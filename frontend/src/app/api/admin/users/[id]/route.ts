import { NextRequest, NextResponse } from "next/server";
import { requireRole } from "@/lib/auth/rbac";
import { recordAudit, updateUserById } from "@/lib/auth/store";
import { UserRole, UserStatus } from "@/lib/auth/types";

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const auth = await requireRole(req, ["ADMIN"]);
  if (auth.errorResponse) return auth.errorResponse;

  try {
    const body = await req.json();
    const patch: { role?: UserRole; status?: UserStatus } = {};

    if (typeof body.role === "string") {
      const role = body.role.trim().toUpperCase() as UserRole;
      if (!["ADMIN", "INVESTIGATOR", "ANALYST"].includes(role)) {
        return NextResponse.json(
          { code: "VALIDATION_ERROR", message: "Invalid role." },
          { status: 400 }
        );
      }
      patch.role = role;
    }

    if (typeof body.status === "string") {
      const status = body.status.trim().toUpperCase() as UserStatus;
      if (status !== "ACTIVE" && status !== "DEACTIVATED") {
        return NextResponse.json(
          { code: "VALIDATION_ERROR", message: "Invalid account status." },
          { status: 400 }
        );
      }
      if (params.id === auth.session.userId && status === "DEACTIVATED") {
        return NextResponse.json(
          {
            code: "SELF_DEACTIVATION_BLOCKED",
            message: "Administrators cannot deactivate their own active account.",
          },
          { status: 400 }
        );
      }
      patch.status = status;
    }

    const updated = updateUserById(params.id, patch);
    if (!updated) {
      return NextResponse.json(
        { code: "NOT_FOUND", message: "User not found." },
        { status: 404 }
      );
    }

    recordAudit({
      actorEmail: auth.session.email,
      actorRole: "ADMIN",
      action: "ADMIN_USER_UPDATED",
      target: updated.email,
      details: `Updated user (${Object.entries(patch)
        .map(([k, v]) => `${k}=${v}`)
        .join(", ")}).`,
    });

    return NextResponse.json({ user: updated });
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Failed to update user." },
      { status: 500 }
    );
  }
}
