"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

type GuideProgressState = {
  completed: Set<string>;
  toggle: (key: string, done: boolean) => Promise<void>;
  ready: boolean;
  isAuthed: boolean;
};

const GuideProgressContext = createContext<GuideProgressState | null>(null);

/**
 * Source UNIQUE de la progression des tutoriels, partagée par toute l'app
 * (menu d'en-tête + pages). Évite que l'icône reste à 0 % alors que des étapes
 * viennent d'être validées sur une autre vue.
 */
export function GuideProgressProvider({ children }: { children: React.ReactNode }) {
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

  return (
    <GuideProgressContext.Provider value={{ completed, toggle, ready, isAuthed: !!user }}>
      {children}
    </GuideProgressContext.Provider>
  );
}

/** Suivi des acquis des tutoriels (état partagé via le provider). */
export function useGuideProgress(): GuideProgressState {
  const ctx = useContext(GuideProgressContext);
  if (!ctx) {
    throw new Error("useGuideProgress doit être utilisé sous <GuideProgressProvider>");
  }
  return ctx;
}
