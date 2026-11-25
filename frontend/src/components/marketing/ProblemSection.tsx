"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Layers,
  Shuffle,
  HelpCircle,
  ShieldAlert,
  ArrowRight,
  ShieldCheck,
  Scale,
  Building2,
  Lock,
} from "lucide-react";

const CHALLENGES = [
  {
    icon: Layers,
    title: "Multi-Chain Architectural Divergence",
    subtitle: "UTXO vs Account-Based Incompatibility",
    description:
      "Bitcoin's multi-input/output UTXO structure and Ethereum's account-based nonce/call traces operate under fundamentally different mechanics. Legacy tools apply naive 1-to-1 heuristics, causing severe false-positive attribution across Bitcoin addresses.",
    solution: "Explicit intermediate UTXO transaction modeling and chain-specific normalizers.",
  },
  {
    icon: Shuffle,
    title: "Evasive Obfuscation Techniques",
    subtitle: "Peel-Chains, Mixers & Rapid Structuring",
    description:
      "Adversaries conceal illicit fund flows through multi-hop peeling chains, privacy pools (Tornado Cash, Wasabi), and sub-threshold burst structuring designed to bypass static exchange surveillance rules.",
    solution: "Automated peel-chain sequence detection with CoinJoin false-positive suppression guards.",
  },
  {
    icon: HelpCircle,
    title: "The Black-Box Scoring Dilemma",
    subtitle: "Inadmissible Predictions in Court",
    description:
      "Commercial platforms output opaque probability scores (e.g. '87% Risk') derived from unexplainable machine learning models. Under legal cross-examination, single risk numbers fail evidentiary scrutiny without granular rule attribution.",
    solution: "4-Dimensional orthogonal scoring: Risk Priority, Attribution Confidence, Known Risk, and Coverage.",
  },
  {
    icon: Lock,
    title: "Chain of Custody & Precision Loss",
    subtitle: "Tampering Risks & Float Drift",
    description:
      "Standard databases lack non-repudiation proofs, leaving evidence vulnerable to alteration claims. Furthermore, JavaScript IEEE 754 floating-point calculations create rounding drift across 8-decimal Satoshi and 18-decimal Wei flows.",
    solution: "Strict Python Decimal / BigInt arithmetic sealed in a tamper-evident SHA-256 hash-chain ledger.",
  },
];

const STAKEHOLDERS = [
  {
    role: "Law Enforcement & FIUs",
    icon: ShieldCheck,
    detail: "Generate court-admissible forensic dossiers with unbroken SHA-256 cryptographic chain of custody.",
  },
  {
    role: "AML / CFT Compliance Officers",
    icon: Building2,
    detail: "Rapidly triage high-volume suspicious alerts, screen sanctioned entities, and prepare SAR-ready reports.",
  },
  {
    role: "Cybersecurity Incident Responders",
    icon: ShieldAlert,
    detail: "Instantly trace exploit drain paths, ransomware extortions, and cross-chain bridge hops in real time.",
  },
  {
    role: "Legal Counsel & Forensic Auditors",
    icon: Scale,
    detail: "Present transparent, rule-grounded evidence that clearly explains why entities were flagged without guesswork.",
  },
];

export function ProblemSection() {
  const prefersReduced = useReducedMotion();

  return (
    <section
      id="problem"
      className="relative bg-[#080909] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="max-w-3xl mb-16 space-y-4"
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          whileInView={prefersReduced ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              THE PROBLEM WE SOLVE
            </span>
          </div>

          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            Illicit Crypto Flows Hide in Plain Sight.{" "}
            <span className="text-[#FF6A13]">Investigators Need Evidence,</span> Not Guesswork.
          </h2>

          <p className="text-base sm:text-lg text-[#A6A39A] leading-relaxed pt-2">
            Billions in ransomware payments, DeFi exploit proceeds, and sanctions-evasion capital move through
            blockchain networks annually. Financial crime investigators cannot rely on black-box heuristics or opaque
            risk scores that collapse under legal scrutiny.
          </p>
        </motion.div>

        {/* 4 Core Challenge Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 mb-20">
          {CHALLENGES.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                className="bg-[#101111] border border-white/10 hover:border-[#FF6A13]/40 rounded-sm p-6 sm:p-8 transition-colors flex flex-col justify-between"
                initial={prefersReduced ? false : { opacity: 0, y: 20 }}
                whileInView={prefersReduced ? undefined : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.4, delay: idx * 0.08 }}
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <span className="w-10 h-10 rounded-sm bg-[#151616] border border-white/10 flex items-center justify-center text-[#FF6A13]">
                      <Icon className="w-5 h-5" />
                    </span>
                    <span
                      className="text-xs font-mono text-[#A6A39A] uppercase tracking-wider"
                      style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                    >
                      CHALLENGE 0{idx + 1}
                    </span>
                  </div>

                  <h3
                    className="text-xl font-bold uppercase text-[#F1EEE6] mb-1"
                    style={{ fontFamily: "var(--font-display), sans-serif" }}
                  >
                    {item.title}
                  </h3>
                  <div
                    className="text-xs text-[#FF6A13] uppercase tracking-wider mb-3 font-mono"
                    style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                  >
                    {item.subtitle}
                  </div>

                  <p className="text-sm text-[#A6A39A] leading-relaxed mb-6">{item.description}</p>
                </div>

                <div className="pt-4 border-t border-white/10 bg-[#151616]/60 -mx-6 -mb-6 p-4 rounded-b-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-[#22C55E] text-xs font-mono font-bold shrink-0">TRAZEN FIX:</span>
                    <span className="text-xs text-[#F1EEE6] font-mono">{item.solution}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Who Benefits Section */}
        <div className="bg-[#101111] border border-white/10 rounded-sm p-8 sm:p-10">
          <div className="max-w-2xl mb-8">
            <span
              className="text-xs uppercase tracking-[0.2em] text-[#FF6A13] font-mono block mb-2"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              TARGET BENEFICIARIES
            </span>
            <h3
              className="text-2xl sm:text-3xl font-bold uppercase text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Who Benefits from Explainable Blockchain Forensics
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {STAKEHOLDERS.map((s) => {
              const Icon = s.icon;
              return (
                <div key={s.role} className="bg-[#151616] p-5 rounded-sm border border-white/10 space-y-3">
                  <span className="w-8 h-8 rounded-sm bg-[#080909] border border-white/10 flex items-center justify-center text-[#FF6A13]">
                    <Icon className="w-4 h-4" />
                  </span>
                  <h4 className="text-sm font-bold uppercase text-[#F1EEE6] font-mono">{s.role}</h4>
                  <p className="text-xs text-[#A6A39A] leading-relaxed">{s.detail}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex flex-wrap items-center justify-between gap-4">
            <div className="text-xs text-[#A6A39A] font-mono">
              Ready to experience deterministic, court-admissible blockchain investigations?
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/investigations"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors font-mono"
              >
                Start Investigation
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-sm bg-[#151616] border border-white/15 hover:border-[#FF6A13] text-[#F1EEE6] text-xs uppercase tracking-[0.14em] transition-colors font-mono"
              >
                Launch SOC Demo
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
