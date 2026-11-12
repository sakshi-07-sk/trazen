"use client";

import React, { useState, useMemo } from "react";
import { InvestigationTimelineEvent, TimelineEventType } from "@/types/investigation";
import { Badge } from "@/components/common/Badge";
import { formatAddress, formatTimestamp, cn } from "@/lib/utils";
import {
  ArrowDownRight,
  GitCommit,
  ShieldCheck,
  UserCheck,
  Layers,
  Clock,
  ArrowRightLeft,
  AlertTriangle,
  ArrowUpDown,
} from "lucide-react";

interface InvestigationTimelineViewProps {
  timeline: InvestigationTimelineEvent[];
  onSelectEvent?: (event: InvestigationTimelineEvent) => void;
}

export function InvestigationTimelineView({
  timeline,
  onSelectEvent,
}: InvestigationTimelineViewProps) {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const filteredEvents = useMemo(() => {
    const result = timeline.filter((e) => {
      if (filterType !== "ALL" && e.type !== filterType) return false;
      return true;
    });

    return result.sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return sortOrder === "asc" ? timeA - timeB : timeB - timeA;
    });
  }, [timeline, filterType, sortOrder]);

  const getEventIcon = (type: TimelineEventType) => {
    switch (type) {
      case "TRANSACTION":
        return <ArrowDownRight className="w-3.5 h-3.5 text-blue-400" />;
      case "BRIDGE":
        return <ArrowRightLeft className="w-3.5 h-3.5 text-violet-400" />;
      case "FINDING":
        return <AlertTriangle className="w-3.5 h-3.5 text-red-400" />;
      case "ANALYST":
        return <UserCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case "AUDIT":
        return <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Timeline Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-cyber-surface border border-cyber-border rounded-lg text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">EVENT TYPE:</span>
          {(
            [
              ["ALL", "ALL"],
              ["TRANSACTION", "TX FLOWS"],
              ["BRIDGE", "BRIDGES"],
              ["FINDING", "FINDINGS"],
              ["ANALYST", "ANALYST ACTIONS"],
              ["AUDIT", "AUDIT LEDGER"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setFilterType(key)}
              className={cn(
                "px-2.5 py-1 rounded border transition-colors",
                filterType === key
                  ? "bg-cyber-primary text-white border-blue-400 font-bold"
                  : "bg-cyber-card text-slate-300 border-cyber-border hover:border-slate-500"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
          className="flex items-center gap-1.5 px-3 py-1 bg-cyber-card border border-cyber-border text-slate-200 hover:text-white rounded transition-colors"
        >
          <ArrowUpDown className="w-3.5 h-3.5 text-cyber-primary" />
          <span>ORDER: {sortOrder === "desc" ? "NEWEST FIRST" : "OLDEST FIRST"}</span>
        </button>
      </div>

      {/* Chronological Rail */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-cyber-border">
        {filteredEvents.map((evt) => (
          <div
            key={evt.id}
            onClick={() => onSelectEvent?.(evt)}
            className="relative flex items-start gap-4 group cursor-pointer"
          >
            {/* Timeline Dot Icon */}
            <div
              className={cn(
                "absolute -left-6 w-6 h-6 rounded-full border flex items-center justify-center bg-[#070b14] shrink-0 z-10 transition-transform group-hover:scale-110",
                evt.type === "FINDING"
                  ? "border-red-500 shadow-glow-rose"
                  : evt.type === "BRIDGE"
                  ? "border-violet-500"
                  : evt.type === "ANALYST"
                  ? "border-emerald-500"
                  : evt.type === "AUDIT"
                  ? "border-cyan-500"
                  : "border-blue-500 shadow-glow"
              )}
            >
              {getEventIcon(evt.type)}
            </div>

            {/* Event Card */}
            <div className="flex-1 bg-cyber-surface border border-cyber-border group-hover:border-cyber-border-light rounded-lg p-4 transition-all">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      evt.type === "FINDING"
                        ? "critical"
                        : evt.type === "BRIDGE"
                        ? "high"
                        : evt.type === "AUDIT"
                        ? "verified"
                        : "info"
                    }
                  >
                    {evt.type}
                  </Badge>
                  <span className="font-mono text-xs font-semibold text-slate-100">{evt.title}</span>
                </div>
                <span className="font-mono text-xs text-slate-400">{formatTimestamp(evt.timestamp)}</span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">{evt.description}</p>

              {(evt.relatedHash || evt.relatedAddress) && (
                <div className="mt-2.5 pt-2 border-t border-cyber-border/60 flex flex-wrap gap-3 text-[11px] font-mono text-slate-400">
                  {evt.relatedHash && (
                    <span>
                      TX: <code className="text-slate-300">{formatAddress(evt.relatedHash, 10, 8)}</code>
                    </span>
                  )}
                  {evt.relatedAddress && (
                    <span>
                      WALLET: <code className="text-cyber-primary">{formatAddress(evt.relatedAddress)}</code>
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {filteredEvents.length === 0 && (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">
            No timeline events match the selected filter.
          </div>
        )}
      </div>
    </div>
  );
}
