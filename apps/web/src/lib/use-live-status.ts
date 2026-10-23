"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Status = { is_live: boolean; last_live_started_at: string | null; viewers?: number };

const POLL_INTERVAL_MS = 5_000;

/** Statut live d'une chaîne, rafraîchi toutes les 5 s (endpoint cacheable 5 s). */
export function useLiveStatus(slug: string, initialLive: boolean) {
  const [isLive, setIsLive] = useState(initialLive);
  const [viewers, setViewers] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function tick() {
      try {
        const data = await apiFetch<Status>(`/api/channels/${slug}/status`);
        if (cancelled) return;
        setIsLive(data.is_live);
        if (typeof data.viewers === "number") setViewers(data.viewers);
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

  return { isLive, viewers };
}
