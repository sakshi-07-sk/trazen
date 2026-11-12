"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const STAGES = [
  {
    step: "01",
    title: "COLLECT",
    description: "Gather blockchain data and evidence.",
  },
  {
    step: "02",
    title: "ANALYSE",
    description: "Build transaction graphs and examine relationships.",
  },
  {
    step: "03",
    title: "DETECT",
    description: "Identify suspicious activity and potential attack indicators.",
  },
  {
    step: "04",
    title: "VERIFY",
    description: "Verify evidence integrity using cryptographic techniques.",
  },
];

export function WorkflowSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section className="relative bg-[#080909] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          className="max-w-2xl mb-16 space-y-4"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3">
            <span className="h-[1px] w-8 bg-[#FF6A13]" />
            <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
              HOW IT WORKS
            </span>
          </div>
          <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl lg:text-6xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
            Four-Stage Forensic <span className="text-[#FF6A13]">Workflow</span>
          </h2>
        </motion.div>

        {/* Horizontal Desktop / Vertical Mobile Timeline */}
        <div className="relative">
          {/* Desktop horizontal connecting line */}
          <div
            className="hidden lg:block absolute top-9 left-9 right-9 h-[1px] bg-white/10"
            aria-hidden="true"
          />

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 lg:gap-6 relative">
            {STAGES.map((stage, idx) => (
              <motion.div
                key={stage.step}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
                whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: idx * 0.08 }}
                className="relative flex lg:flex-col gap-5 lg:gap-6"
              >
                {/* Vertical mobile connector */}
                {idx < STAGES.length - 1 && (
                  <div
                    className="lg:hidden absolute left-9 top-20 bottom-[-2rem] w-[1px] bg-white/15"
                    aria-hidden="true"
                  />
                )}

                {/* Numbered Circle + Desktop Arrow */}
                <div className="relative flex items-center justify-between shrink-0">
                  <div className="relative z-10 w-[72px] h-[72px] rounded-full bg-[#151616] border-2 border-[#FF6A13] flex items-center justify-center shadow-none">
                    <span className="font-[family-name:var(--font-display)] text-3xl font-bold text-[#FF6A13]">
                      {stage.step}
                    </span>
                  </div>

                  {idx < STAGES.length - 1 && (
                    <motion.div
                      className="hidden lg:flex items-center justify-center flex-1 px-3"
                      animate={
                        prefersReducedMotion
                          ? undefined
                          : { x: [0, 5, 0], opacity: [0.6, 1, 0.6] }
                      }
                      transition={{
                        duration: 2.2,
                        repeat: Infinity,
                        delay: idx * 0.35,
                        ease: "easeInOut",
                      }}
                    >
                      <div className="h-[1px] flex-1 bg-[#FF6A13]/60" />
                      <ArrowRight className="w-4 h-4 text-[#FF6A13] ml-1 shrink-0" />
                    </motion.div>
                  )}
                </div>

                {/* Stage Card */}
                <div className="bg-[#101111] border border-white/10 p-6 rounded-sm flex-1">
                  <div className="font-[family-name:var(--font-jetbrains)] text-[11px] tracking-[0.18em] uppercase text-[#FF6A13] mb-2">
                    {stage.step} — {stage.title}
                  </div>
                  <h3 className="font-[family-name:var(--font-display)] text-2xl font-bold uppercase tracking-wide text-[#F1EEE6] mb-2">
                    {stage.title}
                  </h3>
                  <p className="text-sm text-[#A6A39A] leading-relaxed">
                    {stage.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
