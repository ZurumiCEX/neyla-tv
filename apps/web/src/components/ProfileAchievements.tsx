"use client";

import { AchievementIcon, type AchievementItem } from "@/components/AchievementIcon";
import { achText } from "@/lib/achievements";
import { useT } from "@/lib/i18n";

/** Rangée des succès obtenus, affichée sur un profil/chaîne (sans casser le design). */
export function ProfileAchievements({
  items,
  max = 10,
}: {
  items: AchievementItem[];
  max?: number;
}) {
  const t = useT();
  if (!items || items.length === 0) return null;
  const shown = items.slice(0, max);
  const extra = items.length - shown.length;
  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5">
      {shown.map((a) => (
        <span
          key={a.key}
          title={achText(t, a).name}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-800 bg-neutral-900/70"
        >
          <AchievementIcon achievement={a} size={20} />
        </span>
      ))}
      {extra > 0 && (
        <span className="flex h-8 items-center rounded-lg border border-neutral-800 bg-neutral-900/70 px-2 text-xs text-neutral-400">
          +{extra}
        </span>
      )}
    </div>
  );
}

/** Avatar + pastille du nombre de succès (coin haut-droit). */
export function AvatarBadge({ count, children }: { count: number; children: React.ReactNode }) {
  const t = useT();
  return (
    <span className="relative inline-flex shrink-0">
      {children}
      {count > 0 && (
        <span
          title={t("ach.count", { n: count })}
          className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-neutral-950 bg-emerald-500 px-1 text-[10px] font-bold leading-none text-neutral-950"
        >
          {count > 99 ? "99+" : count}
        </span>
      )}
    </span>
  );
}
