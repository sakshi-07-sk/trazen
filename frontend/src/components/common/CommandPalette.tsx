"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Bot,
  FileText,
  FolderSearch,
  LayoutDashboard,
  Network,
  Search,
  Settings,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import { useForensic } from "@/context/ForensicContext";

const NAV_COMMANDS = [
  { label: "SOC Dashboard", href: "/dashboard", icon: LayoutDashboard, group: "Navigation" },
  { label: "Investigations", href: "/investigations", icon: FolderSearch, group: "Navigation" },
  { label: "Forensic Graph", href: "/graph", icon: Network, group: "Navigation" },
  { label: "Findings & Patterns", href: "/findings", icon: ShieldAlert, group: "Navigation" },
  { label: "Risk Intelligence", href: "/risk", icon: Activity, group: "Navigation" },
  { label: "Evidence Vault", href: "/evidence", icon: ShieldCheck, group: "Navigation" },
  { label: "Report Generator", href: "/reports", icon: FileText, group: "Navigation" },
  { label: "TraceAI Copilot", href: "/copilot", icon: Bot, group: "Navigation" },
  { label: "Platform Settings", href: "/settings", icon: Settings, group: "Navigation" },
];

export function CommandPalette() {
  const router = useRouter();
  const {
    isCommandPaletteOpen,
    setIsCommandPaletteOpen,
    allCases,
    selectCase,
    setIsCopilotOpen,
  } = useForensic();
  const [query, setQuery] = useState("");

  const filteredNav = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return NAV_COMMANDS;
    return NAV_COMMANDS.filter((item) => item.label.toLowerCase().includes(q));
  }, [query]);

  const filteredCases = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allCases;
    return allCases.filter(
      (c) =>
        c.caseId.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.target.toLowerCase().includes(q)
    );
  }, [allCases, query]);

  if (!isCommandPaletteOpen) return null;

  const close = () => {
    setIsCommandPaletteOpen(false);
    setQuery("");
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-start justify-center pt-[12vh] px-4 no-print"
      onClick={close}
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div
        className="w-full max-w-xl glass-panel rounded-lg border border-cyber-cyan/30 shadow-glow overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/[0.08]">
          <Search className="w-4 h-4 text-cyber-cyan shrink-0" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Jump to module, investigation ID, or wallet address..."
            className="flex-1 bg-transparent text-sm text-cyber-text placeholder:text-cyber-muted focus:outline-none font-mono"
          />
          <button
            type="button"
            onClick={close}
            className="text-cyber-muted hover:text-cyber-text p-1"
            aria-label="Close command palette"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2 space-y-3">
          <div>
            <div className="px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-cyber-muted">
              Modules
            </div>
            <div className="space-y-0.5">
              {filteredNav.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.href}
                    type="button"
                    onClick={() => {
                      router.push(item.href);
                      close();
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded text-left text-xs text-cyber-text hover:bg-cyber-primary-dim hover:text-cyber-cyan transition-colors"
                  >
                    <Icon className="w-4 h-4 text-cyber-cyan shrink-0" />
                    <span className="font-medium">{item.label}</span>
                    <span className="ml-auto font-mono text-[10px] text-cyber-muted">
                      {item.href}
                    </span>
                  </button>
                );
              })}
              <button
                type="button"
                onClick={() => {
                  setIsCopilotOpen(true);
                  close();
                }}
                className="w-full flex items-center gap-3 px-3 py-2 rounded text-left text-xs text-cyber-text hover:bg-cyber-primary-dim hover:text-cyber-cyan transition-colors"
              >
                <Bot className="w-4 h-4 text-cyber-cyan shrink-0" />
                <span className="font-medium">Open Floating TraceAI Copilot</span>
                <span className="ml-auto font-mono text-[10px] text-cyber-muted">
                  DRAWER
                </span>
              </button>
            </div>
          </div>

          {filteredCases.length > 0 && (
            <div>
              <div className="px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-cyber-muted">
                Investigations
              </div>
              <div className="space-y-0.5">
                {filteredCases.map((c) => (
                  <button
                    key={c.caseId}
                    type="button"
                    onClick={() => {
                      selectCase(c.caseId);
                      router.push(`/investigations/${encodeURIComponent(c.caseId)}`);
                      close();
                    }}
                    className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded text-left text-xs text-cyber-text hover:bg-cyber-primary-dim transition-colors"
                  >
                    <div className="min-w-0">
                      <div className="font-medium truncate">{c.title}</div>
                      <div className="font-mono text-[10px] text-cyber-muted truncate">
                        {c.caseId} • {c.target}
                      </div>
                    </div>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-white/[0.12] text-cyber-cyan shrink-0">
                      {c.network}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
