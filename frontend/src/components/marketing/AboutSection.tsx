"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, FileSearch, GitBranch, ShieldCheck, Fingerprint } from "lucide-react";

export function AboutSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="about"
      className="relative bg-[#080909] py-24 lg:py-32 border-b border-white/10 overflow-hidden font-[family-name:var(--font-archivo)]"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Editorial Content */}
          <motion.div
            className="lg:col-span-6 space-y-6"
            initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-3">
              <span className="h-[1px] w-8 bg-[#FF6A13]" />
              <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
                WHO WE ARE
              </span>
            </div>

            <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
              Forensics for people who must{" "}
              <span className="text-[#FF6A13]">explain</span> their findings.
            </h2>

            <p className="text-base sm:text-lg text-[#A6A39A] leading-relaxed max-w-xl">
              CryptoTrace is a blockchain intelligence and digital forensics platform built to make
              investigations more transparent, reliable and secure.
            </p>

            <div className="pt-2">
              <a
                href="#solutions"
                className="group inline-flex items-center gap-3 px-6 py-3.5 bg-[#151616] hover:bg-[#1B1C1C] border border-white/10 hover:border-[#FF6A13]/60 text-[#F1EEE6] text-sm font-medium tracking-wider uppercase transition-colors rounded-sm"
              >
                <span>Learn More</span>
                <ArrowRight className="w-4 h-4 text-[#FF6A13] transition-transform group-hover:translate-x-1" />
              </a>
            </div>
          </motion.div>

          {/* Right Forensic Evidence Collage */}
          <motion.div
            className="lg:col-span-6"
            initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, delay: 0.12, ease: "easeOut" }}
          >
            <div className="relative bg-[#101111] border border-white/10 p-5 sm:p-6 rounded-sm">
              {/* Subtle monochrome grid background */}
              <div
                className="absolute inset-0 opacity-[0.06] pointer-events-none"
                style={{
                  backgroundImage:
                    "linear-gradient(to right, #F1EEE6 1px, transparent 1px), linear-gradient(to bottom, #F1EEE6 1px, transparent 1px)",
                  backgroundSize: "28px 28px",
                }}
              />

              <div className="relative grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Panel 1: Blockchain Investigation */}
                <div className="bg-[#151616] border border-white/10 p-4 rounded-sm flex flex-col justify-between min-h-[168px]">
                  <div className="flex items-center justify-between">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.16em] uppercase text-[#77746D]">
                      EXHIBIT 01 // TRACE
                    </span>
                    <FileSearch className="w-4 h-4 text-[#FF6A13]" />
                  </div>
                  <div className="my-3 space-y-1.5 font-[family-name:var(--font-jetbrains)] text-[11px]">
                    <div className="flex items-center justify-between text-[#A6A39A]">
                      <span>BLK #19482011</span>
                      <span className="text-[#FF6A13]">FLAGGED</span>
                    </div>
                    <div className="h-[1px] bg-white/10" />
                    <div className="text-[#77746D] truncate">0x7a9f...3c4e -&gt; 0x91d0...8b2a</div>
                    <div className="text-[#F1EEE6]">HOP DEPTH: 04</div>
                  </div>
                  <div className="text-xs font-medium uppercase tracking-wider text-[#F1EEE6]">
                    Blockchain Investigation
                  </div>
                </div>

                {/* Panel 2: Wallet Relationships */}
                <div className="bg-[#151616] border border-white/10 p-4 rounded-sm flex flex-col justify-between min-h-[168px]">
                  <div className="flex items-center justify-between">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.16em] uppercase text-[#77746D]">
                      EXHIBIT 02 // GRAPH
                    </span>
                    <GitBranch className="w-4 h-4 text-[#FF6A13]" />
                  </div>
                  <div className="my-2 flex items-center justify-center">
                    <svg
                      viewBox="0 0 180 68"
                      className="w-full h-16"
                      aria-label="Monochrome wallet relationship graph"
                    >
                      <line x1="28" y1="34" x2="88" y2="16" stroke="rgba(255,255,255,0.22)" strokeWidth="1.2" />
                      <line x1="28" y1="34" x2="88" y2="52" stroke="#FF6A13" strokeWidth="1.5" />
                      <line x1="88" y1="16" x2="152" y2="34" stroke="rgba(255,255,255,0.22)" strokeWidth="1.2" />
                      <line x1="88" y1="52" x2="152" y2="34" stroke="#FF6A13" strokeWidth="1.5" />
                      <circle cx="28" cy="34" r="7" fill="#1B1C1C" stroke="#F1EEE6" strokeWidth="1.5" />
                      <circle cx="88" cy="16" r="6" fill="#1B1C1C" stroke="#A6A39A" strokeWidth="1.2" />
                      <circle cx="88" cy="52" r="7" fill="#1B1C1C" stroke="#FF6A13" strokeWidth="1.8" />
                      <circle cx="152" cy="34" r="7" fill="#1B1C1C" stroke="#F1EEE6" strokeWidth="1.5" />
                    </svg>
                  </div>
                  <div className="text-xs font-medium uppercase tracking-wider text-[#F1EEE6]">
                    Wallet Relationships
                  </div>
                </div>

                {/* Panel 3: Transaction Evidence */}
                <div className="bg-[#151616] border border-white/10 p-4 rounded-sm flex flex-col justify-between min-h-[168px]">
                  <div className="flex items-center justify-between">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.16em] uppercase text-[#77746D]">
                      EXHIBIT 03 // EVIDENCE
                    </span>
                    <ShieldCheck className="w-4 h-4 text-[#FF6A13]" />
                  </div>
                  <div className="my-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-[#FF6A13] rounded-full" />
                      <span className="font-[family-name:var(--font-jetbrains)] text-[11px] text-[#F1EEE6]">
                        SHA-256 SEALED
                      </span>
                    </div>
                    <div className="font-[family-name:var(--font-jetbrains)] text-[10px] text-[#77746D] break-all">
                      9f86d081884c7d659a2feaa0c55ad015
                    </div>
                  </div>
                  <div className="text-xs font-medium uppercase tracking-wider text-[#F1EEE6]">
                    Transaction Evidence
                  </div>
                </div>

                {/* Panel 4: Digital Forensic Analysis */}
                <div className="bg-[#151616] border border-white/10 p-4 rounded-sm flex flex-col justify-between min-h-[168px]">
                  <div className="flex items-center justify-between">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.16em] uppercase text-[#77746D]">
                      EXHIBIT 04 // ANALYSIS
                    </span>
                    <Fingerprint className="w-4 h-4 text-[#FF6A13]" />
                  </div>
                  <div className="my-3 space-y-1.5">
                    <div className="flex justify-between font-[family-name:var(--font-jetbrains)] text-[11px]">
                      <span className="text-[#A6A39A]">POISONING CHECK</span>
                      <span className="text-[#FF6A13]">MATCH</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#1B1C1C] overflow-hidden">
                      <div className="w-4/5 h-full bg-[#FF6A13]" />
                    </div>
                    <div className="flex justify-between font-[family-name:var(--font-jetbrains)] text-[10px] text-[#77746D]">
                      <span>DUSTING PATTERN</span>
                      <span>LOGGED</span>
                    </div>
                  </div>
                  <div className="text-xs font-medium uppercase tracking-wider text-[#F1EEE6]">
                    Digital Forensic Analysis
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
