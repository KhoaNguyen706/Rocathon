import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm off-white canvas, inspired by the Moss landing page.
        canvas: {
          DEFAULT: "#f4f2ec",
          soft: "#ebe8e0",
          card: "#ffffff",
        },
        ink: {
          950: "#0b0b0b",
          900: "#121212",
          800: "#1e1e1e",
          700: "#3a3a3a",
          500: "#6b6b6b",
          400: "#8a8a8a",
          300: "#b3b1aa",
          200: "#d6d3cb",
          100: "#e7e4dc",
        },
        accent: {
          pink: "#f5b5ea",
          lime: "#d3f26a",
          green: "#22c55e",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-sans)",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        serif: [
          "var(--font-serif)",
          "Instrument Serif",
          "Cormorant Garamond",
          "Georgia",
          "ui-serif",
          "serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(17,17,17,0.04), 0 8px 24px -12px rgba(17,17,17,0.12)",
        card: "0 1px 0 rgba(17,17,17,0.04), 0 10px 40px -20px rgba(17,17,17,0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
