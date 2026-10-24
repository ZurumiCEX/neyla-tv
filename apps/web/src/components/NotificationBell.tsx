"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import {
  describeNotif,
  onNotifs,
  publishNotifs,
  type Notif,
  type NotifPage,
} from "@/lib/notifications";

const POLL_MS = 20_000;

export function NotificationBell() {
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [items, setItems] = useState<Notif[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const load = useCallback(async () => {
    try {
      const d = await authFetch<NotifPage>("/api/notifications?limit=15");
      setItems(d.results);
      setUnread(d.unread);
    } catch {
      /* ignore */
    }
  }, [authFetch]);

  // Rafraîchissement périodique, en pause quand l'onglet est caché.
  useEffect(() => {
    if (loading || !user) return;
    load();
    const id = setInterval(() => {
      if (document.visibilityState === "visible") load();
    }, POLL_MS);
    const onVisible = () => document.visibilityState === "visible" && load();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [loading, user, load]);

  // Lecture depuis la boîte de réception : compteur et liste à jour ici aussi.
  useEffect(
    () =>
      onNotifs(({ unread: total, readIds, delta }) => {
        if (typeof total === "number") setUnread(total);
        if (typeof delta === "number") setUnread((u) => Math.max(0, u + delta));
        if (readIds?.length) {
          const now = new Date().toISOString();
          setItems((prev) =>
            prev.map((n) => (readIds.includes(n.id) ? { ...n, read_at: now } : n)),
          );
        }
      }),
    [],
  );

  async function toggle() {
    const next = !open;
    setOpen(next);
    // Ouvrir la cloche marque comme lues les notifications affichées, sauf les
    // messages du support, qui restent à lire dans la boîte de réception.
    const ids = items.filter((n) => !n.read_at && n.type !== "support_message").map((n) => n.id);
    if (!next || ids.length === 0) return;
    try {
      await authFetch("/api/notifications/read", { method: "POST", body: JSON.stringify({ ids }) });
      const now = new Date().toISOString();
      setItems((prev) => prev.map((n) => (ids.includes(n.id) ? { ...n, read_at: now } : n)));
      setUnread((u) => Math.max(0, u - ids.length));
      publishNotifs({ readIds: ids });
    } catch {
      /* ignore */
    }
  }

  if (loading || !user) return null;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={toggle}
        className="relative flex h-8 w-8 items-center justify-center rounded-md text-neutral-300 hover:bg-neutral-900"
        aria-label={t("notif.title")}
      >
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 01-3.4 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-neutral-950">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <p className="border-b border-neutral-800 px-3 py-2 text-xs uppercase tracking-wider text-neutral-500">
            {t("notif.title")}
          </p>
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-neutral-500">{t("notif.empty")}</p>
            ) : (
              items.map((n) => {
                const { text, href, icon } = describeNotif(n, t);
                const body = (
                  <div
                    className={`flex items-start gap-2 px-3 py-2 text-sm ${
                      n.read_at ? "text-neutral-400" : "text-neutral-100"
                    } hover:bg-neutral-800`}
                  >
                    <span aria-hidden className="w-5 shrink-0 text-center">
                      {icon}
                    </span>
                    <span className="min-w-0 flex-1">{text}</span>
                    {!n.read_at && (
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                    )}
                  </div>
                );
                return href ? (
                  <Link key={n.id} href={href} onClick={() => setOpen(false)}>
                    {body}
                  </Link>
                ) : (
                  <div key={n.id}>{body}</div>
                );
              })
            )}
          </div>
          <Link
            href="/inbox"
            onClick={() => setOpen(false)}
            className="block border-t border-neutral-800 px-3 py-2 text-center text-xs font-semibold text-emerald-300 hover:bg-neutral-800"
          >
            {t("notif.seeAll")}
          </Link>
        </div>
      )}
    </div>
  );
}
