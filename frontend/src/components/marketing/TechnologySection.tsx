"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Layers, Server, Database, Cpu, Share2, Lock } from "lucide-react";

const ARCH_LAYERS = [
  {
    id: "frontend",
    layer: "PRESENTATION LAYER",
    name: "Next.js / React / TypeScript",
    detail: "Investigation workspace, RBAC portals, and interactive graph exploration UI.",
    icon: Layers,
  },
  {
    id: "api",
    layer: "API GATEWAY",
    name: "FastAPI Service",
    detail: "Typed REST endpoints for wallet queries, case management, and forensic runs.",
    icon: Server,
  },
  {
    id: "data",
    layer: "DATA LAYER",
    name: "SQLAlchemy & Database",
    detail: "Async relational persistence for cases, findings, users, and audit records.",
    icon: Database,
  },
  {
    id: "intelligence",
    layer: "INTELLIGENCE ENGINE",
    name: "Transaction & Risk Detection",
    detail: "Address poisoning, dusting, token impersonation, and behavioural heuristics.",
    icon: Cpu,
  },
  {
    id: "graph",
    layer: "GRAPH ANALYSIS",
    name: "NetworkX",
    detail: "Multi-hop wallet relationship modelling, centrality, and flow path analysis.",
    icon: Share2,
  },
  {
    id: "integrity",
    layer: "EVIDENCE INTEGRITY",
    name: "SHA-256 Hash Chain",
    detail: "Chained cryptographic digests linking recorded investigation events.",
    icon: Lock,
  },
];

export function TechnologySection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="technology"
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
              SYSTEM ARCHITECTURE
            </span>
          </div>
          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            Engineered for <span className="text-[#FF6A13]">Verifiable</span> Intelligence
          </h2>
          <p className="text-base sm:text-lg text-[#A6A39A] leading-relaxed">
            A modular forensic stack connecting browser-based investigation tools to FastAPI
            services, NetworkX graph computation, and cryptographic audit chaining.
          </p>
        </motion.div>

        {/* Architecture Diagram */}
        <div className="relative bg-[#080909] border border-white/10 p-6 sm:p-8 lg:p-10 rounded-sm">
          {/* Top-to-bottom / grid connector SVG */}
          <div className="mb-8 pb-6 border-b border-white/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 bg-[#FF6A13] rounded-full" />
              <span className="font-[family-name:var(--font-jetbrains)] text-xs uppercase tracking-[0.18em] text-[#F1EEE6]">
                CRYPTOTRACE // IMPLEMENTED STACK TOPOLOGY
              </span>
            </div>
            <span className="font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-[0.16em] text-[#77746D]">
              6 CORE ARCHITECTURAL LAYERS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
            {ARCH_LAYERS.map((node, idx) => {
              const Icon = node.icon;
              return (
                <motion.div
                  key={node.id}
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 18 }}
                  whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.45, delay: idx * 0.06 }}
                  className="relative bg-[#151616] border border-white/10 p-6 rounded-sm"
                >
                  {/* Orange connector accent bar on left */}
                  <div className="absolute left-0 top-6 bottom-6 w-[2px] bg-[#FF6A13]" />

                  <div className="flex items-center justify-between mb-4 pl-2">
                    <span className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.2em] uppercase text-[#FF6A13]">
                      {node.layer}
                    </span>
                    <Icon className="w-4 h-4 text-[#A6A39A]" />
                  </div>

                  <h3 className="font-[family-name:var(--font-display)] text-2xl font-bold uppercase tracking-wide text-[#F1EEE6] mb-2 pl-2">
                    {node.name}
                  </h3>

                  <p className="text-sm text-[#A6A39A] leading-relaxed pl-2">
                    {node.detail}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Dataflow pipeline bar */}
          <div className="mt-8 pt-6 border-t border-white/10">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-[0.14em] text-[#A6A39A]">
              <span className="text-[#F1EEE6]">Next.js UI</span>
              <span className="hidden md:inline text-[#FF6A13]">———&gt;</span>
              <span className="text-[#F1EEE6]">FastAPI REST</span>
              <span className="hidden md:inline text-[#FF6A13]">———&gt;</span>
              <span className="text-[#F1EEE6]">NetworkX + Risk Engine</span>
              <span className="hidden md:inline text-[#FF6A13]">———&gt;</span>
              <span className="text-[#F1EEE6]">SQLAlchemy + SHA-256 Chain</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
