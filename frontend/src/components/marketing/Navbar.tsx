"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, Shield, X } from "lucide-react";

const NAV_LINKS = [
  { id: "home", label: "Home", href: "#home" },
  { id: "about", label: "About", href: "#about" },
  { id: "solutions", label: "Solutions", href: "#solutions" },
  { id: "technology", label: "Technology", href: "#technology" },
  { id: "use-cases", label: "Use Cases", href: "#use-cases" },
  { id: "contact", label: "Contact", href: "#contact" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [activeId, setActiveId] = useState("home");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 24);
      const offsets = NAV_LINKS.map((item) => {
        const el = document.getElementById(item.id);
        if (!el) return { id: item.id, top: Infinity };
        return { id: item.id, top: Math.abs(el.getBoundingClientRect().top - 120) };
      });
      offsets.sort((a, b) => a.top - b.top);
      if (offsets[0]) setActiveId(offsets[0].id);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-colors duration-200 ${
        scrolled
          ? "bg-[#080909]/95 backdrop-blur-md border-b border-white/10"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto h-16 px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Left: Brand */}
        <Link
          href="#home"
          className="flex items-center gap-2.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#FF6A13] rounded"
        >
          <span className="w-8 h-8 rounded bg-[#151616] border border-[#FF6A13]/50 flex items-center justify-center">
            <Shield className="w-4 h-4 text-[#FF6A13]" aria-hidden="true" />
          </span>
          <span
            className="text-xl font-bold tracking-[0.12em] uppercase text-[#F1EEE6]"
            style={{ fontFamily: "var(--font-display), sans-serif" }}
          >
            CryptoTrace
          </span>
        </Link>

        {/* Center: Section Links */}
        <nav aria-label="Primary Navigation" className="hidden lg:flex items-center gap-7">
          {NAV_LINKS.map((item) => {
            const isActive = activeId === item.id;
            return (
              <a
                key={item.id}
                href={item.href}
                className={`group relative py-1 text-xs uppercase tracking-[0.16em] transition-colors focus:outline-none focus-visible:text-[#FF6A13] ${
                  isActive ? "text-[#F1EEE6]" : "text-[#A6A39A] hover:text-[#F1EEE6]"
                }`}
                style={{ fontFamily: "var(--font-jetbrains), monospace" }}
              >
                {item.label}
                <span
                  className={`absolute left-0 -bottom-0.5 h-[2px] bg-[#FF6A13] transition-all duration-200 ${
                    isActive ? "w-full" : "w-0 group-hover:w-full"
                  }`}
                />
              </a>
            );
          })}
        </nav>

        {/* Right: System Online + Run Demo */}
        <div className="hidden md:flex items-center gap-4">
          <div
            className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-[#A6A39A]"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            <span className="w-2 h-2 rounded-full bg-[#22C55E]" aria-hidden="true" />
            <span>System Online</span>
          </div>

          <Link
            href="/signin"
            className="px-3.5 py-2 rounded-sm border border-white/15 text-xs uppercase tracking-[0.12em] text-[#F1EEE6] hover:border-[#FF6A13] hover:text-[#FF6A13] transition-colors"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            Sign In
          </Link>

          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-sm bg-[#FF6A13] hover:bg-[#FF812E] text-[#080909] text-xs font-semibold uppercase tracking-[0.14em] transition-colors"
            style={{ fontFamily: "var(--font-jetbrains), monospace" }}
          >
            Run Demo
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          type="button"
          onClick={() => setMobileOpen((v) => !v)}
          className="lg:hidden p-2 rounded-sm border border-white/15 text-[#F1EEE6]"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="lg:hidden bg-[#101111] border-b border-white/10 px-6 py-5 space-y-3">
          {NAV_LINKS.map((item) => (
            <a
              key={item.id}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className="block py-1.5 text-xs uppercase tracking-[0.16em] text-[#A6A39A] hover:text-[#FF6A13]"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              {item.label}
            </a>
          ))}
          <div className="pt-3 border-t border-white/10 flex flex-wrap items-center gap-3">
            <div
              className="flex items-center gap-2 text-[11px] uppercase text-[#A6A39A]"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
              <span>System Online</span>
            </div>
            <Link
              href="/signin"
              onClick={() => setMobileOpen(false)}
              className="px-3.5 py-2 rounded-sm border border-white/15 text-xs uppercase text-[#F1EEE6]"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              Sign In
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMobileOpen(false)}
              className="px-4 py-2 rounded-sm bg-[#FF6A13] text-[#080909] text-xs font-semibold uppercase"
              style={{ fontFamily: "var(--font-jetbrains), monospace" }}
            >
              Run Demo
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
