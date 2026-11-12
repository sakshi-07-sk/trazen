"use client";

import React, { useState } from "react";
import { Bot, Send, Sparkles, ShieldCheck } from "lucide-react";
import { SocShell } from "@/components/layout/SocShell";
import { useForensic } from "@/context/ForensicContext";
import { investigationApi } from "@/services/api/investigationApi";
import { CopilotMessage } from "@/types/investigation";
import { formatTimestamp, cn, getCaseRiskScore } from "@/lib/utils";

const SUGGESTED_PROMPTS = [
  "Why is this wallet suspicious?",
  "Explain the three-hop trace.",
  "Explain the detected peel-chain pattern.",
  "Which parts of this trace remain uncertain?",
  "Summarize the investigation.",
];

export default function CopilotPage() {
  const { allCases, activeCase, selectCase } = useForensic();
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: "welcome",
      sender: "copilot",
      text: `TraceAI Copilot ready for **${activeCase.caseId}** (${activeCase.network}). All responses are rule-based and grounded in verified case findings and SHA-256 evidence records.`,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const sendPrompt = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    const userMsg: CopilotMessage = {
      id: `u-${Date.now()}`,
      sender: "user",
      text: trimmed,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const reply = await investigationApi.askCopilot({
        caseId: activeCase.caseId,
        query: trimmed,
        history: messages,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: "copilot",
          text: reply.message,
          evidenceIds: reply.evidenceIds,
          findings: reply.findings,
          isOfflineFallback: reply.isOffline,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: "copilot",
          text: `Based on local case data for ${activeCase.caseId}: Risk Score is ${getCaseRiskScore(activeCase)}/100 with ${activeCase.findings.length} deterministic findings and ${activeCase.evidence.length} evidence records.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <SocShell
      title="TraceAI Forensic Copilot"
      subtitle="Rule-based, evidence-grounded assistant citing verified findings & SHA-256 records"
      actions={
        <select
          value={activeCase.caseId}
          onChange={(e) => selectCase(e.target.value)}
          className="h-9 px-3 rounded bg-[#0E1217] border border-white/[0.1] text-xs font-mono text-[#F5F7FA]"
          aria-label="Select investigation case"
        >
          {allCases.map((c) => (
            <option key={c.caseId} value={c.caseId}>
              {c.caseId} · {c.network}
            </option>
          ))}
        </select>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Chat Thread */}
        <div className="lg:col-span-8 rounded border border-white/[0.08] bg-[#0E1217] flex flex-col h-[640px]">
          <div className="px-5 py-3.5 border-b border-white/[0.08] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs font-mono uppercase tracking-wider text-[#F5F7FA]">
                Rule-Based Evidence Assistant
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#22C55E] flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Grounded
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "max-w-2xl rounded p-4 text-xs leading-relaxed border",
                  m.sender === "user"
                    ? "ml-auto bg-[#00E5FF]/10 border-[#00E5FF]/30 text-[#F5F7FA]"
                    : "mr-auto bg-[#07090C] border-white/[0.08] text-[#F5F7FA]"
                )}
              >
                <div className="flex items-center justify-between text-[10px] font-mono text-[#8A929E] mb-1.5">
                  <span>{m.sender === "user" ? "ANALYST" : "TRACEAI COPILOT"}</span>
                  <span>{formatTimestamp(m.timestamp)}</span>
                </div>
                <p className="whitespace-pre-wrap">{m.text}</p>
              </div>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendPrompt(input);
            }}
            className="p-4 border-t border-white/[0.08] flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about findings, peel chains, confidence caps, or evidence..."
              className="flex-1 h-10 px-3.5 rounded bg-[#07090C] border border-white/[0.1] text-xs font-mono text-[#F5F7FA] placeholder:text-[#8A929E]/60 focus:outline-none focus:border-[#00E5FF]/50"
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              className="h-10 px-4 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase inline-flex items-center gap-1.5 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              Send
            </button>
          </form>
        </div>

        {/* Suggested Prompts */}
        <aside className="lg:col-span-4 space-y-4">
          <div className="rounded border border-white/[0.08] bg-[#0E1217] p-5">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#00E5FF] mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              Suggested Forensic Queries
            </div>
            <div className="space-y-2">
              {SUGGESTED_PROMPTS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => sendPrompt(q)}
                  className="w-full text-left p-3 rounded bg-[#07090C] border border-white/[0.08] hover:border-[#00E5FF]/40 text-xs text-[#F5F7FA] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </SocShell>
  );
}
