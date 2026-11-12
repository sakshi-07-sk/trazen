import React from "react";
import Link from "next/link";
import { Shield } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-[#080909] text-[#A6A39A] pt-16 pb-10 border-t border-white/10 font-[family-name:var(--font-archivo)] overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-14 border-b border-white/10">
          {/* Brand */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-sm bg-[#151616] border border-[#FF6A13]/60 flex items-center justify-center">
                <Shield className="w-4 h-4 text-[#FF6A13]" />
              </div>
              <span className="font-[family-name:var(--font-display)] text-2xl font-bold tracking-wider uppercase text-[#F1EEE6]">
                Crypto<span className="text-[#FF6A13]">Trace</span>
              </span>
            </div>
            <p className="text-sm text-[#A6A39A] max-w-sm leading-relaxed">
              Blockchain intelligence and digital forensics platform engineered for transparent
              transaction tracing, risk detection, and tamper-evident audit logging.
            </p>
          </div>

          {/* Platform */}
          <div className="md:col-span-2 space-y-3">
            <h3 className="font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-[0.18em] text-[#F1EEE6]">
              Platform
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <a href="#solutions" className="hover:text-[#FF6A13] transition-colors">
                  Transaction Intelligence
                </a>
              </li>
              <li>
                <a href="#solutions" className="hover:text-[#FF6A13] transition-colors">
                  Address Analysis
                </a>
              </li>
              <li>
                <a href="#solutions" className="hover:text-[#FF6A13] transition-colors">
                  Graph Integrity
                </a>
              </li>
              <li>
                <a href="#solutions" className="hover:text-[#FF6A13] transition-colors">
                  Evidence Auditing
                </a>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div className="md:col-span-2 space-y-3">
            <h3 className="font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-[0.18em] text-[#F1EEE6]">
              Company
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <a href="#about" className="hover:text-[#FF6A13] transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="#technology" className="hover:text-[#FF6A13] transition-colors">
                  Technology
                </a>
              </li>
              <li>
                <a href="#use-cases" className="hover:text-[#FF6A13] transition-colors">
                  Use Cases
                </a>
              </li>
              <li>
                <a href="#contact" className="hover:text-[#FF6A13] transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div className="md:col-span-3 space-y-3">
            <h3 className="font-[family-name:var(--font-jetbrains)] text-[11px] uppercase tracking-[0.18em] text-[#F1EEE6]">
              Resources
            </h3>
            <ul className="space-y-2.5 text-sm">
              <li>
                <Link href="/dashboard" className="hover:text-[#FF6A13] transition-colors">
                  Investigation Workspace
                </Link>
              </li>
              <li>
                <a href="#technology" className="hover:text-[#FF6A13] transition-colors">
                  Architecture Overview
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/sakshi-07-sk/trazen"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-[#FF6A13] transition-colors"
                >
                  GitHub Repository
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Copyright & Large Wordmark */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#77746D] font-[family-name:var(--font-jetbrains)]">
          <span>CRYPTOTRACE // BLOCKCHAIN FORENSICS &amp; DIGITAL EVIDENCE</span>
          <span>ALL RECORDED EVENTS SUBJECT TO INTEGRITY VERIFICATION</span>
        </div>

        <div
          className="mt-8 select-none text-center font-[family-name:var(--font-display)] font-bold uppercase tracking-[0.04em] leading-none text-[#151616] text-[14vw] sm:text-[11vw] lg:text-[138px]"
          aria-hidden="true"
        >
          CRYPTOTRACE
        </div>
      </div>
    </footer>
  );
}
