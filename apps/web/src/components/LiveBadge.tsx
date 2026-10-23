"use client";

import { useT } from "@/lib/i18n";
import { useLiveStatus } from "@/lib/use-live-status";

export function LiveBadge({ slug, initial }: { slug: string; initial: { is_live: boolean } }) {
  const t = useT();
  const { isLive } = useLiveStatus(slug, initial.is_live);

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
        isLive ? "bg-secondary/20 text-secondary-light" : "bg-neutral-800 text-neutral-400"
      }`}
      aria-live="polite"
    >
      <span
        className={`h-2 w-2 rounded-[1px] ${
          isLive ? "animate-pulse bg-secondary" : "bg-neutral-500"
        }`}
      />
      {isLive ? t("live.badge.on") : t("live.badge.off")}
    </span>
  );
}
