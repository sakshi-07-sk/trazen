"use client";

import React, { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ShieldCheck, LockKeyhole, Eye, RotateCcw, AlertTriangle, CheckCircle2 } from "lucide-react";

const SECURITY_PILLARS = [
  {
    title: "Tamper-Evident Audit Records",
    detail: "Investigation events are linked sequentially so unauthorized edits break downstream verification.",
  },
  {
    title: "SHA-256 Hash-Chain Verification",
    detail: "Each recorded entry incorporates the prior digest, helping detect modifications to recorded data.",
  },
  {
    title: "Investigation Event Traceability",
    detail: "Actions across wallet lookups, findings, and evidence exports remain chronologically attributed.",
  },
  {
    title: "Access Control & Security Monitoring",
    detail: "Role-based portals separate Admin, Investigator, and Analyst workflows with session validation.",
  },
];

interface SimBlock {
  index: number;
  label: string;
  payload: string;
}

const INITIAL_BLOCKS: SimBlock[] = [
  { index: 1, label: "CASE_OPENED", payload: "case=CT-204 | actor=investigator | target=0x7a9f...3c4e" },
  { index: 2, label: "POISONING_FLAG", payload: "lookalike=0x7a9f...3c4f | similarity=0.94" },
  { index: 3, label: "EVIDENCE_SEALED", payload: "graph_snapshot=4_hops | status=RECORDED" },
];

