"use client";

import React from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useForensic } from "@/context/ForensicContext";
import { cn } from "@/lib/utils";

export function ToastContainer() {
  const { toasts, dismissToast } = useForensic();
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 left-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none no-print"
      aria-live="polite"
    >
      {toasts.map((toast) => {
        const Icon =
          toast.variant === "success"
            ? CheckCircle2
            : toast.variant === "error" || toast.variant === "warning"
              ? AlertCircle
              : Info;
        const borderClass =
          toast.variant === "success"
            ? "border-green-500/35 text-green-300"
            : toast.variant === "error"
              ? "border-red-500/35 text-red-300"
              : toast.variant === "warning"
                ? "border-amber-500/35 text-amber-300"
                : "border-cyber-cyan/35 text-cyber-cyan";

        return (
          <div
            key={toast.id}
            className={cn(
              "pointer-events-auto glass-panel rounded-lg px-3.5 py-2.5 flex items-start gap-2.5 shadow-glow-sm",
              borderClass
            )}
          >
            <Icon className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="font-mono text-[11px] font-semibold text-cyber-text">
                {toast.title}
              </div>
              {toast.description && (
                <div className="font-mono text-[10px] text-cyber-muted truncate">
                  {toast.description}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => dismissToast(toast.id)}
              className="text-cyber-muted hover:text-cyber-text"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
