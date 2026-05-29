"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Status = { is_live: boolean; last_live_started_at: string | null };

const POLL_INTERVAL_MS = 5_000;

export function LiveBadge({
  slug,
  initial,
}: {
  slug: string;
  initial: { is_live: boolean };
}) {
  const [isLive, setIsLive] = useState(initial.is_live);

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const data = await apiFetch<Status>(`/api/channels/${slug}/status`);
        if (!cancelled) setIsLive(data.is_live);
      } catch {
        /* tolérant : on garde l'état précédent */
      }
    }

    const id = setInterval(tick, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [slug]);

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
      {isLive ? "En direct" : "Hors-ligne"}
    </span>
  );
}
