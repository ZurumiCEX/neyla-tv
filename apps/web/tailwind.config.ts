import type { Config } from "tailwindcss";

// Charte mono-couleur : la couleur de marque #FFC81E (jaune doré) et ses teintes.
// La palette `emerald` est remappée dessus, donc les classes existantes
// (emerald-300/400/500, hover, gradients) deviennent dorées automatiquement.
// NB : les fonds de marque sont associés à un texte foncé (text-neutral-950).
const brand = {
  50: "#fffaeb",
  100: "#fff1c6",
  200: "#ffe49a",
  300: "#ffd95e", // texte/liens clairs sur fond sombre
  400: "#ffce3a",
  500: "#FFC81E", // couleur de marque
  600: "#e6b000", // hover (plus foncé)
  700: "#b88a00",
  800: "#8a6700",
  900: "#5c4400",
};

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Marque unique #FFC81E (et ses teintes) sur toute la plateforme.
        emerald: brand,
        brand,
        secondary: {
          DEFAULT: "#FFC81E",
          light: "#ffd95e",
        },
      },
    },
  },
  plugins: [],
};

export default config;
