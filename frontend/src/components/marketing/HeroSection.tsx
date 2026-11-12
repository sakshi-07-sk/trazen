"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
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
          <p
            className="text-xs uppercase tracking-[0.22em] text-[#FF6A13] mb-4"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            CRYPTOTRACE — BLOCKCHAIN FORENSICS
          </p>

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
            Trace suspicious activity. Protect digital evidence.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <a
              href="#solutions"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              Explore Platform
              <ArrowRight className="w-4 h-4" />
            </a>

            <a
              href="#technology"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-sm bg-[#151616] border border-white/15 hover:border-[#FF6A13] text-[#F1EEE6] text-xs uppercase tracking-[0.14em] transition-colors"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              Discover Technology
            </a>
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
