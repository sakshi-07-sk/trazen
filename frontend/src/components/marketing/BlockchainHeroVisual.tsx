"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Lock, Shield } from "lucide-react";

const FLOATING_LABELS = [
  { text: "Detect Fraudulent Activity", pos: "top-4 left-2 sm:left-4" },
  { text: "Analyse Transactions", pos: "top-6 right-2 sm:right-4" },
  { text: "Verify Evidence", pos: "bottom-12 left-2 sm:left-6" },
  { text: "Build Trust", pos: "bottom-6 right-2 sm:right-6" },
];

export function BlockchainHeroVisual() {
  const prefersReduced = useReducedMotion();

  return (
    <div
      className="relative w-full max-w-[540px] mx-auto aspect-square rounded-sm border border-white/10 bg-[#101111] overflow-hidden p-4 sm:p-6 flex items-center justify-center"
      aria-label="Blockchain security shield and transaction network diagram"
    >
      {/* Subtle architectural grid */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.08) 1px, transparent 1px)",
          backgroundSize: "36px 36px",
        }}
      />

      {/* SVG Network Pathways & Blockchain Cubes */}
      <svg
        viewBox="0 0 420 420"
        className="w-full h-full relative z-10"
        role="img"
        aria-label="Connected blockchain nodes and orange forensic trace pathways"
      >
        {/* Outer ring */}
        <circle
          cx="210"
          cy="210"
          r="146"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeDasharray="4 6"
        />
        <circle
          cx="210"
          cy="210"
          r="98"
          fill="none"
          stroke="rgba(255,106,19,0.28)"
          strokeWidth="1.2"
        />

        {/* Orange Transaction Pathways */}
        <g stroke="#FF6A13" strokeWidth="1.75" fill="none" strokeLinecap="round">
          <path d="M84 112 L152 162 L210 210" />
          <path d="M336 112 L268 162 L210 210" />
          <path d="M84 308 L152 258 L210 210" />
          <path d="M336 308 L268 258 L210 210" />
          <path d="M210 64 L210 132" strokeDasharray="3 4" />
          <path d="M210 288 L210 356" strokeDasharray="3 4" />
        </g>

        {/* Animated pulse along pathways */}
        {!prefersReduced && (
          <g fill="#FF812E">
            <circle r="3.5">
              <animateMotion dur="3.4s" repeatCount="indefinite" path="M84 112 L152 162 L210 210" />
            </circle>
            <circle r="3.5">
              <animateMotion dur="3.8s" repeatCount="indefinite" path="M336 308 L268 258 L210 210" />
            </circle>
            <circle r="3.5">
              <animateMotion dur="4.2s" repeatCount="indefinite" path="M336 112 L268 162 L210 210" />
            </circle>
          </g>
        )}

        {/* Blockchain Cube Nodes */}
        {[
          { x: 64, y: 92, label: "BLK-01" },
          { x: 316, y: 92, label: "BLK-02" },
          { x: 64, y: 288, label: "UTXO" },
          { x: 316, y: 288, label: "ERC20" },
        ].map((cube) => (
          <g key={cube.label} transform={`translate(${cube.x}, ${cube.y})`}>
            <rect
              width="40"
              height="40"
              rx="2"
              fill="#151616"
              stroke="rgba(255,255,255,0.18)"
            />
            <rect
              x="6"
              y="6"
              width="28"
              height="28"
              rx="1"
              fill="none"
              stroke="#FF6A13"
              strokeOpacity="0.6"
            />
            <text
              x="20"
              y="24"
              textAnchor="middle"
              fill="#F1EEE6"
              fontSize="8"
              fontFamily="monospace"
            >
              {cube.label}
            </text>
          </g>
        ))}

        {/* Top & Bottom Anchor Nodes */}
        <circle cx="210" cy="64" r="6" fill="#151616" stroke="#FF6A13" strokeWidth="2" />
        <circle cx="210" cy="356" r="6" fill="#151616" stroke="#FF6A13" strokeWidth="2" />
      </svg>

      {/* Central Security Shield + Lock */}
      <motion.div
        initial={prefersReduced ? false : { scale: 0.94, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="absolute z-20 w-24 h-24 rounded-sm bg-[#151616] border border-[#FF6A13] flex flex-col items-center justify-center shadow-2xl"
      >
        <div className="relative flex items-center justify-center">
          <Shield className="w-10 h-10 text-[#FF6A13]" aria-hidden="true" />
          <Lock className="w-4 h-4 text-[#F1EEE6] absolute" aria-hidden="true" />
        </div>
        <span
          className="mt-1.5 text-[9px] uppercase tracking-[0.18em] text-[#A6A39A]"
          style={{ fontFamily: "var(--font-jetbrains), monospace" }}
        >
          SHA-256 LOCK
        </span>
      </motion.div>

      {/* Floating Technical Labels */}
      {FLOATING_LABELS.map((item, idx) => (
        <motion.div
          key={item.text}
          initial={prefersReduced ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: prefersReduced ? 0 : 0.15 + idx * 0.1 }}
          className={`absolute z-30 ${item.pos} px-2.5 py-1.5 rounded-sm bg-[#1B1C1C]/95 border border-white/15 text-[10px] sm:text-[11px] text-[#F1EEE6] flex items-center gap-2`}
          style={{ fontFamily: "var(--font-jetbrains), monospace" }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#FF6A13]" aria-hidden="true" />
          <span>{item.text}</span>
        </motion.div>
      ))}
    </div>
  );
}
