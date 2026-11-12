"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  ArrowRight,
  AlertCircle,
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { PublicSignupRole } from "@/lib/auth/types";
import { cn } from "@/lib/utils";

export default function SignUpPage() {
  const router = useRouter();
  const { signUp } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState<PublicSignupRole>("INVESTIGATOR");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!termsAccepted) {
      setError("You must accept the terms and conditions.");
      return;
    }

    setIsSubmitting(true);
    const result = await signUp({
      fullName,
      email,
      password,
      confirmPassword,
      organization,
      role,
      termsAccepted,
    });
    setIsSubmitting(false);

    if (!result.ok) {
      setError(result.error || "Unable to create account.");
      return;
    }

    router.push(result.redirectTo || "/investigator/dashboard");
    router.refresh();
  };

  return (
    <div className="min-h-screen bg-[#080909] text-[#F1EEE6] selection:bg-[#FF6A13] selection:text-[#080909] flex flex-col justify-center items-center p-6 relative overflow-hidden font-[family-name:var(--font-archivo)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(255,106,19,0.08),transparent_45%)] pointer-events-none" />

      <div className="w-full max-w-lg relative z-10">
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
          <div className="mb-5">
            <div className="inline-flex items-center gap-2.5 mb-1.5">
              <span className="h-[1px] w-5 bg-[#FF6A13]" />
              <p
                className="text-[11px] uppercase tracking-[0.22em] text-[#FF6A13]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                FORENSIC ONBOARDING
              </p>
            </div>
            <h1
              className="text-3xl font-extrabold uppercase tracking-tight text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Create Account
            </h1>
            <p className="text-xs text-[#A6A39A] mt-1">
              Register as an Investigator or Threat Intelligence Analyst.
            </p>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 p-3 rounded-sm bg-[#EF4444]/10 border border-[#EF4444]/35 text-xs text-[#EF4444] flex items-center gap-2"
            >
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="signup-name"
                  className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Full Name
                </label>
                <input
                  id="signup-name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Alex Mercer"
                  className="w-full h-10 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                />
              </div>

              <div>
                <label
                  htmlFor="signup-org"
                  className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Organization
                </label>
                <input
                  id="signup-org"
                  type="text"
                  required
                  value={organization}
                  onChange={(e) => setOrganization(e.target.value)}
                  placeholder="Cyber Forensics Unit"
                  className="w-full h-10 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="signup-email"
                className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Work Email
              </label>
              <input
                id="signup-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@organization.io"
                className="w-full h-10 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
              />
            </div>

            {/* Role Selection: Strictly Investigator or Analyst */}
            <div>
              <span
                className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Select Workspace Role
              </span>
              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    {
                      id: "INVESTIGATOR",
                      title: "Investigator",
                      desc: "Wallet tracing, graphs & evidence",
                    },
                    {
                      id: "ANALYST",
                      title: "Analyst",
                      desc: "Threat intel, risk & pattern alerts",
                    },
                  ] as const
                ).map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setRole(opt.id)}
                    className={cn(
                      "p-3 rounded-sm border text-left transition-colors",
                      role === opt.id
                        ? "bg-[#FF6A13]/12 border-[#FF6A13]/60"
                        : "bg-[#080909] border-white/15 hover:border-white/30"
                    )}
                  >
                    <p className="text-xs font-mono font-semibold text-[#F1EEE6]">
                      {opt.title}
                    </p>
                    <p className="text-[11px] text-[#A6A39A] mt-0.5">{opt.desc}</p>
                  </button>
                ))}
              </div>
              <p className="mt-1.5 text-[10px] font-mono text-[#A6A39A] flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-[#22C55E]" />
                Admin accounts can only be provisioned by an existing authorized Admin.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="signup-password"
                  className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Password (8+ chars)
                </label>
                <div className="relative">
                  <input
                    id="signup-password"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
                    className="w-full h-10 pl-3 pr-9 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#A6A39A] hover:text-[#F1EEE6]"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label
                  htmlFor="signup-confirm"
                  className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Confirm Password
                </label>
                <input
                  id="signup-confirm"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  className="w-full h-10 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                />
              </div>
            </div>

            <label className="flex items-start gap-2 text-xs text-[#A6A39A] cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="accent-[#FF6A13] mt-0.5"
              />
              <span>
                I agree to the CryptoTrace Forensic Terms of Service and chain-of-custody
                audit logging policy.
              </span>
            </label>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-10 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors inline-flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              {isSubmitting ? "Creating Account..." : "Create Account"}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-[#A6A39A]">
            Already have an account?{" "}
            <Link href="/signin" className="text-[#FF6A13] hover:text-[#FF812E] font-mono hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
