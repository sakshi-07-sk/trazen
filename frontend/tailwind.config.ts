import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/context/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cyber: {
          void: "#000000",
          bg: "#080909",
          surface: "#151616",
          card: "#151616",
          "card-hover": "#1B1C1C",
          border: "rgba(255,255,255,0.1)",
          "border-light": "rgba(255,255,255,0.18)",
          primary: "#FF6A13",
          "primary-dim": "rgba(255, 106, 19, 0.12)",
          "primary-glow": "rgba(255, 106, 19, 0.18)",
          cyan: "#FF6A13",
          text: "#F1EEE6",
          muted: "#A6A39A",
          emerald: "#22C55E",
          amber: "#F59E0B",
          orange: "#FF6A13",
          rose: "#EF4444",
        },
      },
      fontFamily: {
        sans: ["var(--font-archivo)", "var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: [
          "var(--font-jetbrains)",
          "var(--font-geist-mono)",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        glow: "0 0 28px -6px rgba(255, 106, 19, 0.28)",
        "glow-sm": "0 0 14px -4px rgba(255, 106, 19, 0.24)",
        "glow-rose": "0 0 20px -5px rgba(239, 68, 68, 0.25)",
        "glow-emerald": "0 0 20px -5px rgba(34, 197, 94, 0.25)",
      },
    },
  },
  plugins: [],
};
export default config;
