// Paliers de DONATION (basés sur le montant d'Aura d'un tip), affichés sur
// l'écran de stream (overlay). Distincts des paliers de solde (AuraBadge).
//
// Étincelle 1–20 000 · Lueur 20 001–40 000 · Radiance 40 001–70 000 ·
// Halo 70 001–100 000 · Nova 100 001–150 000 · Supernova 150 001–230 000 ·
// Aurore 230 001+

export type DonationTier = {
  key: string;
  name: string; // libellé de marque (FR)
  min: number;
  max: number | null; // borne incluse ; null = illimité
  color: string;
  glow: string;
};

export const DONATION_TIERS: DonationTier[] = [
  {
    key: "spark",
    name: "Étincelle",
    min: 1,
    max: 20000,
    color: "#FFC81E",
    glow: "rgba(255,200,30,0.55)",
  },
  {
    key: "glow",
    name: "Lueur",
    min: 20001,
    max: 40000,
    color: "#a855f7",
    glow: "rgba(168,85,247,0.55)",
  },
  {
    key: "radiance",
    name: "Radiance",
    min: 40001,
    max: 70000,
    color: "#14b8a6",
    glow: "rgba(20,184,166,0.55)",
  },
  {
    key: "halo",
    name: "Halo",
    min: 70001,
    max: 100000,
    color: "#f59e0b",
    glow: "rgba(245,158,11,0.55)",
  },
  {
    key: "nova",
    name: "Nova",
    min: 100001,
    max: 150000,
    color: "#3b82f6",
    glow: "rgba(59,130,246,0.55)",
  },
  {
    key: "supernova",
    name: "Supernova",
    min: 150001,
    max: 230000,
    color: "#ec4899",
    glow: "rgba(236,72,153,0.55)",
  },
  {
    key: "aurore",
    name: "Aurore",
    min: 230001,
    max: null,
    color: "#22c55e",
    glow: "rgba(34,197,94,0.55)",
  },
];

/** Palier de donation atteint pour un montant d'Aura (null si <= 0). */
export function donationTier(amount: number): DonationTier | null {
  if (!amount || amount < 1) return null;
  let current: DonationTier | null = null;
  for (const tier of DONATION_TIERS) {
    if (amount >= tier.min) current = tier;
  }
  return current;
}
