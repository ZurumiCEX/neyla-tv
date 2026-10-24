"use client";

import { useCallback, useEffect, useState } from "react";
import type { LevelProgress } from "@/components/LevelBadge";
import { useAuth } from "@/lib/auth-context";
import { onWalletChanged } from "@/lib/wallet-events";

/** Niveau de l'utilisateur connecté, rafraîchi après chaque dépense (tip, abo, don). */
export function useMyLevel(): LevelProgress | null {
  const { user, loading, authFetch } = useAuth();
  const [data, setData] = useState<LevelProgress | null>(null);

  const refresh = useCallback(() => {
    authFetch<LevelProgress>("/api/users/me/level")
      .then(setData)
      .catch(() => setData(null));
  }, [authFetch]);

  useEffect(() => {
    if (loading || !user) return;
    refresh();
    return onWalletChanged(refresh);
  }, [loading, user, refresh]);

  return data;
}
