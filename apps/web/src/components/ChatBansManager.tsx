"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type UserBan = {
  username: string;
  display_name: string;
  until: string | null;
  shadow: boolean;
  reason: string;
};
type IpBan = { ip: string; until: string | null; reason: string };
type Bans = { user_bans: UserBan[]; ip_bans: IpBan[] };

export function ChatBansManager() {
  const t = useT();
  const { authFetch } = useAuth();
  const [bans, setBans] = useState<Bans | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    authFetch<Bans>("/api/c/me/chat-bans")
      .then(setBans)
      .catch(() => setBans({ user_bans: [], ip_bans: [] }));
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  async function liftUser(username: string) {
    setBusy(true);
    try {
      await authFetch(`/api/c/me/chat-bans/user/${encodeURIComponent(username)}`, {
        method: "DELETE",
      });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function liftIp(ip: string) {
    setBusy(true);
    try {
      await authFetch(`/api/c/me/chat-bans/ip/${encodeURIComponent(ip)}`, { method: "DELETE" });
      load();
    } finally {
      setBusy(false);
    }
  }

  if (!bans) return null;
  const empty = bans.user_bans.length === 0 && bans.ip_bans.length === 0;

  function kind(b: UserBan): string {
    if (b.shadow) return t("mod.shadow");
    return b.until ? t("mod.timeout") : t("mod.permanent");
  }

  return (
    <div className="border-t border-neutral-800 pt-6">
      <p className="mb-3 text-xs uppercase tracking-wider text-neutral-500">{t("mod.title")}</p>
      {empty ? (
        <p className="text-sm text-neutral-500">{t("mod.none")}</p>
      ) : (
        <div className="space-y-2">
          {bans.user_bans.map((b) => (
            <div
              key={b.username}
              className="flex items-center justify-between rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-3 py-2 text-sm"
            >
              <span className="min-w-0">
                <span className="font-medium text-neutral-100">{b.display_name}</span>{" "}
                <span className="text-neutral-500">@{b.username}</span>
                <span className="ml-2 rounded-full bg-neutral-800 px-2 py-0.5 text-xs text-neutral-400">
                  {kind(b)}
                </span>
              </span>
              <button
                type="button"
                onClick={() => liftUser(b.username)}
                disabled={busy}
                className="shrink-0 rounded-lg border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-emerald-500 hover:text-emerald-300 disabled:opacity-50"
              >
                {t("mod.lift")}
              </button>
            </div>
          ))}
          {bans.ip_bans.map((b) => (
            <div
              key={b.ip}
              className="flex items-center justify-between rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-3 py-2 text-sm"
            >
              <span>
                <span className="font-mono text-neutral-200">{b.ip}</span>
                <span className="ml-2 rounded-full bg-neutral-800 px-2 py-0.5 text-xs text-neutral-400">
                  {t("mod.ipban")}
                </span>
              </span>
              <button
                type="button"
                onClick={() => liftIp(b.ip)}
                disabled={busy}
                className="shrink-0 rounded-lg border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-emerald-500 hover:text-emerald-300 disabled:opacity-50"
              >
                {t("mod.lift")}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
