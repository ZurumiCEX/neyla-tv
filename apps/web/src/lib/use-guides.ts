"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { getGuides, type Guide } from "@/lib/guides";
import type { Locale } from "@/lib/messages";

/**
 * Guides/tutoriels : récupérés depuis l'API (contenu géré en back-office),
 * avec repli immédiat sur le contenu intégré (`getGuides`) pour un rendu
 * instantané et tolérant aux pannes réseau.
 */
export function useGuides(locale: Locale): Guide[] {
  const [guides, setGuides] = useState<Guide[]>(() => getGuides(locale));

  useEffect(() => {
    let cancelled = false;
    setGuides(getGuides(locale)); // repli pour la nouvelle locale en attendant l'API
    apiFetch<{ results: Guide[] }>(`/api/guides?locale=${locale}`)
      .then((d) => {
        if (!cancelled && d.results && d.results.length > 0) setGuides(d.results);
      })
      .catch(() => {
        /* repli déjà en place */
      });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  return guides;
}
