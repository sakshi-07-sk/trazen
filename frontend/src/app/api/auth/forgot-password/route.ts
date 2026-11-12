import { NextRequest, NextResponse } from "next/server";
import { createResetToken, recordAudit } from "@/lib/auth/store";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";

    if (!email || !email.includes("@")) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "Valid email address is required." },
        { status: 400 }
      );
    }

    const token = createResetToken(email);
    recordAudit({
      actorEmail: email,
      actorRole: "PUBLIC",
      action: "PASSWORD_RESET_REQUESTED",
      target: email,
      details: token
        ? "Issued time-limited password reset token."
        : "Reset requested for unrecognized email (suppressed in response).",
    });

    return NextResponse.json({
      message:
        "If an active account matches that email, password recovery instructions have been dispatched.",
    });
  } catch {
    return NextResponse.json(
      { code: "SERVER_ERROR", message: "Unable to process password reset request." },
      { status: 500 }
    );
  }
}
