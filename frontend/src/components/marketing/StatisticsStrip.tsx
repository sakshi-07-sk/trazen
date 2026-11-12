"use client";

import React from "react";
import { AnimatedCounter } from "@/components/common/AnimatedCounter";

const ARCH_METRICS = [
  { value: 6, suffix: "", label: "Capabilities" },
  { value: 4, suffix: "", label: "Investigation Stages" },
  { value: 256, suffix: "-bit", label: "Hash Chain" },
  { value: 7, suffix: "", label: "System Components" },
];

export function StatisticsStrip() {
  return (
    <section aria-label="Platform Architecture Summary" className="bg-[#101111]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-0 lg:divide-x lg:divide-[#FF6A13]/40">
          {ARCH_METRICS.map((item) => (
            <div key={item.label} className="lg:px-8 first:lg:pl-0 last:lg:pr-0">
              <p
                className="text-4xl sm:text-5xl font-bold text-[#F1EEE6] tracking-tight"
                style={{ fontFamily: "var(--font-display), sans-serif" }}
              >
                <AnimatedCounter value={item.value} />
                {item.suffix}
              </p>
              <p
                className="mt-1.5 text-xs uppercase tracking-[0.16em] text-[#A6A39A]"
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Bold Orange Editorial Strip */}
      <div className="bg-[#FF6A13] py-3.5 px-4 sm:px-6 border-y border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <p
            className="text-xl sm:text-2xl font-extrabold uppercase tracking-[0.06em] text-[#080909]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            BLOCKCHAIN INSIGHTS. REAL-WORLD IMPACT.
          </p>
          <span
            className="text-[11px] uppercase tracking-[0.16em] text-[#080909]/80 font-semibold"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            ARCHITECTURAL SPECIFICATION
          </span>
        </div>
      </div>
    </section>
  );
}
