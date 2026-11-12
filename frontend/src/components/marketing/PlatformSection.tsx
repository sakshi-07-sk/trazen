"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  CopyCheck,
  Coins,
  ShieldAlert,
  Network,
  FileLock2,
} from "lucide-react";

const CAPABILITIES = [
  {
    code: "01",
    title: "Blockchain Transaction Intelligence",
    description: "Trace blockchain transaction flows.",
    icon: Activity,
  },
  {
    code: "02",
    title: "Address Poisoning Detection",
    description: "Identify suspicious look-alike wallet addresses.",
    icon: CopyCheck,
  },
  {
    code: "03",
    title: "Dusting Attack Analysis",
    description: "Investigate suspicious small-value transfer patterns.",
    icon: Coins,
  },
  {
    code: "04",
    title: "Token Impersonation Detection",
    description: "Identify tokens with suspicious similarities to legitimate assets.",
    icon: ShieldAlert,
  },
  {
    code: "05",
    title: "Transaction Graph Integrity",
    description: "Validate relationships between wallets and transactions.",
    icon: Network,
  },
  {
    code: "06",
    title: "Tamper-Evident Forensic Auditing",
    description: "Protect the integrity of recorded investigation events.",
    icon: FileLock2,
  },
];

export function PlatformSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="solutions"
      className="relative bg-[#101111] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="max-w-3xl mb-14 lg:mb-16 space-y-4"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              OUR PLATFORM
            </span>
          </div>
          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            Six Core Forensic <span className="text-[#FF6A13]">Capabilities</span>
          </h2>
          <p className="text-base sm:text-lg text-[#A6A39A] leading-relaxed">
            Purpose-built analytical modules engineered to surface adversarial patterns and preserve
            verifiable investigation records.
          </p>
        </motion.div>

        {/* 3x2 Desktop Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CAPABILITIES.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.article
                key={item.code}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
                whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: idx * 0.06 }}
                className="group relative bg-[#151616] border border-white/10 hover:border-[#FF6A13]/50 p-7 rounded-sm transition-all duration-300 hover:-translate-y-1 flex flex-col justify-between min-h-[230px]"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="w-11 h-11 bg-[#1B1C1C] group-hover:bg-[#FF6A13] border border-white/10 group-hover:border-[#FF6A13] rounded-sm flex items-center justify-center transition-colors duration-300">
                      <Icon className="w-5 h-5 text-[#FF6A13] group-hover:text-[#080909] transition-colors duration-300" />
                    </div>
                    <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.18em] text-[#77746D] group-hover:text-[#FF6A13] transition-colors">
                      MOD // {item.code}
                    </span>
                  </div>

                  <h3 className="font-[family-name:var(--font-display)] text-2xl font-bold uppercase tracking-wide text-[#F1EEE6] mb-3">
                    {item.title}
                  </h3>

                  <p className="text-sm text-[#A6A39A] leading-relaxed">
                    {item.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between">
                  <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.18em] uppercase text-[#77746D]">
                    Forensic Module
                  </span>
                  <span className="h-[2px] w-6 bg-white/15 group-hover:w-12 group-hover:bg-[#FF6A13] transition-all duration-300" />
                </div>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
