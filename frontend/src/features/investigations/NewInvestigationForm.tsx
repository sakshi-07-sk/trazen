"use client";

import React, { useState } from "react";
import { BlockchainNetwork, TargetType, InvestigationCase } from "@/types/investigation";
import { validateCryptoInput } from "@/lib/validation";
import { investigationApi, ApiError } from "@/services/api/investigationApi";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { cn } from "@/lib/utils";
import {
  ShieldAlert,
  Search,
  Sliders,
  Calendar,
  AlertTriangle,
  Play,
  RotateCcw,
  Layers,
  Sparkles,
  Server,
} from "lucide-react";

interface NewInvestigationFormProps {
  onInvestigationCreated: (investigation: InvestigationCase) => void;
}

export function NewInvestigationForm({ onInvestigationCreated }: NewInvestigationFormProps) {
  const [network, setNetwork] = useState<BlockchainNetwork>("ETH");
  const [targetType, setTargetType] = useState<TargetType>("address");
  const [targetInput, setTargetInput] = useState("");
  const [maxHops, setMaxHops] = useState<number>(3);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [ingestionMode, setIngestionMode] = useState<"demo" | "live">("demo");

  // State for loading, validation, and errors
  const [isLoading, setIsLoading] = useState(false);
  const [progressStage, setProgressStage] = useState<string>("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [providerError, setProviderError] = useState<string | null>(null);

  const handleInputChange = (val: string) => {
    setTargetInput(val);
    setValidationError(null);
    setProviderError(null);
  };

  const handleQuickDemo = (demoNetwork: BlockchainNetwork) => {
    if (demoNetwork === "ETH") {
      setNetwork("ETH");
      setTargetType("address");
      setTargetInput("0x098b716b8aaf21512996dc57eb0615e2383e2f96");
      setMaxHops(4);
    } else {
      setNetwork("BTC");
      setTargetType("address");
      setTargetInput("bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6");
      setMaxHops(3);
    }
    setIngestionMode("demo");
    setValidationError(null);
    setProviderError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setProviderError(null);

    const validation = validateCryptoInput(targetInput, network, targetType);
    if (!validation.isValid) {
      setValidationError(validation.error || "Input format is invalid for selected network and type.");
      return;
    }

    setIsLoading(true);

    try {
      // Simulate progress stages for enterprise forensic feel
      setProgressStage("Validating Cryptographic Address Checksum...");
      await new Promise((r) => setTimeout(r, 400));

      setProgressStage("Connecting to Consensus Archive Node...");
      await new Promise((r) => setTimeout(r, 500));

      setProgressStage("Expanding Directed Transaction Graph & UTXO Trees...");
      await new Promise((r) => setTimeout(r, 600));

      setProgressStage("Executing Forensic Anomaly Detection Rules...");
      await new Promise((r) => setTimeout(r, 400));

      setProgressStage("Sealing Immutable SHA-256 Evidence Ledger...");

      const newCase = await investigationApi.createInvestigation({
        target: targetInput.trim(),
        network,
        type: targetType,
        maxHops,
        timeRange: dateFrom && dateTo ? { from: dateFrom, to: dateTo } : undefined,
        mode: ingestionMode,
      });

      onInvestigationCreated(newCase);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.code === "PROVIDER_ERROR" || err.status === 503) {
          setProviderError(err.message);
        } else {
          setValidationError(err.message);
        }
      } else {
        setValidationError((err as Error).message || "An unexpected error occurred during ingestion.");
      }
    } finally {
      setIsLoading(false);
      setProgressStage("");
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-cyber-surface border border-cyber-border rounded-xl shadow-2xl text-xs font-mono space-y-6">
      {/* Title & Description */}
      <div className="border-b border-cyber-border pb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Search className="w-4 h-4 text-cyber-primary" />
            INITIATE ON-CHAIN INVESTIGATION
          </h2>
          <p className="text-slate-400 text-xs mt-1 font-sans">
            Configure target seed entity, network parameters, and graph expansion depth.
          </p>
        </div>

        {/* Quick Demo Pre-sets */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-500">SAMPLE CASES:</span>
          <button
            type="button"
            onClick={() => handleQuickDemo("ETH")}
            className="px-2.5 py-1 bg-cyber-card hover:bg-slate-800 text-cyber-primary border border-cyber-border rounded text-[11px] font-semibold"
          >
            Lazarus ETH Case
          </button>
          <button
            type="button"
            onClick={() => handleQuickDemo("BTC")}
            className="px-2.5 py-1 bg-cyber-card hover:bg-slate-800 text-amber-400 border border-cyber-border rounded text-[11px] font-semibold"
          >
            Ransomware BTC Case
          </button>
        </div>
      </div>

      {/* Provider Error Banner */}
      {providerError && (
        <div className="p-4 bg-red-950/40 border border-red-500/50 rounded-lg text-red-300 space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>LIVE INGESTION PROVIDER FAILURE</span>
          </div>
          <p className="font-sans text-xs text-slate-200 leading-relaxed">{providerError}</p>
          <div className="pt-2 flex items-center gap-3">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                setIngestionMode("demo");
                setProviderError(null);
              }}
            >
              SWITCH TO DEMO INVESTIGATION MODE
            </Button>
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <div className="p-3 bg-amber-950/40 border border-amber-500/40 rounded-lg text-amber-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="font-sans text-xs text-slate-200">{validationError}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Network & Target Type Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-slate-400 mb-1.5 font-semibold">BLOCKCHAIN NETWORK:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setNetwork("ETH")}
                className={cn(
                  "py-2 px-3 rounded border text-center font-bold transition-colors",
                  network === "ETH"
                    ? "bg-cyber-primary text-white border-blue-400 shadow-glow"
                    : "bg-cyber-card text-slate-400 border-cyber-border hover:border-slate-500"
                )}
              >
                ETHEREUM (EVM)
              </button>
              <button
                type="button"
                onClick={() => setNetwork("BTC")}
                className={cn(
                  "py-2 px-3 rounded border text-center font-bold transition-colors",
                  network === "BTC"
                    ? "bg-amber-500 text-slate-950 border-amber-400"
                    : "bg-cyber-card text-slate-400 border-cyber-border hover:border-slate-500"
                )}
              >
                BITCOIN (UTXO)
              </button>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1.5 font-semibold">TARGET IDENTIFIER TYPE:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setTargetType("address")}
                className={cn(
                  "py-2 px-3 rounded border text-center font-bold transition-colors",
                  targetType === "address"
                    ? "bg-cyber-card text-slate-100 border-cyber-primary"
                    : "bg-cyber-card text-slate-400 border-cyber-border hover:border-slate-500"
                )}
              >
                WALLET ADDRESS
              </button>
              <button
                type="button"
                onClick={() => setTargetType("transaction")}
                className={cn(
                  "py-2 px-3 rounded border text-center font-bold transition-colors",
                  targetType === "transaction"
                    ? "bg-cyber-card text-slate-100 border-cyber-primary"
                    : "bg-cyber-card text-slate-400 border-cyber-border hover:border-slate-500"
                )}
              >
                TRANSACTION HASH
              </button>
            </div>
          </div>
        </div>

        {/* Input Target */}
        <div>
          <label className="block text-slate-400 mb-1.5 font-semibold">
            SEED {network} {targetType.toUpperCase()}:
          </label>
          <div className="relative">
            <input
              type="text"
              required
              placeholder={
                network === "ETH"
                  ? targetType === "address"
                    ? "0x... (40 hex characters)"
                    : "0x... (64 hex characters)"
                  : targetType === "address"
                  ? "bc1... or 1... or 3... (Bitcoin address)"
                  : "... (64 hex characters)"
              }
              value={targetInput}
              onChange={(e) => handleInputChange(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border focus:border-cyber-primary text-slate-100 rounded px-3.5 py-2.5 text-xs font-mono tracking-wider focus:outline-none transition-colors"
            />
          </div>
        </div>

        {/* Depth Configuration & Ingestion Source */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="flex justify-between text-slate-400 mb-1.5 font-semibold">
              <span>MAXIMUM HOP EXPANSION:</span>
              <span className="text-cyber-primary font-bold">{maxHops} HOPS</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              className="w-full accent-cyber-primary cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>1 (Direct Neighbors)</span>
              <span>3 (Standard Trace)</span>
              <span>5 (Deep Obfuscation)</span>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1.5 font-semibold">DATA INGESTION SOURCE:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setIngestionMode("demo")}
                className={cn(
                  "py-2 px-2.5 rounded border text-center transition-colors text-[11px]",
                  ingestionMode === "demo"
                    ? "bg-violet-950/60 border-violet-500/50 text-violet-300 font-bold"
                    : "bg-cyber-card border-cyber-border text-slate-400 hover:text-slate-200"
                )}
              >
                DEMO REPLAY
              </button>
              <button
                type="button"
                onClick={() => setIngestionMode("live")}
                className={cn(
                  "py-2 px-2.5 rounded border text-center transition-colors text-[11px]",
                  ingestionMode === "live"
                    ? "bg-cyber-primary/20 border-cyber-primary text-blue-300 font-bold"
                    : "bg-cyber-card border-cyber-border text-slate-400 hover:text-slate-200"
                )}
              >
                LIVE CONSENSUS RPC
              </button>
            </div>
          </div>
        </div>

        {/* Optional Time Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">OPTIONAL TIMESTAMP FROM (UTC):</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border text-slate-200 rounded px-3 py-1.5 focus:outline-none focus:border-cyber-primary"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">OPTIONAL TIMESTAMP TO (UTC):</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border text-slate-200 rounded px-3 py-1.5 focus:outline-none focus:border-cyber-primary"
            />
          </div>
        </div>

        {/* Ingestion Progress State */}
        {isLoading && (
          <div className="p-4 bg-cyber-card border border-cyber-primary/40 rounded-lg space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-cyber-primary font-bold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyber-primary animate-ping" />
                EXECUTION IN PROGRESS
              </span>
              <span className="text-slate-400">{progressStage}</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-cyber-primary h-full animate-pulse w-3/4 rounded-full" />
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={isLoading}
            icon={<Play className="w-4 h-4 fill-current" />}
          >
            START FORENSIC INVESTIGATION
          </Button>
        </div>
      </form>
    </div>
  );
}
