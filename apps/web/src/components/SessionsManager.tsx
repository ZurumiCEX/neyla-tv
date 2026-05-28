"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Session = {
  id: number;
  device: string;
  ip: string | null;
  created_at: string;
  last_seen_at: string;
  is_current: boolean;
};

function deviceLabel(ua: string, t: (k: string) => string): string {
  if (!ua) return t("sessions.unknownDevice");
  const browser = /Edg/.test(ua)
    ? "Edge"
    : /Chrome/.test(ua)
      ? "Chrome"
      : /Firefox/.test(ua)
        ? "Firefox"
        : /Safari/.test(ua)
          ? "Safari"
          : t("sessions.unknownDevice");
  const os = /Android/.test(ua)
    ? "Android"
    : /iPhone|iPad|iOS/.test(ua)
      ? "iOS"
      : /Windows/.test(ua)
        ? "Windows"
        : /Mac OS/.test(ua)
          ? "macOS"
          : /Linux/.test(ua)
            ? "Linux"
            : "";
  return os ? `${browser} · ${os}` : browser;
}

export function SessionsManager() {
  const t = useT();
  const { authFetch } = useAuth();
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    authFetch<{ results: Session[] }>("/api/auth/sessions")
      .then((d) => setSessions(d.results))
      .catch(() => setSessions([]));
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  async function revoke(id: number) {
    setBusy(true);
    try {
      await authFetch(`/api/auth/sessions/${id}`, { method: "DELETE" });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function revokeOthers() {
    setBusy(true);
    try {
      await authFetch("/api/auth/sessions/revoke-others", { method: "POST" });
      load();
    } finally {
      setBusy(false);
    }
  }

  if (sessions === null) return null;

  const hasOthers = sessions.some((s) => !s.is_current);

  return (
    <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold">{t("sessions.title")}</h2>
        {hasOthers && (
          <button
            type="button"
            onClick={revokeOthers}
            disabled={busy}
            className="rounded-lg border border-red-500/40 px-3 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
          >
            {t("sessions.revokeOthers")}
          </button>
        )}
      </div>

      {sessions.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("sessions.none")}</p>
      ) : (
        <ul className="space-y-2">
          {sessions.map((s) => (
            <li
              key={s.id}
              className="flex items-center justify-between rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-3 py-2.5 text-sm"
            >
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-medium text-neutral-100">
                  {deviceLabel(s.device, t)}
                  {s.is_current && (
                    <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">
                      {t("sessions.current")}
                    </span>
                  )}
                </p>
                <p className="text-xs text-neutral-500">
                  {s.ip ?? "—"} ·{" "}
                  {t("sessions.lastSeen", {
                    date: new Date(s.last_seen_at).toLocaleString("fr-FR", {
                      day: "2-digit",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    }),
                  })}
                </p>
              </div>
              {!s.is_current && (
                <button
                  type="button"
                  onClick={() => revoke(s.id)}
                  disabled={busy}
                  className="shrink-0 rounded-lg border border-neutral-700 px-3 py-1.5 text-xs text-neutral-300 hover:border-red-500/50 hover:text-red-300 disabled:opacity-50"
                >
                  {t("sessions.revoke")}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
