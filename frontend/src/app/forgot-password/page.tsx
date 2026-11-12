"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Mail, Shield, AlertCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setMessage("");

    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatus("error");
        setMessage(data.message || "Unable to process request.");
        return;
      }
      setStatus("sent");
      setMessage(data.message);
    } catch {
      setStatus("error");
      setMessage("Network error while requesting password reset.");
    }
  };

  return (
    <div className="min-h-screen bg-[#080909] text-[#F1EEE6] selection:bg-[#FF6A13] selection:text-[#080909] flex flex-col justify-center items-center p-6 relative overflow-hidden font-[family-name:var(--font-archivo)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,106,19,0.08),transparent_45%)] pointer-events-none" />
      <div className="w-full max-w-md relative z-10">
        <Link href="/" className="flex items-center justify-center gap-2.5 mb-8 group">
          <div className="w-9 h-9 rounded-sm bg-[#151616] border border-[#FF6A13]/50 group-hover:border-[#FF6A13] flex items-center justify-center transition-colors">
            <Shield className="w-4 h-4 text-[#FF6A13]" />
          </div>
          <span
            className="text-xl font-bold tracking-[0.12em] uppercase text-[#F1EEE6]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            CryptoTrace
          </span>
        </Link>

        <div className="rounded-sm border border-white/10 bg-[#151616]/95 backdrop-blur-md p-7 shadow-2xl">
          <div className="inline-flex items-center gap-2.5 mb-1.5">
            <span className="h-[1px] w-5 bg-[#FF6A13]" />
            <p
              className="text-[11px] uppercase tracking-[0.22em] text-[#FF6A13]"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              CREDENTIAL RECOVERY
            </p>
          </div>
          <h1
            className="text-3xl font-extrabold uppercase tracking-tight text-[#F1EEE6]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            Forgot Password
          </h1>
          <p className="text-xs text-[#A6A39A] mt-1 mb-5">
            Enter your registered email address to request a recovery link.
          </p>

          {status === "sent" && (
            <div className="mb-4 p-3.5 rounded-sm bg-[#22C55E]/10 border border-[#22C55E]/35 text-xs text-[#22C55E] flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{message}</span>
            </div>
          )}

          {status === "error" && (
            <div className="mb-4 p-3.5 rounded-sm bg-[#EF4444]/10 border border-[#EF4444]/35 text-xs text-[#EF4444] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{message}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="reset-email"
                className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A6A39A] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="reset-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@cryptotrace.io"
                  className="w-full h-10 pl-9 pr-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={status === "submitting"}
              className="w-full h-10 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors disabled:opacity-60"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              {status === "submitting" ? "Dispatching..." : "Request Recovery Link"}
            </button>
          </form>

          <Link
            href="/signin"
            className="mt-6 inline-flex items-center gap-1.5 text-xs font-mono text-[#A6A39A] hover:text-[#FF6A13]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
