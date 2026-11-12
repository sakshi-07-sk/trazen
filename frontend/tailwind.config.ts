import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#070b12",
          surface: "#0d131f",
          card: "#111827",
          "card-hover": "#172033",
          border: "#1e293b",
          "border-light": "#334155",
          primary: "#3b82f6",
          "primary-glow": "rgba(59, 130, 246, 0.15)",
          violet: "#8b5cf6",
          cyan: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#ef4444",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      boxShadow: {
        glow: "0 0 20px -5px rgba(59, 130, 246, 0.2)",
        "glow-rose": "0 0 20px -5px rgba(239, 68, 68, 0.2)",
        "glow-emerald": "0 0 20px -5px rgba(16, 185, 129, 0.2)",
      },
    },
  },
  plugins: [],
};
export default config;
