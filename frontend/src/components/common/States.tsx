"use client";

import React from "react";
import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export function SkeletonLoader({
  rows = 3,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-12 rounded-lg bg-white/[0.04] border border-white/[0.06] animate-pulse"
        />
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="glass-panel rounded-lg p-10 text-center flex flex-col items-center justify-center gap-3 border border-white/[0.08]">
      <div className="p-3 rounded-full bg-cyber-primary-dim border border-cyber-cyan/25 text-cyber-cyan">
        <Inbox className="w-5 h-5" />
      </div>
      <h3 className="text-sm font-semibold text-cyber-text uppercase tracking-wider font-mono">
        {title}
      </h3>
      <p className="text-xs text-cyber-muted max-w-md">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Unable to load forensic data",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-lg p-6 bg-red-950/20 border border-red-500/30 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
      <div className="flex-1 space-y-2">
        <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-red-300">
          {title}
        </h3>
        <p className="text-xs text-red-200/80">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-red-400/40 text-red-200 hover:bg-red-500/15 font-mono text-[11px] transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            RETRY REQUEST
          </button>
        )}
      </div>
    </div>
  );
}
