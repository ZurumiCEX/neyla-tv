"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

/** Suivi des acquis des tutoriels (persisté côté serveur si connecté). */
export function useGuideProgress() {
  const { user, loading, authFetch } = useAuth();
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      setCompleted(new Set());
      setReady(true);
      return;
    }
    authFetch<{ completed: string[] }>("/api/guides/progress")
      .then((d) => setCompleted(new Set(d.completed)))
      .catch(() => setCompleted(new Set()))
      .finally(() => setReady(true));
  }, [user, loading, authFetch]);

  const toggle = useCallback(
    async (key: string, done: boolean) => {
      // Optimiste.
      setCompleted((prev) => {
        const next = new Set(prev);
        if (done) next.add(key);
        else next.delete(key);
        return next;
      });
      try {
        await authFetch("/api/guides/progress", {
          method: "POST",
          body: JSON.stringify({ key, done }),
        });
      } catch {
        // rollback
        setCompleted((prev) => {
          const next = new Set(prev);
          if (done) next.delete(key);
          else next.add(key);
          return next;
        });
      }
    },
    [authFetch],
  );

  return { completed, toggle, ready, isAuthed: !!user };
}
