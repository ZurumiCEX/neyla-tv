import type { Config } from "tailwindcss";

// Charte mono-couleur : tout le vert primaire (emerald) est remappé sur la
// couleur de marque #5D1C6A et ses teintes. Les classes existantes
// (emerald-300/400/500, hover, etc.) deviennent donc automatiquement violettes.
const brand = {
  50: "#f7eef9",
  100: "#eddcf0",
  200: "#d8b8de",
  300: "#c08fcc", // texte/liens clairs sur fond sombre
  400: "#9b4dab", // accents, hover clair
  500: "#5D1C6A", // couleur de marque
  600: "#4d1659",
  700: "#3d1147",
  800: "#2d0d35",
  900: "#1f0925",
};

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Marque unique #5D1C6A (et ses teintes) sur toute la plateforme.
        emerald: brand,
        brand,
        secondary: {
          DEFAULT: "#5D1C6A",
          light: "#9b4dab",
        },
      },
    },
  },
  plugins: [],
};

export default config;
