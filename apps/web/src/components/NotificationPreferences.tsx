"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

const LABELS: Record<string, string> = {
  live_started: "Live d'une chaîne suivie",
  new_follower: "Nouvel abonné (follow)",
  application_decided: "Candidature streamer traitée",
  subscription: "Nouvel abonné payant",
  tip_received: "Tip reçu",
  achievement: "Succès débloqué",
  support_message: "Message du support",
};

export function NotificationPreferences() {
  const { authFetch } = useAuth();
  const [prefs, setPrefs] = useState<Record<string, boolean> | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setPrefs(await authFetch<Record<string, boolean>>("/api/notifications/preferences"));
    } catch {
      /* ignore */
    }
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  async function toggle(type: string, enabled: boolean) {
    setPrefs((p) => (p ? { ...p, [type]: enabled } : p));
    setMessage(null);
    try {
      await authFetch("/api/notifications/preferences", {
        method: "PUT",
        body: JSON.stringify({ [type]: enabled }),
      });
      setMessage("Préférences enregistrées.");
    } catch {
      setMessage("Échec de l'enregistrement.");
      load();
    }
  }

  if (!prefs) return null;

  return (
    <section className="mt-6 space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <h2 className="text-lg font-bold">Notifications</h2>
      <p className="text-xs text-neutral-500">
        Choisis les notifications que tu souhaites recevoir.
      </p>
      {Object.keys(LABELS).map((type) => (
        <label key={type} className="flex items-center justify-between gap-3 text-sm">
          <span className="text-neutral-300">{LABELS[type]}</span>
          <input
            type="checkbox"
            checked={prefs[type] ?? true}
            onChange={(e) => toggle(type, e.target.checked)}
            className="h-4 w-4 accent-emerald-500"
          />
        </label>
      ))}
      {message && <p className="text-xs text-neutral-400">{message}</p>}
    </section>
  );
}
