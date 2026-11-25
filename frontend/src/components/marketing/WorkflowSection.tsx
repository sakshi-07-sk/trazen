"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, CheckCircle2 } from "lucide-react";

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Target Ingestion",
    role: "User Action",
    description: "Enter an Ethereum (0x) or Bitcoin (1/3/bc1) address, tx hash, or upload a custom JSON/CSV transaction batch.",
  },
  {
    step: "02",
    title: "Cryptographic Validation",
    role: "Role 1 Engine",
    description: "Validates cryptographic checksums (EIP-55, Base58Check, Bech32) and rejects malformed payloads before execution.",
  },
  {
    step: "03",
    title: "Decimal Normalization",
    role: "Role 1 Ingestion",
    description: "Standardizes heterogenous UTXO and account models into exact Decimal precision, preventing IEEE-754 float drift.",
  },
  {
    step: "04",
    title: "Multi-Hop Traversal",
    role: "Role 1 & 2 Engine",
    description: "NetworkX constructs directed transaction topologies extending 1 to 5 hops while tracking confirmed vs inferred edges.",
  },
  {
    step: "05",
    title: "Entity Clustering",
    role: "Role 2 Forensics",
    description: "Clusters co-spent wallets via CIOH while suppressing false mergers on CoinJoin and collaborative transactions.",
  },
  {
    step: "06",
    title: "Anomaly Detection",
    role: "Role 2 Forensics",
    description: "Fires deterministic rules: peel-chain tracking, privacy pool identification, and rapid structuring analysis.",
  },
  {
    step: "07",
    title: "4D Explainable Risk",
    role: "Role 3 Scoring",
    description: "Calculates Risk Priority, Attribution Confidence, Known Risk Exposure, and Coverage without black-box scores.",
  },
  {
    step: "08",
    title: "Graph Exploration",
    role: "Role 4 Command Center",
    description: "Interactive Cytoscape.js canvas with hop depth filters, monetary thresholds, and deep-dive wallet drawers.",
  },
  {
    step: "09",
    title: "Evidence Vault Sealing",
    role: "Role 3 Audit",
    description: "Chains all ingested records, findings, and operator actions into an immutable SHA-256 tamper-evident ledger.",
  },
  {
    step: "10",
    title: "Court-Ready Dossier",
    role: "Role 4 Reporting",
    description: "Generates comprehensive, cryptographically signed investigation dossiers in Markdown and print-ready formats.",
  },
];

export function WorkflowSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="workflow"
      className="relative bg-[#080909] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          className="max-w-3xl mb-16 space-y-4"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              END-TO-END INVESTIGATION PIPELINE
            </span>
          </div>

          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            The 10-Stage Forensic <span className="text-[#FF6A13]">Workflow</span>
          </h2>

          <p className="text-base sm:text-lg text-[#A6A39A] leading-relaxed pt-2">
            From raw, unverified blockchain inputs to immutable, court-admissible forensic intelligence dossiers.
            Every stage maintains strict mathematical rigor and cryptographic auditability.
          </p>
        </motion.div>

        {/* 10-Step Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {WORKFLOW_STEPS.map((s, idx) => (
            <motion.div
              key={s.step}
              className="bg-[#101111] border border-white/10 hover:border-[#FF6A13]/50 rounded-sm p-5 flex flex-col justify-between transition-colors group"
              initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
              whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.1 }}
              transition={{ duration: 0.35, delay: idx * 0.04 }}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span
                    className="text-lg font-bold text-[#FF6A13] font-mono"
                    style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                  >
                    {s.step}
                  </span>
                  <span
                    className="text-[10px] text-[#A6A39A] uppercase tracking-wider font-mono bg-[#151616] px-2 py-0.5 rounded-sm border border-white/5"
                    style={{ fontFamily: "var(--font-jetbrains), monospace" }}
                  >
                    {s.role}
                  </span>
                </div>

                <h3
                  className="text-sm font-bold uppercase text-[#F1EEE6] mb-2 group-hover:text-[#FF6A13] transition-colors"
                  style={{ fontFamily: "var(--font-display), sans-serif" }}
                >
                  {s.title}
                </h3>

                <p className="text-xs text-[#A6A39A] leading-relaxed">{s.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-1.5 text-[11px] text-[#22C55E] font-mono">
                <CheckCircle2 className="w-3 h-3 shrink-0" />
                <span>Verified Output</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA Banner */}
        <div className="mt-12 p-6 sm:p-8 bg-[#101111] border border-white/10 rounded-sm flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-1">
            <h4
              className="text-lg font-bold uppercase text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-display), sans-serif" }}
            >
              Experience the 10-Step Workflow Live
            </h4>
            <p className="text-xs text-[#A6A39A] font-mono">
              Test Lazarus Group (ETH), Ransomware (BTC), or import a custom transaction dataset.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/investigations"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors font-mono"
            >
              Start Investigation
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-sm bg-[#151616] border border-white/15 hover:border-[#FF6A13] text-[#F1EEE6] text-xs uppercase tracking-[0.14em] transition-colors font-mono"
            >
              View Command Center
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
