"use client";

import { useCallback, useEffect, useState } from "react";
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
import { useFormat } from "@/lib/use-format";

export function InboxView() {
  const t = useT();
  const { date, time } = useFormat();
  const { user, loading, authFetch } = useAuth();
  const [items, setItems] = useState<Notif[]>([]);
  const [nextBefore, setNextBefore] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(
    async (before?: number) => {
      setBusy(true);
      try {
        const qs = before ? `?before=${before}` : "";
        const d = await authFetch<NotifPage>(`/api/notifications${qs}`);
        setItems((prev) => (before ? [...prev, ...d.results] : d.results));
        setNextBefore(d.next_before);
        publishNotifs({ unread: d.unread });
      } catch {
        /* ignore */
      } finally {
        setBusy(false);
        setLoaded(true);
      }
    },
    [authFetch],
  );

  useEffect(() => {
    if (loading || !user) return;
    load();
  }, [loading, user, load]);

  // Lues depuis la cloche : on reflète l'état ici.
  useEffect(
    () =>
      onNotifs(({ readIds }) => {
        if (!readIds?.length) return;
        const now = new Date().toISOString();
        setItems((prev) => prev.map((n) => (readIds.includes(n.id) ? { ...n, read_at: now } : n)));
      }),
    [],
  );

  async function markRead(ids: number[]) {
    if (ids.length === 0) return;
    try {
      await authFetch("/api/notifications/read", { method: "POST", body: JSON.stringify({ ids }) });
    } catch {
      return;
    }
    const now = new Date().toISOString();
    setItems((prev) => prev.map((n) => (ids.includes(n.id) ? { ...n, read_at: now } : n)));
    publishNotifs({ readIds: ids, delta: -ids.length });
  }

  /** Tout marquer comme lu côté serveur (pages non chargées comprises), sauf le support. */
  async function markAllRead() {
    try {
      const d = await authFetch<{ unread: number }>("/api/notifications/read", {
        method: "POST",
        body: JSON.stringify({ except: ["support_message"] }),
      });
      const now = new Date().toISOString();
      const ids = items.filter((n) => n.type !== "support_message").map((n) => n.id);
      setItems((prev) =>
        prev.map((n) => (n.type !== "support_message" && !n.read_at ? { ...n, read_at: now } : n)),
      );
      publishNotifs({ readIds: ids, unread: d.unread });
    } catch {
      /* ignore */
    }
  }

  const support = items.filter((n) => n.type === "support_message");
  const others = items.filter((n) => n.type !== "support_message");
  const unreadOthers = others.filter((n) => !n.read_at).map((n) => n.id);
  const when = (iso: string) => `${date(iso, { day: "numeric", month: "short" })} · ${time(iso)}`;

  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-neutral-500">
        {t("inbox.supportSection")}
      </h2>
      {support.length === 0 ? (
        <p className="mb-6 text-sm text-neutral-500">{t("inbox.noMessages")}</p>
      ) : (
        <ul className="mb-8 space-y-3">
          {support.map((n) => (
            <li
              key={n.id}
              className={`rounded-xl border p-4 ${
                n.read_at
                  ? "border-neutral-800 bg-neutral-900/40"
                  : "border-secondary/40 bg-secondary/10"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{String(n.payload.title ?? "")}</p>
                  <p className="mt-1 whitespace-pre-line text-sm text-neutral-300">
                    {String(n.payload.body ?? "")}
                  </p>
                  <p className="mt-2 text-xs text-neutral-500">{when(n.created_at)}</p>
                </div>
                {!n.read_at && (
                  <button
                    type="button"
                    onClick={() => markRead([n.id])}
                    className="shrink-0 text-xs text-secondary-light hover:underline"
                  >
                    {t("inbox.markRead")}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="mb-2 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
          {t("inbox.othersSection")}
        </h2>
        {unreadOthers.length > 0 && (
          <button
            type="button"
            onClick={markAllRead}
            className="text-xs text-secondary-light hover:underline"
          >
            {t("inbox.markAllRead")}
          </button>
        )}
      </div>
      {loaded && others.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("notif.empty")}</p>
      ) : (
        <ul className="divide-y divide-neutral-800 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/40">
          {others.map((n) => {
            const { text, href, icon } = describeNotif(n, t);
            const row = (
              <div className="flex items-start gap-3 px-3 py-2.5 text-sm hover:bg-neutral-800/60">
                <span aria-hidden className="w-6 shrink-0 text-center text-base">
                  {icon}
                </span>
                <div className="min-w-0 flex-1">
                  <p className={n.read_at ? "text-neutral-400" : "font-medium text-neutral-100"}>
                    {text}
                  </p>
                  <p className="text-xs text-neutral-500">{when(n.created_at)}</p>
                </div>
                {!n.read_at && (
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                )}
              </div>
            );
            return (
              <li key={n.id}>
                {href ? (
                  <Link href={href} onClick={() => !n.read_at && markRead([n.id])}>
                    {row}
                  </Link>
                ) : (
                  row
                )}
              </li>
            );
          })}
        </ul>
      )}
      {nextBefore !== null && (
        <button
          type="button"
          disabled={busy}
          onClick={() => load(nextBefore)}
          className="mt-3 w-full rounded-lg border border-neutral-700 py-2 text-sm text-neutral-300 hover:border-emerald-500 disabled:opacity-50"
        >
          {busy ? t("common.loading") : t("inbox.loadMore")}
        </button>
      )}
    </div>
  );
}
