"use client";

import React, { useEffect, useState } from "react";

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  brackets?: boolean;
  decimals?: number;
  durationMs?: number;
  className?: string;
}

export function AnimatedCounter({
  value,
  prefix = "",
  suffix = "",
  brackets = false,
  decimals = 0,
  durationMs = 750,
  className = "",
}: AnimatedCounterProps) {
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReduced || durationMs <= 0) {
      setDisplay(value);
      return;
    }

    let rafId = 0;
    const start = performance.now();
    const from = 0;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (value - from) * eased);
      if (progress < 1) {
        rafId = requestAnimationFrame(tick);
      }
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [value, durationMs]);

  const formatted =
    decimals > 0
      ? display.toFixed(decimals)
      : Math.round(display).toLocaleString();

  const inner = `${prefix}${formatted}${suffix}`;
  return (
    <span className={className}>
      {brackets ? `[ ${inner} ]` : inner}
    </span>
  );
}
