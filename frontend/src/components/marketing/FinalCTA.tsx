"use client";

import React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export function FinalCTA() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="contact"
      className="relative bg-[#080909] py-28 lg:py-36 border-b border-white/10 overflow-hidden font-[family-name:var(--font-archivo)]"
    >
      {/* Subtle animated global blockchain network SVG */}
      <div className="absolute inset-0 pointer-events-none opacity-25" aria-hidden="true">
        <svg viewBox="0 0 1200 500" className="w-full h-full object-cover">
          <g stroke="rgba(255,255,255,0.12)" strokeWidth="1" fill="none">
            <path d="M80 120 L280 210 L520 130 L760 240 L1020 140 L1140 260" />
            <path d="M120 380 L340 290 L600 360 L860 270 L1080 390" />
            <path d="M280 210 L340 290" stroke="#FF6A13" strokeOpacity="0.45" />
            <path d="M520 130 L600 360" />
            <path d="M760 240 L860 270" stroke="#FF6A13" strokeOpacity="0.45" />
          </g>
          {[
            [80, 120],
            [280, 210],
            [520, 130],
            [760, 240],
            [1020, 140],
            [340, 290],
            [600, 360],
            [860, 270],
          ].map(([cx, cy], idx) => (
            <motion.circle
              key={`${cx}-${cy}`}
              cx={cx}
              cy={cy}
              r={idx % 2 === 0 ? 4 : 5}
              fill={idx % 2 === 0 ? "#F1EEE6" : "#FF6A13"}
              animate={
                prefersReducedMotion
                  ? undefined
                  : { opacity: [0.35, 1, 0.35], scale: [1, 1.25, 1] }
              }
              transition={{
                duration: 3 + (idx % 3),
                repeat: Infinity,
                delay: idx * 0.25,
              }}
            />
          ))}
        </svg>
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 lg:px-8 text-center">
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
          whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              START AN INVESTIGATION
            </span>
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
          </div>

          <h2 className="font-[family-name:var(--font-display)] text-5xl sm:text-6xl lg:text-7xl font-bold uppercase tracking-tight leading-[0.92] text-[#F1EEE6]">
            EVERY TRANSACTION LEAVES A TRAIL.
            <br />
            <span className="text-[#FF6A13]">MAKE EVERY INVESTIGATION COUNT.</span>
          </h2>

          <p className="text-base sm:text-lg text-[#A6A39A] max-w-2xl mx-auto leading-relaxed">
            Explore blockchain intelligence with a stronger focus on transparency and evidence
            integrity.
          </p>

          <div className="pt-4">
            <Link
              href="/signin"
              className="group inline-flex items-center gap-3 px-8 py-4 bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] font-semibold text-sm tracking-wider uppercase rounded-sm transition-colors"
            >
              <span>Explore CryptoTrace</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
