"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SeverityBadgeProps {
  severity: string;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const norm = severity.toUpperCase();
  const styles =
    norm === "CRITICAL"
      ? "bg-red-500/15 text-red-400 border-red-500/35"
      : norm === "HIGH"
        ? "bg-orange-500/15 text-orange-400 border-orange-500/35"
        : norm === "MEDIUM"
          ? "bg-amber-500/15 text-amber-400 border-amber-500/35"
          : "bg-green-500/15 text-green-400 border-green-500/35";

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded border font-mono text-[10px] font-semibold uppercase tracking-wider",
        styles,
        className
      )}
    >
      {norm}
    </span>
  );
}