async function sha256Hex(input: string): Promise<string> {
  if (typeof window !== "undefined" && window.crypto?.subtle) {
    const bytes = new TextEncoder().encode(input);
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  // Fallback deterministic hex preview for environments without WebCrypto
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0").repeat(8);
}

export function SecuritySection() {
  const prefersReducedMotion = useReducedMotion();
  const [blocks, setBlocks] = useState<SimBlock[]>(INITIAL_BLOCKS);
  const [baselineHashes, setBaselineHashes] = useState<string[]>([]);
  const [currentHashes, setCurrentHashes] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    async function computeChain(list: SimBlock[]) {
      let prev = "0000000000000000000000000000000000000000000000000000000000000000";
      const out: string[] = [];
      for (const b of list) {
        prev = await sha256Hex(`${b.index}|${b.label}|${b.payload}|${prev}`);
        out.push(prev);
      }
      return out;
    }

    computeChain(INITIAL_BLOCKS).then((base) => {
      if (active) setBaselineHashes(base);
    });
    computeChain(blocks).then((curr) => {
      if (active) setCurrentHashes(curr);
    });

    return () => {
      active = false;
    };
  }, [blocks]);

  const handlePayloadChange = (idx: number, value: string) => {
    setBlocks((prev) =>
      prev.map((item, i) => (i === idx ? { ...item, payload: value } : item))
    );
  };

  const handleReset = () => {
    setBlocks(INITIAL_BLOCKS);
  };

  const chainIntact =
    baselineHashes.length === currentHashes.length &&
    baselineHashes.every((h, idx) => h === currentHashes[idx]);

  return (
    <section className="relative bg-[#080909] py-24 lg:py-32 border-b border-white/10 font-[family-name:var(--font-archivo)]">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
          {/* Left Explanation */}
          <motion.div
            className="lg:col-span-5 space-y-6"
            initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-3">
              <span className="h-[1px] w-8 bg-[#FF6A13]" />
              <span className="font-[family-name:var(--font-jetbrains)] text-xs tracking-[0.22em] uppercase text-[#FF6A13]">
                SECURITY &amp; EVIDENCE INTEGRITY
              </span>
            </div>

            <h2 className="font-[family-name:var(--font-display)] text-4xl sm:text-5xl font-bold uppercase tracking-tight leading-[0.95] text-[#F1EEE6]">
              Detect Changes to <span className="text-[#FF6A13]">Recorded</span> Evidence
            </h2>

            <p className="text-sm sm:text-base text-[#A6A39A] leading-relaxed">
              Cryptographic hash chaining links each recorded audit event to its predecessor.
              While hashing does not prove that external source data was authentic prior to capture,
              it reliably detects any post-recording tampering.
            </p>

            <div className="space-y-4 pt-2">
              {SECURITY_PILLARS.map((pillar) => (
                <div
                  key={pillar.title}
                  className="bg-[#101111] border border-white/10 p-4 rounded-sm flex items-start gap-3.5"
                >
                  <ShieldCheck className="w-4 h-4 text-[#FF6A13] mt-1 shrink-0" />
                  <div>
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-[#F1EEE6]">
                      {pillar.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-[#A6A39A] mt-1 leading-relaxed">
                      {pillar.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right Interactive Hash-Chain Demonstration */}
          <motion.div
            className="lg:col-span-7"
            initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="bg-[#101111] border border-white/10 p-6 sm:p-8 rounded-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-5 mb-6 border-b border-white/10">
                <div>
                  <div className="font-[family-name:var(--font-jetbrains)] text-[10px] tracking-[0.2em] uppercase text-[#FF6A13]">
                    SIMULATED DEMONSTRATION DATA
                  </div>
                  <h3 className="font-[family-name:var(--font-display)] text-2xl font-bold uppercase tracking-wide text-[#F1EEE6] mt-1">
                    Interactive SHA-256 Hash-Chain Verifier
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm border font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-wider ${
                      chainIntact
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                        : "border-[#FF6A13]/60 bg-[#FF6A13]/15 text-[#FF812E]"
                    }`}
                  >
                    {chainIntact ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Chain Verified
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Tamper Detected
                      </>
                    )}
                  </span>

                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#151616] hover:bg-[#1B1C1C] border border-white/10 text-[#F1EEE6] font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-wider rounded-sm transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-[#FF6A13]" />
                    Reset
                  </button>
                </div>
              </div>

              <p className="text-xs text-[#77746D] mb-5 font-[family-name:var(--font-jetbrains)]">
                Edit any simulated event payload below to observe how a single modification
                invalidates the block digest and every subsequent hash in the chain.
              </p>

              <div className="space-y-4">
                {blocks.map((block, idx) => {
                  const curr = currentHashes[idx] ?? "";
                  const base = baselineHashes[idx] ?? "";
                  const matched = curr !== "" && curr === base;
                  const prevHash =
                    idx === 0
                      ? "0000000000000000..."
                      : `${(currentHashes[idx - 1] ?? "").slice(0, 16)}...`;

                  return (
                    <div
                      key={block.index}
                      className={`p-4 rounded-sm border transition-colors ${
                        matched
                          ? "bg-[#151616] border-white/10"
                          : "bg-[#1B1C1C] border-[#FF6A13]/60"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2.5">
                        <div className="flex items-center gap-2 font-[family-name:var(--font-jetbrains)] text-xs">
                          <LockKeyhole
                            className={`w-3.5 h-3.5 ${
                              matched ? "text-[#A6A39A]" : "text-[#FF6A13]"
                            }`}
                          />
                          <span className="text-[#F1EEE6]">
                            EVENT #0{block.index} {"//"} {block.label}
                          </span>
                        </div>
                        <span
                          className={`font-[family-name:var(--font-jetbrains)] text-[10px] uppercase tracking-wider ${
                            matched ? "text-[#77746D]" : "text-[#FF6A13]"
                          }`}
                        >
                          {matched ? "UNMODIFIED" : "HASH MISMATCH"}
                        </span>
                      </div>

                      <label className="block">
                        <span className="sr-only">Payload for event {block.index}</span>
                        <input
                          type="text"
                          value={block.payload}
                          onChange={(e) => handlePayloadChange(idx, e.target.value)}
                          className="w-full bg-[#080909] border border-white/10 focus:border-[#FF6A13] focus:outline-none px-3 py-2 rounded-sm font-[family-name:var(--font-jetbrains)] text-xs text-[#F1EEE6]"
                        />
                      </label>

                      <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 font-[family-name:var(--font-jetbrains)] text-[10px] text-[#77746D]">
                        <div className="truncate">PREV: {prevHash}</div>
                        <div className={`truncate ${matched ? "text-[#A6A39A]" : "text-[#FF812E]"}`}>
                          SHA-256: {curr ? `${curr.slice(0, 24)}...` : "computing..."}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-5 pt-4 border-t border-white/10 flex items-center gap-2 text-xs text-[#A6A39A]">
                <Eye className="w-4 h-4 text-[#FF6A13] shrink-0" />
                <span>
                  Note: SHA-256 hash chaining verifies record integrity after capture; it does not
                  independently certify the truthfulness of unverified external inputs.
                </span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
