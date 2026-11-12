"use client";

import React from "react";
import { RefreshCw, Save, Wifi, WifiOff } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { useForensic } from "@/context/ForensicContext";

export default function SettingsPage() {
  const { settings, updateSettings, isOnline, isLoading, refreshData, addToast } =
    useForensic();

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    addToast({
      title: "Settings Saved",
      description: "Platform configuration persisted to local storage.",
      variant: "success",
    });
  };

  return (
    <SocShell
      title="Platform Configuration & Endpoints"
      subtitle="Configure Role 1 / Role 2 API endpoints, offline fallback, thresholds & display preferences"
    >
      <form onSubmit={handleSave} className="max-w-3xl space-y-6">
        {/* Connection Status Card */}
        <section className="rounded border border-white/[0.08] bg-[#0E1217] p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-[#8A929E]">
                API TELEMETRY STATUS
              </p>
              <div className="mt-2 flex items-center gap-2 text-sm font-mono">
                {isOnline && !settings.offlineMode ? (
                  <>
                    <Wifi className="w-4 h-4 text-[#22C55E]" />
                    <span className="text-[#22C55E]">CONNECTED TO BACKEND</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-[#F59E0B]" />
                    <span className="text-[#F59E0B]">
                      {settings.offlineMode
                        ? "FORCED OFFLINE MOCK MODE"
                        : "OFFLINE MOCK FALLBACK ACTIVE"}
                    </span>
                  </>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => refreshData()}
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded border border-white/[0.12] text-xs font-mono text-[#F5F7FA] hover:border-[#00E5FF]/50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              Test Connection
            </button>
          </div>
        </section>

        {/* Backend Endpoints */}
        <section className="rounded border border-white/[0.08] bg-[#0E1217] p-6 space-y-4">
          <h2 className="text-xs font-mono uppercase tracking-[0.16em] text-[#00E5FF]">
            Backend Service Endpoints
          </h2>

          <div>
            <label className="block text-xs font-mono text-[#8A929E] mb-1.5">
              Role 1 — Graph & Ingestion API URL
            </label>
            <input
              type="url"
              value={settings.role1Endpoint}
              onChange={(e) => updateSettings({ role1Endpoint: e.target.value })}
              className="w-full h-10 px-3 rounded bg-[#07090C] border border-white/[0.1] text-xs font-mono text-[#F5F7FA] focus:outline-none focus:border-[#00E5FF]/50"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-[#8A929E] mb-1.5">
              Role 2 — Forensic & ML Intelligence API URL
            </label>
            <input
              type="url"
              value={settings.role2Endpoint}
              onChange={(e) => updateSettings({ role2Endpoint: e.target.value })}
              className="w-full h-10 px-3 rounded bg-[#07090C] border border-white/[0.1] text-xs font-mono text-[#F5F7FA] focus:outline-none focus:border-[#00E5FF]/50"
            />
          </div>

          <label className="flex items-center justify-between pt-2 cursor-pointer">
            <div>
              <p className="text-xs font-medium text-[#F5F7FA]">
                Force Offline Mock Store
              </p>
              <p className="text-[11px] text-[#8A929E]">
                Use local deterministic mock cases without polling backend APIs
              </p>
            </div>
            <input
              type="checkbox"
              checked={settings.offlineMode}
              onChange={(e) => updateSettings({ offlineMode: e.target.checked })}
              className="accent-[#00E5FF] w-4 h-4"
            />
          </label>
        </section>

        {/* Forensic & Graph Preferences */}
        <section className="rounded border border-white/[0.08] bg-[#0E1217] p-6 space-y-4">
          <h2 className="text-xs font-mono uppercase tracking-[0.16em] text-[#00E5FF]">
            Forensic Thresholds & Graph Defaults
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-[#8A929E] mb-1.5">
                High-Risk Alert Threshold ({settings.highRiskThreshold}/100)
              </label>
              <input
                type="range"
                min={40}
                max={95}
                value={settings.highRiskThreshold}
                onChange={(e) =>
                  updateSettings({ highRiskThreshold: Number(e.target.value) })
                }
                className="w-full accent-[#00E5FF]"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-[#8A929E] mb-1.5">
                Default Graph Layout
              </label>
              <select
                value={settings.defaultGraphLayout}
                onChange={(e) =>
                  updateSettings({
                    defaultGraphLayout: e.target.value as
                      | "cose"
                      | "breadthfirst"
                      | "circle",
                  })
                }
                className="w-full h-10 px-3 rounded bg-[#07090C] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
              >
                <option value="cose">Force-Directed (COSE)</option>
                <option value="breadthfirst">Hierarchical</option>
                <option value="circle">Circular</option>
              </select>
            </div>
          </div>

          <label className="flex items-center justify-between pt-2 cursor-pointer">
            <div>
              <p className="text-xs font-medium text-[#F5F7FA]">
                Reduce Motion & Animations
              </p>
              <p className="text-[11px] text-[#8A929E]">
                Disable 3D canvas motion and scroll transitions
              </p>
            </div>
            <input
              type="checkbox"
              checked={settings.reduceMotion}
              onChange={(e) => updateSettings({ reduceMotion: e.target.checked })}
              className="accent-[#00E5FF] w-4 h-4"
            />
          </label>
        </section>

        <button
          type="submit"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase tracking-wider hover:bg-[#33ECFF]"
        >
          <Save className="w-3.5 h-3.5" />
          Save Configuration
        </button>
      </form>
    </SocShell>
  );
}
