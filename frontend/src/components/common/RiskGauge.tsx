"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface RiskGaugeProps {
  label: string;
  score: number; // 0 - 100
  subtitle?: string;
  accent?: "cyan" | "red" | "orange" | "amber" | "green";
  className?: string;
}

export function RiskGauge({
  label,
  score,
  subtitle,
  accent,
  className,
}: RiskGaugeProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const resolvedAccent =
    accent ||
    (clamped >= 80
      ? "red"
      : clamped >= 60
        ? "orange"
        : clamped >= 35
          ? "amber"
          : "green");

  const strokeColor = {
    cyan: "#FF6A13",
    red: "#EF4444",
    orange: "#FF6A13",
    amber: "#F59E0B",
    green: "#22C55E",
  }[resolvedAccent];

  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (clamped / 100) * circumference;

  return (
    <div
      className={cn(
        "glass-panel rounded-sm p-4 flex flex-col justify-between gap-3 border border-white/10",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-cyber-muted">
          {label}
        </span>
        <span
          className="font-mono text-xs font-semibold"
          style={{ color: strokeColor }}
        >
          [ {clamped} / 100 ]
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-24 h-24 shrink-0">
          <svg
            viewBox="0 0 100 100"
            className="w-full h-full -rotate-90"
            role="img"
            aria-label={`${label}: ${clamped} out of 100`}
          >
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="7"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke={strokeColor}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={{ transition: "stroke-dashoffset 600ms ease-out" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-lg font-bold text-cyber-text">
              {clamped}
            </span>
            <span className="font-mono text-[9px] text-cyber-muted uppercase">
              INDEX
            </span>
          </div>
        </div>
        {subtitle && (
          <p className="text-xs text-cyber-muted leading-relaxed">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
