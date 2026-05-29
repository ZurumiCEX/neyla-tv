"use client";

import { useT } from "@/lib/i18n";

// Paliers Aura basés sur le solde courant. `min` = solde minimal pour atteindre
// le palier. Couleurs ≈ maquette (gris→violet→teal→ambre→bleu→rose).
export type AuraTier = {
  index: number;
  key: string;
  min: number;
  color: string;
  glow: string;
};

export const AURA_TIERS: AuraTier[] = [
  { index: 0, key: "spark", min: 1, color: "#9ca3af", glow: "rgba(156,163,175,0.5)" },
  { index: 1, key: "glow", min: 10, color: "#a855f7", glow: "rgba(168,85,247,0.5)" },
  { index: 2, key: "radiant", min: 100, color: "#14b8a6", glow: "rgba(20,184,166,0.5)" },
  { index: 3, key: "halo", min: 1000, color: "#f59e0b", glow: "rgba(245,158,11,0.5)" },
  { index: 4, key: "nova", min: 5000, color: "#3b82f6", glow: "rgba(59,130,246,0.5)" },
  { index: 5, key: "supreme", min: 10000, color: "#ec4899", glow: "rgba(236,72,153,0.55)" },
];

/** Renvoie le palier atteint pour un solde, ou null si < premier seuil. */
export function auraTier(balance: number): AuraTier | null {
  let current: AuraTier | null = null;
  for (const tier of AURA_TIERS) {
    if (balance >= tier.min) current = tier;
  }
  return current;
}

/** Prochain palier à atteindre (pour la barre de progression), ou null si max. */
export function nextAuraTier(balance: number): AuraTier | null {
  return AURA_TIERS.find((t) => balance < t.min) ?? null;
}

// Emblèmes par palier (inspirés de la charte). viewBox 48x48, centré en x=24,
// dessiné en `currentColor` (couleur du palier).
function Emblem({ tierKey }: { tierKey: string }) {
  const stroke = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 3,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (tierKey) {
    case "spark":
      return (
        <>
          <polygon points="24,3 28,8 24,13 20,8" fill="currentColor" />
          <path d="M13 17 L24 24 L35 17" {...stroke} />
          <path d="M13 25 L24 32 L35 25" {...stroke} />
          <circle cx="24" cy="41" r="3.2" fill="currentColor" />
        </>
      );
    case "glow":
      return (
        <>
          <polygon points="17,6 31,6 24,15" fill="currentColor" />
          <circle cx="24" cy="22" r="6" {...stroke} />
          <path d="M16 30 H32 L24 43 Z" fill="currentColor" />
        </>
      );
    case "radiant":
      return (
        <>
          <polygon points="24,3 30,9 24,15 18,9" fill="currentColor" />
          <path d="M11 30 A13 13 0 0 1 37 30" {...stroke} />
          <rect x="12" y="34" width="24" height="3.2" rx="1.6" fill="currentColor" />
          <rect x="12" y="40" width="24" height="3.2" rx="1.6" fill="currentColor" />
        </>
      );
    case "halo":
      return (
        <>
          <polygon points="24,3 30,9 24,15 18,9" {...stroke} strokeWidth={2.5} />
          <path d="M13 19 L24 26 L35 19" {...stroke} />
          <path d="M13 27 L24 34 L35 27" {...stroke} />
          <circle cx="24" cy="42" r="3.2" fill="currentColor" />
        </>
      );
    case "nova":
      return (
        <>
          <circle cx="24" cy="9" r="4.5" fill="currentColor" />
          <path d="M13 42 V24 L24 18 L35 24 V42" {...stroke} strokeWidth={4} />
        </>
      );
    case "supreme":
      return (
        <>
          <path d="M12 6 L17 12 L24 5 L31 12 L36 6 L34 18 H14 Z" fill="currentColor" />
          <polygon points="24,22 31,30 24,38 17,30" fill="currentColor" />
          <circle cx="24" cy="43" r="3" fill="currentColor" />
        </>
      );
    default:
      return <polygon points="24,6 30,24 24,42 18,24" fill="currentColor" />;
  }
}

export function AuraBadge({
  tier,
  size = 40,
  locked = false,
}: {
  tier: AuraTier;
  size?: number;
  locked?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden
      style={{
        color: locked ? "#52525b" : tier.color,
        opacity: locked ? 0.55 : 1,
        filter: locked ? undefined : `drop-shadow(0 0 5px ${tier.glow})`,
      }}
    >
      <Emblem tierKey={tier.key} />
    </svg>
  );
}

/** Pastille compacte palier + libellé (réutilisée header wallet / studio). */
export function AuraTierPill({ balance }: { balance: number }) {
  const t = useT();
  const tier = auraTier(balance);
  if (!tier) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-neutral-700 px-2.5 py-1 text-xs text-neutral-400">
        {t("aura.tier.none")}
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold"
      style={{ borderColor: tier.color, color: tier.color }}
    >
      <AuraBadge tier={tier} size={18} />
      {t(`aura.tier.${tier.key}`)}
    </span>
  );
}
