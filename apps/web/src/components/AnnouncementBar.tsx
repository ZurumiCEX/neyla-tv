"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type Announcement = {
  id: number;
  title: string;
  body: string;
  level: "info" | "success" | "warning" | "critical";
  display_mode: "ticker" | "popup" | "both";
  dismissible: boolean;
  cta_label: string;
  cta_url: string;
};

const LEVEL_STYLES: Record<Announcement["level"], string> = {
  info: "bg-blue-900/40 border-b-blue-700/50 text-blue-100",
  success: "bg-emerald-900/40 border-b-emerald-700/50 text-emerald-100",
  warning: "bg-amber-900/40 border-b-amber-700/50 text-amber-100",
  critical: "bg-red-900/50 border-b-red-700/60 text-red-100",
};

/**
 * Bandeau d'annonces (ticker + popup) sous le header.
 *
 * - `display_mode=ticker|both` → ligne défilante.
 * - `display_mode=popup|both`  → modale une fois par utilisateur (localStorage).
 * - Filtrage audience (anonyme/viewer/streamer) géré côté API.
 */
export function AnnouncementBar() {
  const t = useT();
  const [items, setItems] = useState<Announcement[]>([]);
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());
  const [popupItem, setPopupItem] = useState<Announcement | null>(null);

  useEffect(() => {
    apiFetch<{ results: Announcement[] }>("/api/announcements/active")
      .then((d) => setItems(d.results))
      .catch(() => setItems([]));
  }, []);

  useEffect(() => {
    // Première popup non vue.
    const popup = items.find(
      (a) =>
        (a.display_mode === "popup" || a.display_mode === "both") &&
        !readDismissed(`ann:${a.id}:popup`),
    );
    setPopupItem(popup ?? null);
  }, [items]);

  function dismiss(id: number) {
    setDismissed((s) => new Set(s).add(id));
    try {
      localStorage.setItem(`ann:${id}:dismissed`, "1");
    } catch {
      /* ignore */
    }
  }

  function dismissPopup() {
    if (!popupItem) return;
    try {
      localStorage.setItem(`ann:${popupItem.id}:popup`, "1");
    } catch {
      /* ignore */
    }
    setPopupItem(null);
  }

  // Tickers visibles
  const tickers = items.filter(
    (a) =>
      (a.display_mode === "ticker" || a.display_mode === "both") &&
      !dismissed.has(a.id) &&
      !readDismissed(`ann:${a.id}:dismissed`),
  );

  return (
    <>
      {tickers.map((a) => (
        <div
          key={a.id}
          role="status"
          className={`flex items-center gap-3 border-b px-4 py-2 text-xs font-medium ${LEVEL_STYLES[a.level]}`}
        >
          <span className="flex-1 truncate">
            <span className="font-bold uppercase tracking-wider opacity-80">
              {a.level === "critical" ? "⚠" : a.level === "warning" ? "⚠" : a.level === "success" ? "✓" : "ℹ"}{" "}
              {a.title}
            </span>
            {a.body && <span className="ml-2 opacity-90">— {a.body}</span>}
          </span>
          {a.cta_url && (
            <a
              href={a.cta_url}
              className="shrink-0 rounded bg-white/20 px-2 py-0.5 font-bold uppercase tracking-wider hover:bg-white/30"
            >
              {a.cta_label || "Voir"}
            </a>
          )}
          {a.dismissible && (
            <button
              type="button"
              onClick={() => dismiss(a.id)}
              aria-label={t("ann.dismiss")}
              className="shrink-0 rounded p-1 opacity-70 hover:bg-white/10 hover:opacity-100"
            >
              ×
            </button>
          )}
        </div>
      ))}

      {popupItem && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
          onClick={dismissPopup}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-2xl border border-neutral-800 bg-neutral-950 p-6 shadow-2xl"
          >
            <h2 className="mb-2 text-lg font-bold text-neutral-100">{popupItem.title}</h2>
            {popupItem.body && (
              <p className="text-sm text-neutral-300 whitespace-pre-line">{popupItem.body}</p>
            )}
            <div className="mt-5 flex items-center justify-end gap-2">
              {popupItem.cta_url && (
                <a
                  href={popupItem.cta_url}
                  onClick={dismissPopup}
                  className="rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-white hover:bg-secondary-light"
                >
                  {popupItem.cta_label || "Découvrir"}
                </a>
              )}
              <button
                type="button"
                onClick={dismissPopup}
                className="rounded-lg border border-neutral-700 px-4 py-2 text-sm text-neutral-300 hover:border-neutral-500"
              >
                {t("ann.dismiss")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function readDismissed(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}
