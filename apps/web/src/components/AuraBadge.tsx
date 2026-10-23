"use client";

import { useT } from "@/lib/i18n";

// Paliers Aura basés sur le solde courant. `min` = solde minimal pour atteindre
// le palier. Chaque emblème a une face claire (`light`) et une face sombre
// (`dark`) pour l'effet facetté de la charte AURA BADGES.
export type AuraTier = {
  index: number;
  key: string;
  min: number;
  /** Couleur principale (texte, bordures). */
  color: string;
  light: string;
  dark: string;
  glow: string;
};

export const AURA_TIERS: AuraTier[] = [
  {
    index: 0,
    key: "spark",
    min: 1,
    color: "#a3a3a3",
    light: "#b5b5b5",
    dark: "#6b6b6b",
    glow: "rgba(163,163,163,0.45)",
  },
  {
    index: 1,
    key: "glow",
    min: 100,
    color: "#a259f0",
    light: "#a259f0",
    dark: "#7c2fd6",
    glow: "rgba(162,89,240,0.5)",
  },
  {
    index: 2,
    key: "radiant",
    min: 1000,
    color: "#0ccab5",
    light: "#0ccab5",
    dark: "#00a896",
    glow: "rgba(12,202,181,0.5)",
  },
  {
    index: 3,
    key: "nova",
    min: 5000,
    color: "#1f7bf2",
    light: "#7ab0ff",
    dark: "#0a47c2",
    glow: "rgba(31,123,242,0.55)",
  },
  {
    index: 4,
    key: "supreme",
    min: 10000,
    color: "#ff5c45",
    light: "#ff5c45",
    dark: "#f03018",
    glow: "rgba(240,48,24,0.55)",
  },
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

const ROT5 = [0, 72, 144, 216, 288];
const ROT8 = [0, 45, 90, 135, 180, 225, 270, 315];
const ROT12 = Array.from({ length: 12 }, (_, i) => i * 30);

// Emblèmes facettés, viewBox 48x48 centré en (24, 24). Les classes `aura-*`
// portent les animations en boucle (globals.css).
function Emblem({ tier }: { tier: AuraTier }) {
  const { light: L, dark: D } = tier;
  switch (tier.key) {
    case "spark":
      // Chevrons empilés.
      return (
        <g className="aura-float">
          {[5, 17, 29].map((y, i) => (
            <g key={y} opacity={1 - i * 0.12}>
              <polygon points={`5,${y + 11} 24,${y} 24,${y + 7} 5,${y + 18}`} fill={L} />
              <polygon points={`43,${y + 11} 24,${y} 24,${y + 7} 43,${y + 18}`} fill={D} />
            </g>
          ))}
        </g>
      );
    case "glow":
      // Grappe de 4 losanges.
      return (
        <g>
          {[
            [24, 11],
            [11, 24],
            [37, 24],
            [24, 37],
          ].map(([cx, cy], i) => (
            <g
              key={i}
              className="aura-breathe"
              style={{ animationDelay: `${i * 0.35}s` } as React.CSSProperties}
            >
              <polygon points={`${cx},${cy - 10} ${cx},${cy + 10} ${cx - 10},${cy}`} fill={L} />
              <polygon points={`${cx},${cy - 10} ${cx},${cy + 10} ${cx + 10},${cy}`} fill={D} />
            </g>
          ))}
        </g>
      );
    case "radiant":
      // Moulinet pentagonal.
      return (
        <g className="aura-spin-slow">
          {ROT5.map((r) => (
            <g key={r} transform={`rotate(${r} 24 24)`}>
              <polygon points="24,24 24,2 36,12" fill={L} />
              <polygon points="24,24 36,12 33,24" fill={D} />
            </g>
          ))}
          <circle cx="24" cy="24" r="3" fill={D} />
        </g>
      );
    case "nova":
      // Étoile géométrique à 8 branches.
      return (
        <g className="aura-shimmer">
          {ROT8.map((r, i) => {
            const len = i % 2 === 0 ? 23 : 15;
            return (
              <g key={r} transform={`rotate(${r} 24 24)`}>
                <polygon points={`24,24 24,${24 - len} 20,20`} fill={i % 2 ? tier.color : L} />
                <polygon points={`24,24 24,${24 - len} 28,20`} fill={D} />
              </g>
            );
          })}
        </g>
      );
    case "supreme":
      // Losange central + rayons (soleil).
      return (
        <>
          <g className="aura-rays">
            {ROT12.map((r, i) => (
              <polygon
                key={r}
                transform={`rotate(${r} 24 24)`}
                points={i % 2 ? "22.5,9 25.5,9 24,1.5" : "22,10 26,10 24,0.5"}
                fill={i % 2 ? D : L}
              />
            ))}
          </g>
          <g className="aura-breathe">
            <polygon points="24,10 24,24 14,24" fill={L} />
            <polygon points="24,10 24,24 34,24" fill={D} />
            <polygon points="24,38 24,24 14,24" fill={D} />
            <polygon points="24,38 24,24 34,24" fill={L} />
          </g>
        </>
      );
    default:
      return <polygon points="24,6 30,24 24,42 18,24" fill={L} />;
  }
}

export function AuraBadge({
  tier,
  size = 40,
  locked = false,
  animated = true,
}: {
  tier: AuraTier;
  size?: number;
  locked?: boolean;
  /** Animation en boucle (désactivée dans les listes denses). */
  animated?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden
      className={`aura-badge shrink-0 ${animated && !locked ? "aura-animated" : ""}`}
      style={{
        filter: locked ? "grayscale(1)" : `drop-shadow(0 0 ${size > 30 ? 6 : 3}px ${tier.glow})`,
        opacity: locked ? 0.35 : 1,
      }}
    >
      <Emblem tier={tier} />
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
