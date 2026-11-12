"use client";

import React, { useState, useRef, useEffect } from "react";
import { InvestigationCase, CopilotMessage } from "@/types/investigation";
import { investigationApi } from "@/services/api/investigationApi";
import { Badge } from "@/components/common/Badge";
import { formatTimestamp, cn } from "@/lib/utils";
import {
  Bot,
  Send,
  Sparkles,
  ShieldAlert,
  FileText,
  HelpCircle,
  CheckCircle,
  ExternalLink,
  ChevronDown,
  Layers,
  Terminal,
} from "lucide-react";

interface TraceAICopilotPanelProps {
  investigation: InvestigationCase;
  isOpen: boolean;
  onClose: () => void;
  onSelectEvidence?: (evidenceId: string) => void;
  onSelectFinding?: (findingId: string) => void;
}

const SUGGESTED_QUERIES = [
  "Why is this wallet suspicious?",
  "Explain the three-hop trace.",
  "Show the strongest evidence for this receiver.",
  "Explain the detected peel-chain pattern.",
  "Which parts of this trace remain uncertain?",
  "Summarize the investigation.",
  "Generate an investigation report.",
];

export function TraceAICopilotPanel({
  investigation,
  isOpen,
  onClose,
  onSelectEvidence,
  onSelectFinding,
}: TraceAICopilotPanelProps) {
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: "init",
      sender: "copilot",
      timestamp: new Date().toISOString(),
      text: `Hello Analyst. I am **TraceAI**, your forensic assistant for Case **${investigation.caseId}** targeting \`${investigation.target}\`.\n\nI analyze structured findings from Roles 1, 2, and 3 without inventing non-existent transactions or labels. How can I assist your investigation?`,
      evidenceIds: investigation.evidence.slice(0, 2).map((e) => e.id),
      findings: [investigation.findings[0]?.id].filter(Boolean),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSend = async (queryToSend?: string) => {
    const text = (queryToSend || inputQuery).trim();
    if (!text || isGenerating) return;

    setInputQuery("");
    const userMsgId = `user-${Date.now()}`;
    const userMsg: CopilotMessage = {
      id: userMsgId,
      sender: "user",
      timestamp: new Date().toISOString(),
      text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsGenerating(true);

    try {
      const res = await investigationApi.askCopilot({
        caseId: investigation.caseId,
        query: text,
        history: [...messages, userMsg],
      });

      const copilotMsg: CopilotMessage = {
        id: `copilot-${Date.now()}`,
        sender: "copilot",
        timestamp: new Date().toISOString(),
        text: res.message,
        evidenceIds: res.evidenceIds,
        findings: res.findings,
        isOfflineFallback: res.isOffline,
      };

      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: unknown) {
      const errorMsg: CopilotMessage = {
        id: `err-${Date.now()}`,
        sender: "copilot",
        timestamp: new Date().toISOString(),
        text: `⚠️ **AI Provider Offline**: Could not connect to remote LLM endpoint. TraceAI has defaulted to local deterministic forensic rule inspection. Investigation workflows continue uninterrupted.`,
        isOfflineFallback: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-cyber-surface border-l border-cyber-border shadow-2xl z-50 flex flex-col font-mono text-xs text-slate-200">
      {/* Top Header */}
      <div className="p-4 border-b border-cyber-border bg-[#090e18] flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-cyber-primary/10 border border-cyber-primary/40 rounded text-cyber-primary">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 text-sm">TraceAI COPILOT</span>
              <Badge variant="verified">Rule-based, evidence-grounded assistant</Badge>
            </div>
            <span className="text-[10px] text-slate-400">CASE: {investigation.caseId}</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 text-base font-bold"
          title="Close Copilot"
        >
          ×
        </button>
      </div>

      {/* Suggested Quick Queries Pills */}
      <div className="p-3 border-b border-cyber-border/70 bg-cyber-bg/40 space-y-1.5 overflow-x-auto">
        <span className="text-[10px] text-slate-400 block font-semibold">RECOMMENDED FORENSIC QUERIES:</span>
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED_QUERIES.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              disabled={isGenerating}
              className="text-[10px] px-2 py-1 bg-cyber-card hover:bg-slate-800 border border-cyber-border rounded text-slate-300 hover:text-cyber-primary transition-colors disabled:opacity-50 text-left"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex flex-col gap-1.5", {
              "items-end": msg.sender === "user",
              "items-start": msg.sender === "copilot",
            })}
          >
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 px-1">
              <span>{msg.sender === "user" ? "INVESTIGATOR" : "TraceAI COPILOT"}</span>
              <span>•</span>
              <span>{formatTimestamp(msg.timestamp)}</span>
            </div>

            <div
              className={cn(
                "p-3.5 rounded-lg max-w-[92%] leading-relaxed font-sans text-xs space-y-2.5",
                msg.sender === "user"
                  ? "bg-cyber-primary text-white font-mono"
                  : "bg-cyber-card border border-cyber-border text-slate-200"
              )}
            >
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Citations / Supporting Evidence badges */}
              {msg.evidenceIds && msg.evidenceIds.length > 0 && (
                <div className="pt-2 border-t border-cyber-border/60 flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
                  <span className="text-slate-400">GROUNDED EVIDENCE:</span>
                  {msg.evidenceIds.map((evId) => (
                    <button
                      key={evId}
                      onClick={() => onSelectEvidence?.(evId)}
                      className="px-1.5 py-0.5 bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 rounded hover:underline"
                    >
                      {evId}
                    </button>
                  ))}
                </div>
              )}

              {msg.findings && msg.findings.length > 0 && (
                <div className="pt-1 flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
                  <span className="text-slate-400">RULES:</span>
                  {msg.findings.map((fId) => (
                    <button
                      key={fId}
                      onClick={() => onSelectFinding?.(fId)}
                      className="px-1.5 py-0.5 bg-red-950/60 border border-red-500/40 text-red-300 rounded hover:underline"
                    >
                      {fId}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isGenerating && (
          <div className="flex items-center gap-2 text-slate-400 text-xs p-2 font-mono">
            <span className="w-2 h-2 rounded-full bg-cyber-primary animate-ping" />
            <span>Consulting case findings and verifying cryptographic evidence records...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-cyber-border bg-[#090e18]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask a question grounded in case evidence..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isGenerating}
            className="flex-1 bg-cyber-card border border-cyber-border focus:border-cyber-primary text-slate-100 rounded px-3 py-2 text-xs font-mono focus:outline-none"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isGenerating}
            className="p-2 bg-cyber-primary hover:bg-blue-600 disabled:opacity-40 text-white rounded transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
