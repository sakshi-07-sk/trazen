import React from "react";
import { cn } from "@/lib/utils";
import { Badge, BadgeVariant } from "./Badge";

interface RiskMeterProps {
  score: number; // 0 to 100
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function RiskMeter({ score, size = "md", showLabel = true, className }: RiskMeterProps) {
  const boundedScore = Math.max(0, Math.min(100, score));

  let variant: BadgeVariant = "clean";
  let label = "CLEAN";
  let color = "bg-emerald-500";
  let textColor = "text-emerald-400";

  if (boundedScore >= 90) {
    variant = "critical";
    label = "CRITICAL";
    color = "bg-red-500";
    textColor = "text-red-400";
  } else if (boundedScore >= 70) {
    variant = "high";
    label = "HIGH";
    color = "bg-orange-500";
    textColor = "text-orange-400";
  } else if (boundedScore >= 40) {
    variant = "medium";
    label = "MEDIUM";
    color = "bg-amber-500";
    textColor = "text-amber-400";
  } else if (boundedScore >= 20) {
    variant = "low";
    label = "LOW";
    color = "bg-blue-500";
    textColor = "text-blue-400";
  }

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-mono text-slate-400">THREAT SCORE</span>
        <div className="flex items-center gap-2">
          <span className={cn("font-mono font-bold", textColor)}>{boundedScore}/100</span>
          {showLabel && <Badge variant={variant}>{label}</Badge>}
        </div>
      </div>
      <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
        <div
          className={cn("h-full transition-all duration-300 rounded-full", color)}
          style={{ width: `${boundedScore}%` }}
        />
      </div>
    </div>
  );
}
