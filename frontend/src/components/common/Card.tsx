import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  glow?: "none" | "blue" | "rose" | "emerald";
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
}

export function Card({
  className,
  children,
  glow = "none",
  title,
  subtitle,
  action,
  ...props
}: CardProps) {
  const glowStyles = {
    none: "",
    blue: "border-blue-500/30 shadow-glow",
    rose: "border-red-500/30 shadow-glow-rose",
    emerald: "border-emerald-500/30 shadow-glow-emerald",
  };

  return (
    <div
      className={cn(
        "bg-cyber-surface/90 border border-cyber-border rounded-lg p-5 backdrop-blur-sm transition-all duration-150",
        glowStyles[glow],
        className
      )}
      {...props}
    >
      {(title || subtitle || action) && (
        <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-cyber-border/60">
          <div>
            {title && <h3 className="text-sm font-semibold tracking-wide text-slate-100 flex items-center gap-2">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
