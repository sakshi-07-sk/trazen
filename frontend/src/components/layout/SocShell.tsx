"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  Network,
  AlertTriangle,
  Gauge,
  ShieldCheck,
  FileText,
  Bot,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Command,
  Wifi,
  WifiOff,
  RefreshCw,
  User,
  Menu,
  X,
  ChevronRight,
  Shield,
} from "lucide-react";
import { useForensic } from "@/context/ForensicContext";
import { TraceAICopilotPanel } from "@/features/copilot/TraceAICopilotPanel";
import { cn, getCaseRiskScore } from "@/lib/utils";
import { BlockchainNetwork } from "@/types/investigation";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Investigations", href: "/investigations", icon: FolderKanban },
  { label: "Graph Explorer", href: "/graph", icon: Network },
  { label: "Findings", href: "/findings", icon: AlertTriangle },
  { label: "Risk Intelligence", href: "/risk", icon: Gauge },
  { label: "Evidence Vault", href: "/evidence", icon: ShieldCheck },
  { label: "Reports", href: "/reports", icon: FileText },
  { label: "TraceAI Copilot", href: "/copilot", icon: Bot },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function SocShell({
  children,
  title,
  subtitle,
  actions,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const {
    activeCase,
    networkFilter,
    setNetworkFilter,
    globalSearch,
    setGlobalSearch,
    isOnline,
    isLoading,
    refreshData,
    isCopilotOpen,
    setIsCopilotOpen,
    setIsCommandPaletteOpen,
    settings,
  } = useForensic();

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const isActive = (href: string) =>
    href === "/investigations"
      ? pathname === "/investigations" || pathname.startsWith("/investigations/")
      : pathname === href;

  const networks: ("ALL" | BlockchainNetwork)[] = ["ALL", "ETH", "BTC"];

  return (
    <div className="min-h-screen bg-[#080909] text-[#F1EEE6] selection:bg-[#FF6A13] selection:text-[#080909] flex font-[family-name:var(--font-archivo)]">
      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <aside
        className={cn(
          "fixed lg:sticky top-0 left-0 z-50 h-screen bg-[#101111] border-r border-white/10 flex flex-col transition-all duration-200 select-none",
          collapsed ? "w-[72px]" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand Header */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/10">
          <Link
            href="/"
            className="flex items-center gap-2.5 overflow-hidden group"
            title="CryptoTrace Landing"
          >
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
                  Forensic SOC
                </span>
              </div>
            )}
          </Link>

          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="hidden lg:flex p-1.5 rounded-sm text-[#A6A39A] hover:text-[#F1EEE6] hover:bg-white/[0.05] transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
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

        {/* Active Case Context Pill */}
        {!collapsed && (
          <div className="px-3 pt-3 pb-2">
            <Link
              href={`/investigations/${activeCase.caseId}`}
              className="block p-2.5 rounded-sm bg-[#151616] border border-white/10 hover:border-[#FF6A13]/50 transition-colors"
            >
              <div
                className="flex items-center justify-between text-[10px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                <span>Active Case</span>
                <span className="text-[#FF6A13]">{activeCase.network}</span>
              </div>
              <div className="mt-1 flex items-center justify-between gap-2">
                <span
                  className="text-xs text-[#F1EEE6] truncate"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  {activeCase.caseId}
                </span>
                <span
                  className="text-[11px] text-[#FF6A13] shrink-0"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  [ {getCaseRiskScore(activeCase)} / 100 ]
                </span>
              </div>
            </Link>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto px-2.5 py-2 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-sm text-xs uppercase tracking-[0.12em] transition-all border",
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
              </Link>
            );
          })}
        </nav>

        {/* Bottom Status Footer */}
        <div className="p-3 border-t border-white/10">
          {!collapsed ? (
            <div
              className="flex items-center justify-between text-[11px] text-[#A6A39A]"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              <span className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    isOnline && !settings.offlineMode
                      ? "bg-[#22C55E] shadow-[0_0_8px_#22C55E]"
                      : "bg-[#F59E0B]"
                  )}
                />
                {settings.offlineMode
                  ? "OFFLINE MOCK"
                  : isOnline
                  ? "API LIVE"
                  : "FALLBACK MOCK"}
              </span>
              <span className="text-[10px] text-[#A6A39A]/70">v2.0</span>
            </div>
          ) : (
            <div className="flex justify-center">
              <span
                className={cn(
                  "w-2.5 h-2.5 rounded-full",
                  isOnline && !settings.offlineMode ? "bg-[#22C55E]" : "bg-[#F59E0B]"
                )}
                title={isOnline ? "API Live" : "Mock Fallback"}
              />
            </div>
          )}
        </div>
      </aside>

      {/* Main Column */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 h-16 bg-[#080909]/95 backdrop-blur-md border-b border-white/10 px-4 lg:px-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-sm border border-white/15 text-[#A6A39A] hover:text-[#F1EEE6]"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>

            {/* Global Search */}
            <div className="relative flex-1 max-w-md hidden sm:block">
              <Search className="w-3.5 h-3.5 text-[#A6A39A] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={globalSearch}
                onChange={(e) => setGlobalSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && globalSearch.trim()) {
                    router.push("/investigations");
                  }
                }}
                placeholder="Search wallet, tx hash, case ID..."
                className="w-full h-9 pl-9 pr-16 rounded-sm bg-[#151616] border border-white/10 text-xs text-[#F1EEE6] placeholder:text-[#A6A39A]/60 focus:outline-none focus:border-[#FF6A13]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              />
              <button
                type="button"
                onClick={() => setIsCommandPaletteOpen(true)}
                className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-1.5 py-0.5 rounded-sm bg-white/[0.04] border border-white/10 text-[10px] text-[#A6A39A] hover:text-[#FF6A13]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                title="Open Command Palette"
              >
                <Command className="w-2.5 h-2.5" />K
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Network Switcher */}
            <div
              className="hidden md:flex items-center p-0.5 rounded-sm bg-[#151616] border border-white/10"
              role="group"
              aria-label="Blockchain Network Filter"
            >
              {networks.map((net) => (
                <button
                  key={net}
                  type="button"
                  onClick={() => setNetworkFilter(net)}
                  className={cn(
                    "px-2.5 py-1 rounded-sm text-[11px] uppercase tracking-[0.12em] transition-colors",
                    networkFilter === net
                      ? "bg-[#FF6A13]/15 text-[#FF6A13] border border-[#FF6A13]/40"
                      : "text-[#A6A39A] hover:text-[#F1EEE6]"
                  )}
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  {net}
                </button>
              ))}
            </div>

            {/* Online / Refresh Badge */}
            <button
              type="button"
              onClick={() => refreshData()}
              disabled={isLoading}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-sm border text-[11px] uppercase tracking-[0.12em] transition-colors",
                isOnline && !settings.offlineMode
                  ? "bg-[#22C55E]/10 border-[#22C55E]/30 text-[#22C55E]"
                  : "bg-[#F59E0B]/10 border-[#F59E0B]/30 text-[#F59E0B]"
              )}
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              title="Click to sync with backend APIs"
            >
              {isLoading ? (
                <RefreshCw className="w-3 h-3 animate-spin" />
              ) : isOnline && !settings.offlineMode ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              <span className="hidden sm:inline">
                {settings.offlineMode ? "Offline" : isOnline ? "Online" : "Mock"}
              </span>
            </button>

            {/* Profile Menu */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setProfileOpen((p) => !p)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-sm bg-[#151616] border border-white/10 hover:border-[#FF6A13]/50 text-xs transition-colors"
                aria-label="Investigator profile"
              >
                <div className="w-5 h-5 rounded-sm bg-[#FF6A13]/15 border border-[#FF6A13]/40 flex items-center justify-center">
                  <User className="w-3 h-3 text-[#FF6A13]" />
                </div>
                <span
                  className="hidden md:inline text-[11px] text-[#F1EEE6]"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Analyst-01
                </span>
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-52 rounded-sm bg-[#151616] border border-white/15 shadow-2xl p-2 z-50">
                  <div className="px-2.5 py-2 border-b border-white/10">
                    <p className="text-xs font-medium text-[#F1EEE6]">
                      Senior Forensic Analyst
                    </p>
                    <p
                      className="text-[11px] text-[#A6A39A]"
                      style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                    >
                      Role 1 + Role 2 Clearance
                    </p>
                  </div>
                  <div className="pt-1.5 space-y-1">
                    <Link
                      href="/settings"
                      onClick={() => setProfileOpen(false)}
                      className="block px-2.5 py-1.5 rounded-sm text-xs text-[#A6A39A] hover:text-[#F1EEE6] hover:bg-white/[0.05]"
                    >
                      Platform Settings
                    </Link>
                    <Link
                      href="/"
                      onClick={() => setProfileOpen(false)}
                      className="block px-2.5 py-1.5 rounded-sm text-xs text-[#A6A39A] hover:text-[#F1EEE6] hover:bg-white/[0.05]"
                    >
                      Landing Showcase
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Optional Page Subheader */}
        {(title || actions) && (
          <div className="border-b border-white/10 bg-[#101111] px-4 lg:px-6 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              {title && (
                <h1
                  className="text-2xl sm:text-3xl font-bold uppercase tracking-tight text-[#F1EEE6]"
                  style={{ fontFamily: "var(--font-display), sans-serif" }}
                >
                  {title}
                </h1>
              )}
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
        )}

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Floating TraceAI Copilot Button */}
      {!isCopilotOpen && (
        <button
          type="button"
          onClick={() => setIsCopilotOpen(true)}
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2 px-4 py-2.5 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] font-semibold shadow-[0_0_24px_rgba(255,106,19,0.28)] transition-all print:hidden"
          aria-label="Open TraceAI Copilot"
        >
          <Bot className="w-4 h-4" />
          <span
            className="text-xs uppercase tracking-[0.14em]"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            TraceAI
          </span>
        </button>
      )}

      {/* TraceAI Copilot Drawer */}
      <TraceAICopilotPanel
        investigation={activeCase}
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onSelectEvidence={() => router.push("/evidence")}
        onSelectFinding={() => router.push("/findings")}
      />
    </div>
  );
}
