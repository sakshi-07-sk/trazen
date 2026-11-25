"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Play, ShieldAlert } from "lucide-react";
import { BlockchainHeroVisual } from "./BlockchainHeroVisual";

export function HeroSection() {
  const prefersReduced = useReducedMotion();

  return (
    <section
      id="home"
      className="relative pt-28 pb-16 sm:pt-32 sm:pb-24 bg-[#080909] border-b border-white/10 overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 grid lg:grid-cols-12 gap-10 lg:gap-8 items-center">
        {/* Left: Editorial Headline & CTAs */}
        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="lg:col-span-6"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-[#151616] border border-[#FF6A13]/40 text-[#FF6A13] text-[11px] font-mono tracking-wider uppercase mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF6A13] animate-pulse" />
            CRYPTOTRACE — BLOCKCHAIN FORENSICS & THREAT INTELLIGENCE
          </div>

          <h1
            className="text-5xl sm:text-6xl lg:text-7xl font-extrabold uppercase leading-[0.94] tracking-tight text-[#F1EEE6]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            INTELLIGENCE
            <br />
            BEHIND EVERY
            <br />
            <span className="text-[#FF6A13]">INVESTIGATION.</span>
          </h1>

          <p
            className="mt-6 text-base sm:text-lg text-[#A6A39A] max-w-xl leading-relaxed"
            style={{ fontFamily: "var(--font-archivo), sans-serif" }}
          >
            Trace multi-chain illicit crypto flows, unmask peel-chains and mixing pools, and seal court-ready
            evidence dossiers with deterministic SHA-256 provenance.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/investigations"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors font-mono"
            >
              Start Investigation
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-sm bg-[#151616] border border-white/15 hover:border-[#FF6A13] text-[#F1EEE6] text-xs uppercase tracking-[0.14em] transition-colors font-mono"
            >
              <Play className="w-3.5 h-3.5 text-[#FF6A13] fill-current" />
              Run Live Demo
            </Link>

            <a
              href="#problem"
              className="inline-flex items-center gap-1.5 px-4 py-3.5 text-xs text-[#A6A39A] hover:text-[#F1EEE6] uppercase tracking-[0.12em] transition-colors font-mono"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-[#FF6A13]" />
              The Problem
            </a>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex items-center gap-6 text-[11px] font-mono text-[#A6A39A]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
              <span>Deterministic Offline Mode</span>
            </div>
            <div>•</div>
            <div>Bitcoin UTXO & Ethereum EVM</div>
            <div>•</div>
            <div>SHA-256 Chain of Custody</div>
          </div>
        </motion.div>

        {/* Right: Blockchain Security Illustration */}
        <div className="lg:col-span-6">
          <BlockchainHeroVisual />
        </div>
      </div>
    </section>
  );
}
