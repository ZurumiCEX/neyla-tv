import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Couleur secondaire de la marque (statut LIVE, accents).
        secondary: {
          DEFAULT: "#5D1C6A",
          light: "#8a3a99",
        },
      },
    },
  },
  plugins: [],
};

export default config;
