"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Lock, Mail, Shield, ArrowRight, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const DEMO_ACCOUNTS = [
  {
    label: "Admin Demo",
    email: "admin@cryptotrace.io",
    password: "AdminTrace!2025",
    role: "ADMIN",
  },
  {
    label: "Investigator Demo",
    email: "investigator@cryptotrace.io",
    password: "Investigator!2025",
    role: "INVESTIGATOR",
  },
  {
    label: "Analyst Demo",
    email: "analyst@cryptotrace.io",
    password: "Analyst!2025",
    role: "ANALYST",
  },
];

export default function SignInPage() {
  const router = useRouter();
  const { signIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await signIn({ email, password, rememberMe });
    setIsSubmitting(false);

    if (!result.ok) {
      setError(result.error || "Invalid credentials.");
      return;
    }

    router.push(result.redirectTo || "/dashboard");
    router.refresh();
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
          <div className="mb-6">
            <div className="inline-flex items-center gap-2.5 mb-1.5">
              <span className="h-[1px] w-5 bg-[#FF6A13]" />
              <p
                className="text-[11px] uppercase tracking-[0.22em] text-[#FF6A13]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                SECURE ACCESS PORTAL
              </p>
            </div>
            <h1
              className="text-3xl font-extrabold uppercase tracking-tight text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Sign In
            </h1>
            <p className="text-xs text-[#A6A39A] mt-1">
              Authenticate to access your role-specific forensic workspace.
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
            <div>
              <label
                htmlFor="signin-email"
                className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A6A39A] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="signin-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@cryptotrace.io"
                  className="w-full h-10 pl-9 pr-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="signin-password"
                className="block text-xs uppercase tracking-[0.12em] text-[#A6A39A] mb-1.5"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#A6A39A] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="signin-password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full h-10 pl-9 pr-10 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] placeholder:text-[#A6A39A]/50 focus:outline-none focus:border-[#FF6A13]"
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

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 text-[#A6A39A] cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="accent-[#FF6A13]"
                />
                <span>Remember me (7 days)</span>
              </label>
              <Link
                href="/forgot-password"
                className="font-mono text-[#FF6A13] hover:text-[#FF812E] hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-10 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors inline-flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              {isSubmitting ? "Authenticating..." : "Sign In"}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Local Demo Account Helpers */}
          <div className="mt-6 pt-5 border-t border-white/10">
            <p
              className="text-[10px] uppercase tracking-[0.18em] text-[#A6A39A] mb-2.5"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              Demo Credentials (Non-Production)
            </p>
            <div className="grid grid-cols-3 gap-2">
              {DEMO_ACCOUNTS.map((demo) => (
                <button
                  key={demo.role}
                  type="button"
                  onClick={() => {
                    setEmail(demo.email);
                    setPassword(demo.password);
                  }}
                  className="px-2 py-1.5 rounded-sm bg-[#080909] border border-white/15 hover:border-[#FF6A13] hover:text-[#FF6A13] text-[10px] font-mono text-[#F1EEE6] transition-colors"
                >
                  {demo.role}
                </button>
              ))}
            </div>
          </div>

          <p className="mt-6 text-center text-xs text-[#A6A39A]">
            Need an Investigator or Analyst account?{" "}
            <Link href="/signup" className="text-[#FF6A13] hover:text-[#FF812E] font-mono hover:underline">
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
