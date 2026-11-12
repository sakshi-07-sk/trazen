"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Shield,
  LogOut,
  Menu,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  Wifi,
  WifiOff,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useForensic } from "@/context/ForensicContext";
import { UserRole } from "@/lib/auth/types";
import { cn } from "@/lib/utils";

export interface RoleNavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const ROLE_BADGE_STYLES: Record<UserRole, string> = {
  ADMIN: "bg-[#FF6A13]/15 text-[#FF6A13] border-[#FF6A13]/40",
  INVESTIGATOR: "bg-[#FF6A13]/15 text-[#FF6A13] border-[#FF6A13]/40",
  ANALYST: "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/35",
};

export function RoleShell({
  role,
  navItems,
  activeSection,
  onSelectSection,
  title,
  subtitle,
  actions,
  children,
}: {
  role: UserRole;
  navItems: RoleNavItem[];
  activeSection: string;
  onSelectSection: (sectionId: string) => void;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const { user, signOut } = useAuth();
  const { isOnline, settings } = useForensic();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#080909] text-[#F1EEE6] selection:bg-[#FF6A13] selection:text-[#080909] flex font-[family-name:var(--font-archivo)]">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Role-Specific Sidebar */}
      <aside
        className={cn(
          "fixed lg:sticky top-0 left-0 z-50 h-screen bg-[#101111] border-r border-white/10 flex flex-col transition-all duration-200 select-none",
          collapsed ? "w-[72px]" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/10">
          <Link href="/" className="flex items-center gap-2.5 overflow-hidden group">
            <div className="w-8 h-8 rounded-sm bg-[#151616] border border-[#FF6A13]/50 flex items-center justify-center shrink-0 group-hover:border-[#FF6A13] transition-colors">
              <Shield className="w-4 h-4 text-[#FF6A13]" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <span
                  className="block text-base font-bold tracking-[0.12em] uppercase text-[#F1EEE6]"
                  style={{ fontFamily: "var(--font-display), sans-serif" }}
                >
                  CryptoTrace
                </span>
                <span
                  className="block text-[10px] uppercase tracking-[0.18em] text-[#FF6A13]"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  {role} PORTAL
                </span>
              </div>
            )}
          </Link>

          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="hidden lg:flex p-1.5 rounded-sm text-[#A6A39A] hover:text-[#F1EEE6] hover:bg-white/[0.05]"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeftOpen className="w-4 h-4" />
            ) : (
              <PanelLeftClose className="w-4 h-4" />
            )}
          </button>

          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-sm text-[#A6A39A] hover:text-[#F1EEE6]"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activeSection === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  onSelectSection(item.id);
                  setMobileOpen(false);
                }}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-xs uppercase tracking-[0.12em] transition-all border text-left",
                  active
                    ? "bg-[#FF6A13]/12 text-[#FF6A13] border-[#FF6A13]/45"
                    : "text-[#A6A39A] border-transparent hover:text-[#F1EEE6] hover:bg-[#151616]"
                )}
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 shrink-0",
                    active ? "text-[#FF6A13]" : "text-[#A6A39A]"
                  )}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
                {!collapsed && active && (
                  <ChevronRight className="w-3.5 h-3.5 ml-auto text-[#FF6A13]/80" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Logged-in User & Logout */}
        <div className="p-3 border-t border-white/10 space-y-2.5">
          {!collapsed && user && (
            <div className="p-2.5 rounded-sm bg-[#151616] border border-white/10">
              <p className="text-xs font-medium text-[#F1EEE6] truncate">
                {user.fullName}
              </p>
              <p
                className="text-[10px] text-[#A6A39A] truncate"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {user.email}
              </p>
              <span
                className={cn(
                  "inline-block mt-1.5 px-2 py-0.5 rounded-sm border text-[10px] uppercase tracking-[0.12em]",
                  ROLE_BADGE_STYLES[user.role]
                )}
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {user.role}
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={() => signOut()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-sm border border-white/15 bg-[#151616] text-xs uppercase tracking-[0.12em] text-[#A6A39A] hover:text-[#EF4444] hover:border-[#EF4444]/40 transition-colors"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            <LogOut className="w-3.5 h-3.5 shrink-0" />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Column */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-30 h-16 bg-[#080909]/95 backdrop-blur-md border-b border-white/10 px-4 lg:px-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-sm border border-white/15 text-[#A6A39A]"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="min-w-0 flex items-center gap-2.5">
              <span className="h-[1px] w-5 bg-[#FF6A13] hidden sm:inline-block" />
              <p
                className="text-xs uppercase tracking-[0.2em] text-[#FF6A13] truncate"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {role} COMMAND WORKSPACE
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-sm border text-[11px] uppercase tracking-[0.12em]",
                isOnline && !settings.offlineMode
                  ? "bg-[#22C55E]/10 border-[#22C55E]/30 text-[#22C55E]"
                  : "bg-[#F59E0B]/10 border-[#F59E0B]/30 text-[#F59E0B]"
              )}
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              {isOnline && !settings.offlineMode ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              <span className="hidden sm:inline">
                {settings.offlineMode ? "Offline" : isOnline ? "API Live" : "Mock Fallback"}
              </span>
            </div>

            {user && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-sm bg-[#151616] border border-white/10 text-xs">
                <span className="font-medium text-[#F1EEE6]">{user.fullName}</span>
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded-sm border text-[10px] uppercase tracking-[0.12em]",
                    ROLE_BADGE_STYLES[user.role]
                  )}
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  {user.role}
                </span>
              </div>
            )}
          </div>
        </header>

        <div className="border-b border-white/10 bg-[#101111] px-4 lg:px-6 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1
              className="text-2xl sm:text-3xl font-bold uppercase tracking-tight text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              {title}
            </h1>
            {subtitle && (
              <p
                className="text-xs text-[#A6A39A] mt-1 tracking-wide"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>

        <main className="flex-1 p-4 lg:p-6 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
