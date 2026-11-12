"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ShieldAlert, ArrowLeftRight, FileCheck2, Waypoints } from "lucide-react";

const USE_CASES = [
  {
    code: "UC-01",
    title: "Blockchain Fraud Investigation",
    description:
      "Reconstruct fund dispersion paths, isolate deceptive address-poisoning attempts, and document findings in structured case files.",
    icon: ShieldAlert,
    tag: "CASE RECONSTRUCTION",
  },
  {
    code: "UC-02",
    title: "Cryptocurrency Transaction Analysis",
    description:
      "Inspect multi-hop token and native asset transfers, dusting patterns, and anomalous counterparties across transaction histories.",
    icon: ArrowLeftRight,
    tag: "FLOW INSPECTION",
  },
  {
    code: "UC-03",
    title: "Digital Forensic Evidence Review",
    description:
      "Examine recorded investigation artifacts backed by SHA-256 hash-chain logs so reviewers can verify post-capture integrity.",
    icon: FileCheck2,
    tag: "AUDIT VERIFICATION",
  },
  {
    code: "UC-04",
    title: "Suspicious Wallet Relationship Analysis",
    description:
      "Map clusters, intermediary hubs, and look-alike token or wallet interactions using NetworkX graph analysis.",
    icon: Waypoints,
    tag: "GRAPH CORRELATION",
  },
];

export function UseCasesSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="use-cases"
      className="relative bg-[#101111] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          className="max-w-3xl mb-14 space-y-4"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              USE CASES
            </span>
          </div>
          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            Built for High-Stakes <span className="text-[#FF6A13]">Forensic</span> Scenarios
          </h2>
        </motion.div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {USE_CASES.map((uc, idx) => {
            const Icon = uc.icon;
            return (
              <motion.article
                key={uc.code}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
                whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: idx * 0.07 }}
                className="group bg-[#151616] border border-white/10 hover:border-[#FF6A13]/50 p-7 sm:p-8 rounded-sm transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[11px] tracking-[0.18em] uppercase text-[#FF6A13]">
                      {uc.code} {"//"} {uc.tag}
                    </span>
                    <div className="w-10 h-10 bg-[#1B1C1C] border border-white/10 rounded-sm flex items-center justify-center">
                      <Icon className="w-5 h-5 text-[#FF6A13]" />
                    </div>
                  </div>

                  {/* Restrained monochrome micro-diagram */}
                  <div className="mb-5 p-3 bg-[#080909] border border-white/10 rounded-sm flex items-center justify-between font-[family-name:var(--font-jetbrains)] text-[10px] text-[#77746D]">
                    <span>NODE_A</span>
                    <span className="flex-1 mx-3 h-[1px] bg-white/15 relative">
                      <span className="absolute right-0 -top-[2px] w-1.5 h-1.5 bg-[#FF6A13] rounded-full" />
                    </span>
                    <span className="text-[#F1EEE6]">VERIFIED_LOG</span>
                  </div>

                  <h3 className="font-[family-name:var(--font-display)] text-3xl font-bold uppercase tracking-wide text-[#F1EEE6] mb-3">
                    {uc.title}
                  </h3>
                  <p className="text-sm text-[#A6A39A] leading-relaxed">
                    {uc.description}
                  </p>
                </div>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
