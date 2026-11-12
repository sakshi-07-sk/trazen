"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { PublicSignupRole, PublicUser } from "@/lib/auth/types";

interface AuthContextValue {
  user: PublicUser | null;
  isLoading: boolean;
  refreshSession: () => Promise<void>;
  signIn: (params: {
    email: string;
    password: string;
    rememberMe?: boolean;
  }) => Promise<{ ok: boolean; error?: string; redirectTo?: string }>;
  signUp: (params: {
    fullName: string;
    email: string;
    password: string;
    confirmPassword: string;
    organization: string;
    role: PublicSignupRole;
    termsAccepted: boolean;
  }) => Promise<{ ok: boolean; error?: string; redirectTo?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<PublicUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/me", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user || null);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  const signIn: AuthContextValue["signIn"] = async (params) => {
    try {
      const res = await fetch("/api/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (!res.ok) {
        return { ok: false, error: data.message || "Authentication failed." };
      }
      setUser(data.user);
      return { ok: true, redirectTo: data.redirectTo };
    } catch {
      return { ok: false, error: "Network error during sign-in." };
    }
  };

  const signUp: AuthContextValue["signUp"] = async (params) => {
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (!res.ok) {
        return { ok: false, error: data.message || "Registration failed." };
      }
      setUser(data.user);
      return { ok: true, redirectTo: data.redirectTo };
    } catch {
      return { ok: false, error: "Network error during registration." };
    }
  };

  const signOut = async () => {
    try {
      await fetch("/api/auth/signout", { method: "POST" });
    } finally {
      setUser(null);
      router.push("/signin");
      router.refresh();
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isLoading, refreshSession, signIn, signUp, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
