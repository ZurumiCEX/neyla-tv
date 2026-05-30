import type { DonationTier } from "@/lib/donation-tiers";
import { DONATION_TIERS } from "@/lib/donation-tiers";

/**
 * Emblème d'un palier de donation : étoile rayonnante dont l'intensité (nombre
 * de rayons + halo) croît avec le palier. Dessinée en couleur du palier.
 */
export function DonationTierBadge({ tier, size = 64 }: { tier: DonationTier; size?: number }) {
  const idx = DONATION_TIERS.findIndex((t) => t.key === tier.key);
  const rays = 5 + idx; // 5 → 11 rayons selon le palier
  const cx = 32;
  const cy = 32;
  const points: string[] = [];
  const outer = 22;
  const inner = 9 + idx; // cœur plus brillant aux paliers élevés
  for (let i = 0; i < rays * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (Math.PI / rays) * i - Math.PI / 2;
    points.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`);
  }
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      aria-hidden
      style={{ filter: `drop-shadow(0 0 ${6 + idx * 2}px ${tier.glow})` }}
    >
      <circle cx={cx} cy={cy} r="30" fill={tier.color} opacity={0.12} />
      <polygon points={points.join(" ")} fill={tier.color} />
      <circle cx={cx} cy={cy} r={3 + idx * 0.6} fill="#fff" opacity={0.9} />
    </svg>
  );
}
