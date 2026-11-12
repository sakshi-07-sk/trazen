"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  Activity,
  ScrollText,
  Settings,
  UserPlus,
  RefreshCw,
  ShieldCheck,
  Server,
  AlertCircle,
} from "lucide-react";
import { RoleNavItem, RoleShell } from "@/components/layout/RoleShell";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";
import { useForensic } from "@/context/ForensicContext";
import { AdminAuditEntry, PublicUser, UserRole } from "@/lib/auth/types";
import { cn, formatTimestamp, getCaseRiskScore } from "@/lib/utils";

const ADMIN_NAV: RoleNavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "users", label: "User Management", icon: Users },
  { id: "investigations", label: "Investigations", icon: FolderKanban },
  { id: "monitoring", label: "System Monitoring", icon: Activity },
  { id: "audit", label: "Audit Logs", icon: ScrollText },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function AdminDashboardPage() {
  const { allCases, isOnline, settings, updateSettings, addToast, refreshData } =
    useForensic();
  const [section, setSection] = useState("dashboard");
  const [users, setUsers] = useState<PublicUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AdminAuditEntry[]>([]);
  const [loadingAdmin, setLoadingAdmin] = useState(true);
  const [adminError, setAdminError] = useState<string | null>(null);

  // Create user form state
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newOrg, setNewOrg] = useState("");
  const [newRole, setNewRole] = useState<UserRole>("INVESTIGATOR");
  const [newPassword, setNewPassword] = useState("");
  const [creating, setCreating] = useState(false);

  const loadAdminData = useCallback(async () => {
    setLoadingAdmin(true);
    setAdminError(null);
    try {
      const [usersRes, auditRes] = await Promise.all([
        fetch("/api/admin/users", { cache: "no-store" }),
        fetch("/api/admin/audit", { cache: "no-store" }),
      ]);
      if (!usersRes.ok || !auditRes.ok) {
        throw new Error("Unable to load administrative telemetry.");
      }
      const usersJson = await usersRes.json();
      const auditJson = await auditRes.json();
      setUsers(usersJson.users || []);
      setAuditLogs(auditJson.auditLogs || []);
    } catch (err) {
      setAdminError(
        err instanceof Error ? err.message : "Failed to load admin data."
      );
    } finally {
      setLoadingAdmin(false);
    }
  }, []);

  useEffect(() => {
    loadAdminData();
  }, [loadAdminData]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullName: newName,
          email: newEmail,
          organization: newOrg,
          role: newRole,
          password: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        addToast({
          title: "Provisioning Failed",
          description: data.message || "Could not create user.",
          variant: "error",
        });
        return;
      }
      setNewName("");
      setNewEmail("");
      setNewOrg("");
      setNewPassword("");
      addToast({
        title: "Account Provisioned",
        description: `${data.user.email} assigned role ${data.user.role}.`,
        variant: "success",
      });
      await loadAdminData();
    } finally {
      setCreating(false);
    }
  };

  const handleUpdateUser = async (
    id: string,
    patch: { role?: UserRole; status?: "ACTIVE" | "DEACTIVATED" }
  ) => {
    const res = await fetch(`/api/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    const data = await res.json();
    if (!res.ok) {
      addToast({
        title: "Update Denied",
        description: data.message || "Unable to update user.",
        variant: "error",
      });
      return;
    }
    addToast({
      title: "User Updated",
      description: `${data.user.email} updated.`,
      variant: "success",
    });
    await loadAdminData();
  };

  const activeInvestigators = users.filter(
    (u) => u.role === "INVESTIGATOR" && u.status === "ACTIVE"
  ).length;
  const activeAnalysts = users.filter(
    (u) => u.role === "ANALYST" && u.status === "ACTIVE"
  ).length;

  return (
    <RoleShell
      role="ADMIN"
      navItems={ADMIN_NAV}
      activeSection={section}
      onSelectSection={setSection}
      title="Administrator Governance & Operations"
      subtitle="User provisioning, RBAC enforcement, system health & immutable audit logs"
      actions={
        <button
          type="button"
          onClick={() => {
            loadAdminData();
            refreshData();
          }}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-sm bg-[#151616] border border-white/15 hover:border-[#FF6A13] text-xs uppercase tracking-[0.12em] text-[#F1EEE6] transition-colors"
          style={{ fontFamily: "var(--font-jetbrains), monospace" }}
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#FF6A13] ${loadingAdmin ? "animate-spin" : ""}`} />
          Sync Telemetry
        </button>
      }
    >
      {adminError && (
        <div className="mb-6 p-4 rounded-sm border border-[#EF4444]/40 bg-[#EF4444]/10 text-xs text-[#EF4444] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{adminError}</span>
        </div>
      )}

      {/* Overview Dashboard */}
      {section === "dashboard" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Total Registered Users
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#F1EEE6] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={users.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">Across 3 RBAC tiers</p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Active Investigators & Analysts
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#FF6A13] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={activeInvestigators + activeAnalysts} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                {activeInvestigators} Investigators · {activeAnalysts} Analysts
              </p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                Total Investigations
              </p>
              <p
                className="mt-3 text-4xl font-bold text-[#F1EEE6] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                [ <AnimatedCounter value={allCases.length} /> ]
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">ETH & BTC forensic cases</p>
            </div>

            <div className="rounded-sm border border-white/10 hover:border-[#FF6A13]/40 bg-[#151616] p-5 transition-colors">
              <p
                className="text-[11px] uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                System & API Health
              </p>
              <p
                className={cn(
                  "mt-3 text-2xl font-bold tracking-tight",
                  isOnline ? "text-[#22C55E]" : "text-[#F59E0B]"
                )}
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                {isOnline ? "[ OPERATIONAL ]" : "[ FALLBACK MOCK ]"}
              </p>
              <p className="mt-1 text-xs text-[#A6A39A]">
                Role 1 + Role 2 Pipeline
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
              <div className="flex items-center justify-between mb-4">
                <h2
                  className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                  style={{ fontFamily: "var(--font-display), sans-serif" }}
                >
                  Recent Platform Activity
                </h2>
                <button
                  type="button"
                  onClick={() => setSection("audit")}
                  className="text-xs uppercase tracking-[0.12em] text-[#FF6A13] hover:text-[#FF812E]"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Full Audit Log
                </button>
              </div>
              <div className="space-y-3">
                {auditLogs.slice(0, 5).map((log) => (
                  <div
                    key={log.id}
                    className="p-3 rounded-sm bg-[#080909] border border-white/10 text-xs"
                  >
                    <div
                      className="flex items-center justify-between"
                      style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                    >
                      <span className="text-[#FF6A13]">{log.action}</span>
                      <span className="text-[#A6A39A]">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    <p className="text-[#F1EEE6] mt-1">{log.details}</p>
                    <p
                      className="text-[11px] text-[#A6A39A] mt-1"
                      style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                    >
                      Actor: {log.actorEmail} ({log.actorRole})
                    </p>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
              <div className="flex items-center justify-between mb-4">
                <h2
                  className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                  style={{ fontFamily: "var(--font-display), sans-serif" }}
                >
                  Account Directory Snapshot
                </h2>
                <button
                  type="button"
                  onClick={() => setSection("users")}
                  className="text-xs uppercase tracking-[0.12em] text-[#FF6A13] hover:text-[#FF812E]"
                  style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                >
                  Manage Users
                </button>
              </div>
              <div className="space-y-2.5">
                {users.map((u) => (
                  <div
                    key={u.id}
                    className="p-3 rounded-sm bg-[#080909] border border-white/10 flex items-center justify-between gap-2 text-xs"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-[#F1EEE6] truncate">
                        {u.fullName}
                      </p>
                      <p
                        className="text-[11px] text-[#A6A39A] truncate"
                        style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                      >
                        {u.email}
                      </p>
                    </div>
                    <div
                      className="flex items-center gap-2 shrink-0 text-[10px]"
                      style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                    >
                      <span className="px-2 py-0.5 rounded-sm bg-white/[0.05] border border-white/15">
                        {u.role}
                      </span>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded-sm border",
                          u.status === "ACTIVE"
                            ? "text-[#22C55E] border-[#22C55E]/30 bg-[#22C55E]/10"
                            : "text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10"
                        )}
                      >
                        {u.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}

      {/* User Management Section */}
      {section === "users" && (
        <div className="space-y-6">
          <section className="rounded-sm border border-white/10 bg-[#151616] p-6">
            <div className="flex items-center gap-2 mb-4">
              <UserPlus className="w-4 h-4 text-[#FF6A13]" />
              <h2
                className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                Provision New User Account (Admin Only)
              </h2>
            </div>

            <form
              onSubmit={handleCreateUser}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3"
            >
              <input
                type="text"
                required
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Full Name"
                className="h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
              />
              <input
                type="email"
                required
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="Work Email"
                className="h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
              />
              <input
                type="text"
                required
                value={newOrg}
                onChange={(e) => setNewOrg(e.target.value)}
                placeholder="Organization"
                className="h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
              />
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value as UserRole)}
                className="h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
                aria-label="Assign Role"
              >
                <option value="INVESTIGATOR">INVESTIGATOR</option>
                <option value="ANALYST">ANALYST</option>
                <option value="ADMIN">ADMIN</option>
              </select>
              <div className="flex gap-2">
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Temp Password (8+)"
                  className="flex-1 min-w-0 h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 h-9 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-mono font-semibold uppercase shrink-0 transition-colors"
                >
                  {creating ? "..." : "Create"}
                </button>
              </div>
            </form>
          </section>

          <section className="rounded-sm border border-white/10 bg-[#151616] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10 bg-[#101111] text-[11px] font-mono uppercase text-[#A6A39A]">
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Organization</th>
                    <th className="py-3 px-4">Role Assignment</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06] text-xs">
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="py-3 px-4 font-medium text-[#F1EEE6]">
                        {u.fullName}
                      </td>
                      <td className="py-3 px-4 font-mono text-[#A6A39A]">{u.email}</td>
                      <td className="py-3 px-4 text-[#A6A39A]">{u.organization}</td>
                      <td className="py-3 px-4">
                        <select
                          value={u.role}
                          onChange={(e) =>
                            handleUpdateUser(u.id, { role: e.target.value as UserRole })
                          }
                          aria-label={`Change role for ${u.email}`}
                          className="h-8 px-2 rounded-sm bg-[#080909] border border-white/15 text-[11px] font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
                        >
                          <option value="INVESTIGATOR">INVESTIGATOR</option>
                          <option value="ANALYST">ANALYST</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px]">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-sm border",
                            u.status === "ACTIVE"
                              ? "text-[#22C55E] border-[#22C55E]/30 bg-[#22C55E]/10"
                              : "text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10"
                          )}
                        >
                          {u.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          type="button"
                          onClick={() =>
                            handleUpdateUser(u.id, {
                              status: u.status === "ACTIVE" ? "DEACTIVATED" : "ACTIVE",
                            })
                          }
                          className="px-2.5 py-1 rounded-sm border border-white/15 hover:border-[#FF6A13] text-[11px] font-mono text-[#F1EEE6] transition-colors"
                        >
                          {u.status === "ACTIVE" ? "Deactivate" : "Reactivate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {/* Investigations Governance */}
      {section === "investigations" && (
        <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
          <h2
            className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mb-4"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            Platform Investigations Oversight ({allCases.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-[11px] font-mono uppercase text-[#A6A39A]">
                  <th className="py-2.5 pr-4">Case ID</th>
                  <th className="py-2.5 pr-4">Title</th>
                  <th className="py-2.5 pr-4">Chain</th>
                  <th className="py-2.5 pr-4">Risk</th>
                  <th className="py-2.5 pr-4">Findings</th>
                  <th className="py-2.5">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-xs">
                {allCases.map((c) => (
                  <tr key={c.caseId}>
                    <td className="py-3 pr-4 font-mono text-[#FF6A13]">{c.caseId}</td>
                    <td className="py-3 pr-4 text-[#F1EEE6]">{c.title}</td>
                    <td className="py-3 pr-4 font-mono text-[#A6A39A]">{c.network}</td>
                    <td className="py-3 pr-4 font-mono text-[#FF6A13]">
                      [ {getCaseRiskScore(c)} / 100 ]
                    </td>
                    <td className="py-3 pr-4 font-mono text-[#F1EEE6]">
                      {c.findings.length}
                    </td>
                    <td className="py-3 font-mono text-[#A6A39A]">
                      {formatTimestamp(c.updatedAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* System Monitoring */}
      {section === "monitoring" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-sm border border-white/10 bg-[#151616] p-6">
            <div className="flex items-center gap-2 text-xs font-mono text-[#FF6A13] mb-2">
              <Server className="w-4 h-4" />
              ROLE 1 — INGESTION & GRAPH ENGINE
            </div>
            <p className="text-sm font-semibold text-[#F1EEE6]">
              {settings.role1Endpoint}
            </p>
            <p className="text-xs text-[#A6A39A] mt-1">
              Status: {isOnline ? "Reachable & Synchronized" : "Mock Fallback Mode"}
            </p>
          </div>
          <div className="rounded-sm border border-white/10 bg-[#151616] p-6">
            <div className="flex items-center gap-2 text-xs font-mono text-[#22C55E] mb-2">
              <ShieldCheck className="w-4 h-4" />
              ROLE 2 — FORENSIC INTELLIGENCE ENGINE
            </div>
            <p className="text-sm font-semibold text-[#F1EEE6]">
              {settings.role2Endpoint}
            </p>
            <p className="text-xs text-[#A6A39A] mt-1">
              17 behavioral features · 11 benchmark scenarios · SHA-256 audit ready
            </p>
          </div>
        </div>
      )}

      {/* Audit Logs */}
      {section === "audit" && (
        <section className="rounded-sm border border-white/10 bg-[#151616] p-5">
          <h2
            className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6] mb-4"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            Security & RBAC Audit Trail ({auditLogs.length})
          </h2>
          <div className="space-y-2.5">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="p-3.5 rounded-sm bg-[#080909] border border-white/10 text-xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 font-mono">
                  <span className="text-[#FF6A13]">{log.action}</span>
                  <span className="text-[#A6A39A]">
                    {formatTimestamp(log.timestamp)}
                  </span>
                </div>
                <p className="text-[#F1EEE6] mt-1">{log.details}</p>
                <p className="text-[11px] font-mono text-[#A6A39A] mt-1">
                  Actor: {log.actorEmail} ({log.actorRole}) · Target: {log.target}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Admin Settings */}
      {section === "settings" && (
        <section className="rounded-sm border border-white/10 bg-[#151616] p-6 max-w-2xl space-y-4">
          <h2
            className="text-lg font-bold uppercase tracking-wide text-[#F1EEE6]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            Global System Settings
          </h2>
          <div>
            <label className="block text-xs font-mono text-[#A6A39A] mb-1">
              Role 1 Backend URL
            </label>
            <input
              type="url"
              value={settings.role1Endpoint}
              onChange={(e) => updateSettings({ role1Endpoint: e.target.value })}
              className="w-full h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-[#A6A39A] mb-1">
              Role 2 Intelligence URL
            </label>
            <input
              type="url"
              value={settings.role2Endpoint}
              onChange={(e) => updateSettings({ role2Endpoint: e.target.value })}
              className="w-full h-9 px-3 rounded-sm bg-[#080909] border border-white/15 text-xs font-mono text-[#F1EEE6] focus:border-[#FF6A13] focus:outline-none"
            />
          </div>
          <label className="flex items-center justify-between pt-2 text-xs cursor-pointer">
            <span className="text-[#F1EEE6]">Force Offline Mock Store</span>
            <input
              type="checkbox"
              checked={settings.offlineMode}
              onChange={(e) => updateSettings({ offlineMode: e.target.checked })}
              className="accent-[#FF6A13]"
            />
          </label>
        </section>
      )}
    </RoleShell>
  );
}
