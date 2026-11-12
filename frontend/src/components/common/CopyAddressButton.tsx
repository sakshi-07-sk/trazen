"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";
import { useForensic } from "@/context/ForensicContext";
import { cn } from "@/lib/utils";

interface CopyAddressButtonProps {
  value: string;
  label?: string;
  truncate?: boolean;
  className?: string;
}

export function CopyAddressButton({
  value,
  label,
  truncate = true,
  className,
}: CopyAddressButtonProps) {
  const [copied, setCopied] = useState(false);
  const { addToast } = useForensic();

  const display =
    label ||
    (truncate && value.length > 16
      ? `${value.slice(0, 8)}...${value.slice(-6)}`
      : value);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      addToast({
        title: "Copied to clipboard",
        description: value,
        variant: "success",
      });
      setTimeout(() => setCopied(false), 1800);
    } catch {
      addToast({
        title: "Copy failed",
        description: "Clipboard permission denied.",
        variant: "error",
      });
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={value}
      aria-label={`Copy ${value}`}
      className={cn(
        "inline-flex items-center gap-1.5 font-mono text-xs text-cyber-text hover:text-cyber-cyan transition-colors group",
        className
      )}
    >
      <span>{display}</span>
      {copied ? (
        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
      ) : (
        <Copy className="w-3.5 h-3.5 text-cyber-muted group-hover:text-cyber-cyan shrink-0" />
      )}
    </button>
  );
}
