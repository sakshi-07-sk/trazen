import React from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "clean"
  | "info"
  | "verified"
  | "demo";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  size?: "sm" | "md";
}

export function Badge({ children, variant = "info", className, size = "sm" }: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    critical: "bg-red-500/15 text-red-400 border-red-500/30",
    high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
    medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    low: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    clean: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    info: "bg-slate-800 text-slate-300 border-slate-700",
    verified: "bg-emerald-950/60 text-emerald-400 border-emerald-500/40",
    demo: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs font-mono tracking-wider",
    md: "px-2.5 py-1 text-xs font-mono font-medium tracking-wider",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border uppercase transition-colors select-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      <span
        className={cn("w-1.5 h-1.5 rounded-full shrink-0", {
          "bg-red-400 animate-pulse": variant === "critical",
          "bg-orange-400": variant === "high",
          "bg-amber-400": variant === "medium",
          "bg-blue-400": variant === "low",
          "bg-emerald-400": variant === "clean" || variant === "verified",
          "bg-slate-400": variant === "info",
          "bg-violet-400": variant === "demo",
        })}
      />
      {children}
    </span>
  );
}
