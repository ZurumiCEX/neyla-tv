"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type CollabUser = { username: string; display_name: string; avatar_url: string };
type Collab = { id: number; status: string; direction: string; user: CollabUser };
type Data = { active: Collab[]; incoming: Collab[]; outgoing: Collab[] };

function Avatar({ u }: { u: CollabUser }) {
  if (u.avatar_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={u.avatar_url} alt="" className="h-8 w-8 rounded-full object-cover" />;
  }
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-800 text-sm text-neutral-300">
      {(u.display_name || u.username).charAt(0).toUpperCase()}
    </span>
  );
}

export function CollaborationManager() {
  const t = useT();
  const { authFetch } = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    authFetch<Data>("/api/collaborations")
      .then(setData)
      .catch(() => setData({ active: [], incoming: [], outgoing: [] }));
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  async function invite() {
    if (!username.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/collaborations", {
        method: "POST",
        body: JSON.stringify({ username: username.trim() }),
      });
      setUsername("");
      load();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("collab.inviteError"));
    } finally {
      setBusy(false);
    }
  }

  async function respond(id: number, action: "accept" | "decline") {
    setBusy(true);
    try {
      await authFetch(`/api/collaborations/${id}`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    setBusy(true);
    try {
      await authFetch(`/api/collaborations/${id}`, { method: "DELETE" });
      load();
    } finally {
      setBusy(false);
    }
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <h2 className="mb-1 font-semibold">{t("collab.invite")}</h2>
        <p className="mb-3 text-xs text-neutral-400">{t("collab.inviteDesc")}</p>
        <div className="flex gap-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && invite()}
            placeholder={t("collab.invitePlaceholder")}
            className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          />
          <button
            type="button"
            onClick={invite}
            disabled={busy || !username.trim()}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {t("collab.send")}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-300">{error}</p>}
      </section>

      {data.incoming.length > 0 && (
        <CollabList title={t("collab.incoming")}>
          {data.incoming.map((c) => (
            <Row key={c.id} c={c}>
              <button
                type="button"
                onClick={() => respond(c.id, "accept")}
                disabled={busy}
                className="rounded-lg bg-emerald-500 px-3 py-1 text-xs font-semibold text-neutral-950 hover:bg-emerald-400"
              >
                {t("collab.accept")}
              </button>
              <button
                type="button"
                onClick={() => respond(c.id, "decline")}
                disabled={busy}
                className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-red-500/50 hover:text-red-300"
              >
                {t("collab.decline")}
              </button>
            </Row>
          ))}
        </CollabList>
      )}

      <CollabList title={t("collab.active")} empty={t("collab.empty")} items={data.active}>
        {data.active.map((c) => (
          <Row key={c.id} c={c}>
            <button
              type="button"
              onClick={() => remove(c.id)}
              disabled={busy}
              className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-red-500/50 hover:text-red-300"
            >
              {t("collab.remove")}
            </button>
          </Row>
        ))}
      </CollabList>

      {data.outgoing.length > 0 && (
        <CollabList title={t("collab.outgoing")}>
          {data.outgoing.map((c) => (
            <Row key={c.id} c={c}>
              <span className="text-xs text-amber-300">{t("collab.pending")}</span>
              <button
                type="button"
                onClick={() => remove(c.id)}
                disabled={busy}
                className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-red-500/50 hover:text-red-300"
              >
                {t("collab.cancel")}
              </button>
            </Row>
          ))}
        </CollabList>
      )}
    </div>
  );
}

function CollabList({
  title,
  empty,
  items,
  children,
}: {
  title: string;
  empty?: string;
  items?: unknown[];
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
      <h2 className="mb-3 font-semibold">{title}</h2>
      {empty && items && items.length === 0 ? (
        <p className="text-sm text-neutral-500">{empty}</p>
      ) : (
        <ul className="space-y-2">{children}</ul>
      )}
    </section>
  );
}

function Row({ c, children }: { c: Collab; children: React.ReactNode }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-3 py-2">
      <span className="flex min-w-0 items-center gap-2">
        <Avatar u={c.user} />
        <span className="min-w-0">
          <span className="block truncate text-sm text-neutral-100">{c.user.display_name}</span>
          <span className="block truncate text-xs text-neutral-500">@{c.user.username}</span>
        </span>
      </span>
      <span className="flex shrink-0 items-center gap-2">{children}</span>
    </li>
  );
}
