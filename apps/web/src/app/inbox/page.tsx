"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Notif = {
  id: number;
  type: string;
  payload: Record<string, string>;
  read_at: string | null;
  created_at: string;
};

export default function InboxPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [items, setItems] = useState<Notif[]>([]);

  const load = useCallback(async () => {
    try {
      const d = await authFetch<{ results: Notif[] }>("/api/notifications");
      setItems(d.results);
    } catch {
      /* ignore */
    }
  }, [authFetch]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  async function markRead(id: number) {
    await authFetch(`/api/notifications/${id}/read`, { method: "POST" });
    setItems((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)),
    );
  }

  if (loading || !user) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const support = items.filter((n) => n.type === "support_message");
  const others = items.filter((n) => n.type !== "support_message");

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("inbox.title")}</h1>

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
                n.read_at ? "border-neutral-800 bg-neutral-900/40" : "border-fuchsia-500/40 bg-fuchsia-500/5"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{n.payload.title}</p>
                  <p className="mt-1 whitespace-pre-line text-sm text-neutral-300">
                    {n.payload.body}
                  </p>
                </div>
                {!n.read_at && (
                  <button
                    type="button"
                    onClick={() => markRead(n.id)}
                    className="shrink-0 text-xs text-fuchsia-300 hover:underline"
                  >
                    {t("inbox.markRead")}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-neutral-500">
        {t("inbox.othersSection")}
      </h2>
      <ul className="space-y-2">
        {others.map((n) => (
          <li key={n.id} className="rounded-lg border border-neutral-800 bg-neutral-900/40 p-3 text-sm text-neutral-300">
            {n.type} · {new Date(n.created_at).toLocaleString("fr-FR")}
          </li>
        ))}
      </ul>
    </main>
  );
}
