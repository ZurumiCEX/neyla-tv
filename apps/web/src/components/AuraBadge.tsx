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

export function AuraBadge({
  tier,
  size = 40,
  locked = false,
}: {
  tier: AuraTier;
  size?: number;
  locked?: boolean;
}) {
  const color = locked ? "#52525b" : tier.color;
  const id = `aura-grad-${tier.key}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden
      style={locked ? undefined : { filter: `drop-shadow(0 0 6px ${tier.glow})` }}
    >
      <defs>
        <radialGradient id={id} cx="50%" cy="40%" r="65%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity={locked ? 0.15 : 0.9} />
          <stop offset="55%" stopColor={color} />
          <stop offset="100%" stopColor={color} stopOpacity="0.7" />
        </radialGradient>
      </defs>
      {/* Étoile Aura à 4 branches, taille du halo croissante avec le palier. */}
      <path
        d="M24 3l4.6 12.8L41 20l-12.4 4.2L24 37l-4.6-12.8L7 20l12.4-4.2L24 3z"
        fill={`url(#${id})`}
        stroke={color}
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* Couronne de points = niveau du palier. */}
      {!locked &&
        Array.from({ length: tier.index + 1 }).map((_, i) => {
          const angle = (i / (tier.index + 1)) * Math.PI * 2 - Math.PI / 2;
          const cx = 24 + Math.cos(angle) * 19;
          const cy = 24 + Math.sin(angle) * 19;
          return <circle key={i} cx={cx} cy={cy} r="1.6" fill={color} />;
        })}
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
