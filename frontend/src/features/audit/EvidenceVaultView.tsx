"use client";

import React, { useState } from "react";
import { EvidenceVaultItem, AuditLogEvent } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { formatAddress, formatTimestamp, cn } from "@/lib/utils";
import { investigationApi } from "@/services/api/investigationApi";
import {
  ShieldCheck,
  ShieldAlert,
  Link,
  Database,
  Hash,
  Clock,
  CheckCircle2,
  FileText,
  Lock,
  Layers,
  RefreshCw,
} from "lucide-react";

interface EvidenceVaultViewProps {
  evidence: EvidenceVaultItem[];
  auditLogs: AuditLogEvent[];
  caseId: string;
}

export function EvidenceVaultView({ evidence, auditLogs, caseId }: EvidenceVaultViewProps) {
  const [activeTab, setActiveTab] = useState<"evidence" | "hashchain" | "audit">("evidence");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    verified: boolean;
    recordsCount: number;
    headHash: string;
    details: string;
  } | null>(null);

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const res = await investigationApi.verifyAuditChain(caseId);
      setVerificationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Verification Action Bar */}
      <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-100 font-mono">
                CRYPTOGRAPHIC EVIDENCE VAULT & HASH-CHAIN LEDGER
              </h3>
              <Badge variant="verified">SHA-256 SEALED</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Every forensic artifact and RPC receipt is bound to an immutable chronological hash-chain.
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          isLoading={isVerifying}
          icon={<ShieldCheck className="w-4 h-4" />}
          onClick={handleVerifyChain}
        >
          VERIFY HASH-CHAIN INTEGRITY
        </Button>
      </div>

      {/* Verification Result Banner if run */}
      {verificationResult && (
        <div
          className={cn(
            "p-3.5 rounded-lg border text-xs font-mono flex items-start gap-3 transition-all",
            verificationResult.verified
              ? "bg-emerald-950/25 border-emerald-500/40 text-emerald-300"
              : "bg-red-950/25 border-red-500/40 text-red-300"
          )}
        >
          {verificationResult.verified ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            <div className="font-bold flex items-center gap-2">
              <span>LEDGER INTEGRITY VERIFIED (SHA-256 CHECKPOINT)</span>
              <span>•</span>
              <span>{verificationResult.recordsCount} RECORDS INTACT</span>
            </div>
            <div className="text-[11px] text-slate-300">{verificationResult.details}</div>
            <div className="text-[10px] text-slate-400 break-all">
              HEAD MERKLE ROOT: <code>{verificationResult.headHash}</code>
            </div>
          </div>
        </div>
      )}

      {/* View Tabs */}
      <div className="flex border-b border-cyber-border text-xs font-mono bg-cyber-bg/50">
        {(
          [
            ["evidence", `EVIDENCE ARTIFACTS (${evidence.length})`],
            ["hashchain", "CRYPTOGRAPHIC HASH-CHAIN RAIL"],
            ["audit", `FORENSIC AUDIT LOGS (${auditLogs.length})`],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              "px-4 py-2.5 border-b-2 font-medium transition-colors",
              activeTab === key
                ? "border-cyber-primary text-cyber-primary bg-cyber-primary/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab 1: Evidence Artifacts List */}
      {activeTab === "evidence" && (
        <div className="space-y-3">
          {evidence.map((item) => (
            <div
              key={item.id}
              className="p-4 bg-cyber-surface border border-cyber-border rounded-lg space-y-3 font-mono text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-cyber-border/60 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-cyber-primary font-bold text-sm">{item.id}</span>
                  <Badge variant="verified">{item.integrityStatus}</Badge>
                  <span className="text-[11px] text-slate-400">INDEX #{item.hashChainIndex}</span>
                </div>
                <div className="text-slate-400 text-[11px] flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{formatTimestamp(item.retrievalTimestamp)}</span>
                </div>
              </div>

              <div className="text-slate-200 font-sans text-xs bg-cyber-card p-3 rounded border border-cyber-border">
                {item.details}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-slate-300 pt-1">
                <div className="space-y-1">
                  <span className="text-slate-500 block">CONSENSUS SOURCE NODE:</span>
                  <div className="text-slate-200">{item.dataSource}</div>
                  <div className="text-slate-400">BLOCK: #{item.blockNumber.toLocaleString()}</div>
                </div>

                <div className="space-y-1">
                  <span className="text-slate-500 block">SOURCE TRANSACTION HASH:</span>
                  <div className="text-cyber-primary truncate" title={item.sourceTxHash}>
                    {item.sourceTxHash}
                  </div>
                  <div className="text-slate-400">RULE: {item.detectionRuleVersion}</div>
                </div>
              </div>

              {/* Cryptographic hash chain proof snippet */}
              <div className="bg-[#090e18] p-2.5 rounded border border-cyber-border/70 text-[10px] space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>PREVIOUS RECORD HASH:</span>
                  <span className="truncate max-w-[280px] text-slate-500">{item.previousRecordHash}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-cyber-primary">CURRENT RECORD HASH (SHA-256):</span>
                  <span className="truncate max-w-[280px] text-emerald-400 font-bold">{item.recordHash}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Hash Chain Visual Diagram */}
      {activeTab === "hashchain" && (
        <div className="space-y-4">
          <div className="p-4 bg-cyber-surface border border-cyber-border rounded-lg text-xs font-mono space-y-4">
            <h4 className="text-slate-300 font-semibold flex items-center gap-2">
              <Link className="w-4 h-4 text-cyber-primary" />
              SEQUENTIAL MERKLE RECORD LINKAGE
            </h4>

            <div className="space-y-4">
              {evidence.map((rec, idx) => (
                <div key={rec.id} className="relative flex items-start gap-4">
                  <div className="w-7 h-7 rounded-full bg-cyber-primary/20 border border-cyber-primary text-cyber-primary flex items-center justify-center font-bold text-xs shrink-0 mt-1">
                    {rec.hashChainIndex}
                  </div>

                  <div className="flex-1 bg-cyber-card p-3 rounded border border-cyber-border space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-200 font-bold">{rec.id}</span>
                      <span className="text-[10px] text-emerald-400">ALGORITHM: SHA-256</span>
                    </div>
                    <div className="text-[11px] text-slate-400 truncate">
                      PREV: {rec.previousRecordHash}
                    </div>
                    <div className="text-[11px] text-cyber-primary font-bold truncate">
                      HASH: {rec.recordHash}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Audit Logs */}
      {activeTab === "audit" && (
        <div className="space-y-2 font-mono text-xs">
          {auditLogs.map((log) => (
            <div
              key={log.id}
              className="p-3 bg-cyber-surface border border-cyber-border rounded-lg flex flex-wrap items-center justify-between gap-3"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-cyber-primary font-bold">{log.id}</span>
                  <Badge variant="info">{log.eventType}</Badge>
                  <span className="text-slate-400">{formatTimestamp(log.timestamp)}</span>
                </div>
                <div className="text-slate-200 font-sans">{log.details}</div>
                <div className="text-[10px] text-slate-500">OPERATOR: {log.operator}</div>
              </div>

              <div className="text-right text-[10px] text-slate-400">
                <div>PROOF HASH:</div>
                <code className="text-emerald-400 font-bold">{formatAddress(log.sha256Proof, 8, 8)}</code>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
