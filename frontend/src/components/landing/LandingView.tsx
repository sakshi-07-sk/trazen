"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRight,
  Radar,
  ShieldCheck,
  Network,
  Gauge,
  Bot,
  Layers,
  Terminal,
  GitBranch,
  Lock,
  Search,
  FileText,
  Menu,
  X,
} from "lucide-react";
import { HeroGraph3D } from "./HeroGraph3D";

gsap.registerPlugin(ScrollTrigger);

const FEATURES = [
  {
    title: "Wallet Tracking",
    tag: "BITCOIN & ETHEREUM",
    description:
      "Monitor suspect seed addresses across UTXO and EVM account ledgers with normalized inflow/outflow accounting.",
    icon: Search,
  },
  {
    title: "Multi-Hop Analysis",
    tag: "1–3+ HOP TRAVERSAL",
    description:
      "Expand transaction graphs recursively across intermediate hops while preserving confirmed vs. inferred edge provenance.",
    icon: Network,
  },
  {
    title: "Risk Detection",
    tag: "4D SCORING ENGINE",
    description:
      "Detect peel chains, mixer fan-in/fan-out, rapid dormant drains, and structuring with confidence caps on mixer ambiguity.",
    icon: Gauge,
  },
  {
    title: "Wallet Clustering",
    tag: "CIOH + COINJOIN GUARD",
    description:
      "Group co-spending addresses using Common-Input Ownership Heuristics while filtering collaborative CoinJoin false positives.",
    icon: Layers,
  },
  {
    title: "Evidence Reports",
    tag: "SHA-256 HASH CHAIN",
    description:
      "Seal every finding and graph snapshot into a tamper-evident SHA-256 hash chain ready for PDF, Markdown, and JSON export.",
    icon: FileText,
  },
  {
    title: "AI-Powered Insights",
    tag: "TRACEAI COPILOT",
    description:
      "Query an evidence-grounded forensic assistant that explains multi-hop paths and cites exact finding and evidence IDs.",
    icon: Bot,
  },
];

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Input Wallet",
    detail: "Submit a Bitcoin or Ethereum address or transaction hash with hop depth.",
  },
  {
    step: "02",
    title: "Trace Transactions",
    detail: "Assemble multi-hop fund flows and UTXO/ERC-20 relationships.",
  },
  {
    step: "03",
    title: "Detect Threats",
    detail: "Run deterministic peel-chain, mixer, clustering, and 4D risk detectors.",
  },
  {
    step: "04",
    title: "Generate Evidence",
    detail: "Verify SHA-256 hash chains and export courtroom-ready dossiers.",
  },
];

const DEMO_STATS = [
  { label: "DEMO WALLETS INDEXED", value: "[ 14,820 ]", detail: "Simulated multi-chain entities" },
  { label: "BENCHMARK SCENARIOS", value: "[ 11 ]", detail: "Peel chains, mixers & CoinJoin" },
  { label: "BEHAVIORAL FEATURES", value: "[ 17 ]", detail: "Deterministic wallet telemetry vectors" },
  { label: "AUTOMATED CHECKS", value: "[ 68 ]", detail: "Backend, forensic & UI test suite" },
];

