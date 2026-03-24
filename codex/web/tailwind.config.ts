import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f1720",
        sand: "#f6efe2",
        ember: "#d95f3c",
        moss: "#2e5f4d",
        mist: "#dde6e6",
      },
      fontFamily: {
        display: ['"Iowan Old Style"', '"Palatino Linotype"', "serif"],
        body: ['"Avenir Next"', '"Segoe UI"', "sans-serif"],
      },
      boxShadow: {
        panel: "0 18px 50px rgba(15, 23, 32, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

