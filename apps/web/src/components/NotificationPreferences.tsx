"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

const TYPES = [
  "live_started",
  "new_follower",
  "application_decided",
  "subscription",
  "tip_received",
  "achievement",
  "support_message",
];

export function NotificationPreferences() {
  const t = useT();
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
      setMessage(t("settings.notifSaved"));
    } catch {
      setMessage(t("settings.notifError"));
      load();
    }
  }

  if (!prefs) return null;

  return (
    <section className="mt-6 space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <h2 className="text-lg font-bold">{t("settings.notifTitle")}</h2>
      <p className="text-xs text-neutral-500">{t("settings.notifDesc")}</p>
      {TYPES.map((type) => (
        <label key={type} className="flex items-center justify-between gap-3 text-sm">
          <span className="text-neutral-300">{t(`notif.${type}`)}</span>
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