export function LandingView() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReduced) return;

    const lenis = new Lenis({
      duration: 1.1,
      smoothWheel: true,
    });

    lenis.on("scroll", ScrollTrigger.update);

    const tick = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);

    const ctx = gsap.context(() => {
      gsap.from(".hero-stagger", {
        y: 24,
        opacity: 0,
        duration: 0.75,
        stagger: 0.1,
        ease: "power3.out",
      });

      gsap.utils.toArray<HTMLElement>(".reveal-card").forEach((card) => {
        gsap.from(card, {
          y: 28,
          opacity: 0,
          duration: 0.65,
          ease: "power2.out",
          scrollTrigger: {
            trigger: card,
            start: "top 86%",
            once: true,
          },
        });
      });
    }, rootRef);

    return () => {
      ctx.revert();
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, []);

  return (
    <div
      id="home"
      ref={rootRef}
      className="min-h-screen bg-[#000000] text-[#F5F7FA] selection:bg-[#00E5FF]/30"
    >
      {/* 1. Navbar */}
      <header className="fixed top-0 inset-x-0 z-50 h-16 bg-[#000000]/80 backdrop-blur-md border-b border-white/[0.08]">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-[#00E5FF]/10 border border-[#00E5FF]/40 flex items-center justify-center shadow-[0_0_14px_rgba(0,229,255,0.2)]">
              <Radar className="w-4 h-4 text-[#00E5FF]" />
            </div>
            <span className="text-sm font-semibold tracking-[0.2em] uppercase">
              CryptoTrace
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-xs font-mono uppercase tracking-[0.16em] text-[#8A929E]">
            <a href="#home" className="hover:text-[#00E5FF] transition-colors">
              Home
            </a>
            <a href="#features" className="hover:text-[#00E5FF] transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-[#00E5FF] transition-colors">
              How It Works
            </a>
            <a href="#about" className="hover:text-[#00E5FF] transition-colors">
              About
            </a>
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/signin"
              className="px-4 py-2 rounded border border-white/[0.14] text-xs font-mono uppercase tracking-wider text-[#F5F7FA] hover:border-[#00E5FF]/60 hover:text-[#00E5FF] transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase tracking-wider hover:bg-[#33ECFF] transition-colors shadow-[0_0_24px_rgba(0,229,255,0.28)]"
            >
              Start Investigation
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((v) => !v)}
            className="md:hidden p-2 rounded border border-white/[0.1] text-[#F5F7FA]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Mobile Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#07090C] border-b border-white/[0.08] px-6 py-4 space-y-3 text-xs font-mono uppercase">
            <a
              href="#home"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1 text-[#8A929E] hover:text-[#00E5FF]"
            >
              Home
            </a>
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1 text-[#8A929E] hover:text-[#00E5FF]"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1 text-[#8A929E] hover:text-[#00E5FF]"
            >
              How It Works
            </a>
            <a
              href="#about"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-1 text-[#8A929E] hover:text-[#00E5FF]"
            >
              About
            </a>
            <div className="pt-2 flex gap-2">
              <Link
                href="/signin"
                className="flex-1 text-center py-2 rounded border border-white/[0.15] text-[#F5F7FA]"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="flex-1 text-center py-2 rounded bg-[#00E5FF] text-[#000000] font-semibold"
              >
                Sign Up
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* 2 & 3 & 4. Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 overflow-hidden bg-[#000000]">
        <HeroGraph3D />
        <div className="absolute inset-0 bg-gradient-to-b from-black/45 via-transparent to-[#07090C] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_45%,rgba(0,0,0,0.82),transparent_62%)] pointer-events-none" />

        {/* Floating Technical HUD Labels */}
        <div className="hidden lg:block absolute top-28 right-12 px-3 py-2 rounded bg-[#0E1217]/85 border border-white/[0.1] backdrop-blur-md font-mono text-[11px] text-[#8A929E]">
          <span className="text-[#00E5FF]">TRACE_NODE</span> 0x742d...b800
          <span className="ml-3 text-[#00FF9D]">[ 87 / 100 ]</span>
        </div>
        <div className="hidden lg:block absolute bottom-24 right-16 px-3 py-2 rounded bg-[#0E1217]/85 border border-white/[0.1] backdrop-blur-md font-mono text-[11px] text-[#8A929E]">
          RBAC: <span className="text-[#00FF9D]">ADMIN · INVESTIGATOR · ANALYST</span>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 w-full">
          <div className="max-w-3xl">
            <div className="hero-stagger inline-flex items-center gap-2 px-3 py-1 rounded bg-[#0E1217]/90 border border-[#00FF9D]/30 text-[11px] font-mono uppercase tracking-[0.2em] text-[#00FF9D] mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00FF9D] animate-pulse" />
              Enterprise Blockchain Forensics & Threat Intelligence
            </div>

            <h1 className="hero-stagger text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[0.98] text-[#F5F7FA]">
              Follow the Money.
              <br />
              <span className="text-[#00E5FF]">Uncover the Truth.</span>
            </h1>

            <p className="hero-stagger mt-6 text-base sm:text-lg text-[#8A929E] max-w-2xl leading-relaxed">
              Trace multi-hop Bitcoin UTXO and Ethereum ERC-20 transaction flows, detect
              peel-chain and mixer obfuscation, rank probable end receivers, and seal
              tamper-evident SHA-256 forensic evidence.
            </p>

            <div className="hero-stagger mt-9 flex flex-wrap items-center gap-4">
              <Link
                href="/signin"
                className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase tracking-[0.16em] hover:bg-[#33ECFF] transition-all shadow-[0_0_32px_rgba(0,229,255,0.35)]"
              >
                Start Investigation
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded bg-[#0E1217]/85 border border-[#00FF9D]/35 text-xs font-mono uppercase tracking-[0.16em] text-[#00FF9D] hover:bg-[#00FF9D]/10 transition-colors"
              >
                <Terminal className="w-4 h-4" />
                Explore Platform
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Features Grid */}
      <section id="features" className="bg-[#07090C] py-24 border-t border-white/[0.08]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-14 max-w-2xl">
            <p className="text-[11px] font-mono uppercase tracking-[0.22em] text-[#00E5FF]">
              CORE FORENSIC CAPABILITIES
            </p>
            <h2 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight text-[#F5F7FA]">
              Six deterministic intelligence modules built for cybercrime units.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <article
                  key={feat.title}
                  className="reveal-card rounded border border-white/[0.08] bg-[#0E1217]/80 backdrop-blur-md p-6 hover:border-[#00E5FF]/40 transition-colors"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded bg-[#00E5FF]/10 border border-[#00E5FF]/30 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-[#00E5FF]" />
                    </div>
                    <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#00FF9D]">
                      {feat.tag}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-[#F5F7FA]">{feat.title}</h3>
                  <p className="mt-2 text-sm text-[#8A929E] leading-relaxed">
                    {feat.description}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* 6. How It Works */}
      <section id="how-it-works" className="bg-[#000000] py-24 border-t border-white/[0.08]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-14 max-w-2xl">
            <p className="text-[11px] font-mono uppercase tracking-[0.22em] text-[#00FF9D]">
              INVESTIGATION WORKFLOW
            </p>
            <h2 className="mt-3 text-3xl sm:text-4xl font-semibold text-[#F5F7FA]">
              From raw seed address to verified forensic dossier.
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {WORKFLOW_STEPS.map((item) => (
              <div
                key={item.step}
                className="reveal-card rounded border border-white/[0.08] bg-[#0E1217] p-6 relative"
              >
                <span className="text-xs font-mono text-[#00E5FF]">
                  STEP [ {item.step} ]
                </span>
                <h3 className="mt-3 text-lg font-semibold text-[#F5F7FA]">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-[#8A929E] leading-relaxed">
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 7. Statistics Section (Clearly Labelled Demo Data) */}
      <section className="bg-[#07090C] py-24 border-t border-white/[0.08]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-12">
            <div>
              <p className="text-[11px] font-mono uppercase tracking-[0.22em] text-[#00E5FF]">
                PLATFORM TELEMETRY (DEMO BENCHMARKS)
              </p>
              <h2 className="mt-2 text-3xl font-semibold text-[#F5F7FA]">
                Validated against adversarial blockchain topologies.
              </h2>
            </div>
            <span className="px-3 py-1 rounded bg-[#0E1217] border border-[#00FF9D]/30 text-[11px] font-mono text-[#00FF9D]">
              SIMULATED + TEST SUITE METRICS
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {DEMO_STATS.map((stat) => (
              <div
                key={stat.label}
                className="reveal-card rounded border border-white/[0.08] bg-[#0E1217] p-6"
              >
                <p className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#8A929E]">
                  {stat.label}
                </p>
                <p className="mt-3 text-3xl sm:text-4xl font-mono font-bold text-[#00E5FF]">
                  {stat.value}
                </p>
                <p className="mt-2 text-xs text-[#8A929E]">{stat.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 8. About / Platform Capabilities & Technology */}
      <section id="about" className="bg-[#000000] py-24 border-t border-white/[0.08]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-12 max-w-2xl">
            <p className="text-[11px] font-mono uppercase tracking-[0.22em] text-[#00E5FF]">
              ARCHITECTURE & ROLE-BASED SECURITY
            </p>
            <h2 className="mt-2 text-3xl font-semibold text-[#F5F7FA]">
              Three dedicated workspaces enforced by server-side RBAC.
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="reveal-card rounded border border-white/[0.08] bg-[#0E1217] p-6">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#00E5FF]">
                <span>ADMIN WORKSPACE</span>
                <Lock className="w-4 h-4" />
              </div>
              <h3 className="mt-3 text-lg font-semibold text-[#F5F7FA]">
                Governance & Audit Control
              </h3>
              <p className="mt-2 text-sm text-[#8A929E]">
                Manage users, assign Investigator & Analyst roles, monitor Role 1/Role 2
                service health, and inspect security audit logs.
              </p>
              <div className="mt-4 pt-4 border-t border-white/[0.08] text-xs font-mono text-[#00FF9D]">
                /admin/dashboard
              </div>
            </div>

            <div className="reveal-card rounded border border-[#00E5FF]/35 bg-[#0E1217] p-6">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#00E5FF]">
                <span>INVESTIGATOR WORKSPACE</span>
                <GitBranch className="w-4 h-4" />
              </div>
              <h3 className="mt-3 text-lg font-semibold text-[#F5F7FA]">
                Tracing & Evidence Vault
              </h3>
              <p className="mt-2 text-sm text-[#8A929E]">
                Launch BTC/ETH traces, inspect Cytoscape graphs, cluster wallets, collect
                SHA-256 evidence, and export reports.
              </p>
              <div className="mt-4 pt-4 border-t border-white/[0.08] text-xs font-mono text-[#00E5FF]">
                /investigator/dashboard
              </div>
            </div>

            <div className="reveal-card rounded border border-white/[0.08] bg-[#0E1217] p-6">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#00FF9D]">
                <span>ANALYST WORKSPACE</span>
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h3 className="mt-3 text-lg font-semibold text-[#F5F7FA]">
                Threat Intel & Risk Scoring
              </h3>
              <p className="mt-2 text-sm text-[#8A929E]">
                Monitor high-risk wallets, evaluate 4D risk gauges, inspect peel-chain and
                mixer patterns, and review alerts.
              </p>
              <div className="mt-4 pt-4 border-t border-white/[0.08] text-xs font-mono text-[#00FF9D]">
                /analyst/dashboard
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 9. Final CTA & Footer */}
      <section className="bg-[#07090C] py-24 border-t border-white/[0.08]">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-[11px] font-mono uppercase tracking-[0.24em] text-[#00FF9D]">
            READY TO TRACE
          </p>
          <h2 className="mt-4 text-3xl sm:text-5xl font-bold tracking-tight text-[#F5F7FA]">
            Access Your Forensic Workspace.
          </h2>
          <p className="mt-4 text-sm sm:text-base text-[#8A929E] max-w-xl mx-auto">
            Sign in with your assigned clearance or create an Investigator or Analyst
            account to begin tracing on-chain activity.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/signin"
              className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase tracking-[0.16em] hover:bg-[#33ECFF] transition-colors"
            >
              Sign In to Platform
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded border border-white/[0.15] text-xs font-mono uppercase tracking-[0.16em] text-[#F5F7FA] hover:border-[#00FF9D]/50 hover:text-[#00FF9D] transition-colors"
            >
              Create Analyst / Investigator Account
            </Link>
          </div>
        </div>
      </section>

      <footer className="bg-[#000000] border-t border-white/[0.08] py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#8A929E]">
          <span>CRYPTOTRACE // BLOCKCHAIN FORENSICS & THREAT INTELLIGENCE</span>
          <div className="flex items-center gap-6">
            <a href="#features" className="hover:text-[#00E5FF]">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-[#00E5FF]">
              How It Works
            </a>
            <Link href="/signin" className="hover:text-[#00E5FF]">
              Sign In
            </Link>
            <Link href="/signup" className="hover:text-[#00FF9D]">
              Sign Up
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
