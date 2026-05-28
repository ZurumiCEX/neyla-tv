"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { CopyButton } from "@/components/CopyButton";

type Invite = {
  code: string;
  max_uses: number;
  used_count: number;
  is_usable: boolean;
  created_at: string;
};

type InvitesResp = { results: Invite[]; successful_invites: number };

export default function InvitePage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [data, setData] = useState<InvitesResp | null>(null);
  const [maxUses, setMaxUses] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [origin, setOrigin] = useState("");

  const load = useCallback(async () => {
    try {
      setData(await authFetch<InvitesResp>("/api/invites"));
    } catch {
      setError(t("common.loadError"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    setOrigin(window.location.origin);
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  async function create() {
    setError(null);
    try {
      await authFetch("/api/invites", {
        method: "POST",
        body: JSON.stringify({ max_uses: Number(maxUses) || 1 }),
      });
      load();
    } catch {
      setError(t("invite.createError"));
    }
  }

  if (loading || !user) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-2 text-2xl font-bold">{t("invite.title")}</h1>
      <p className="mb-6 text-sm text-neutral-400">
        {t("invite.subtitle", { count: data?.successful_invites ?? 0 })}
      </p>

      <div className="mb-6 flex items-end gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          {t("invite.maxUses")}
          <input
            type="number"
            min={1}
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
            className="w-28 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          />
        </label>
        <button
          type="button"
          onClick={create}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
        >
          {t("invite.generate")}
        </button>
      </div>

      {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

      <ul className="space-y-3">
        {data?.results.map((inv) => {
          const link = `${origin}/register?invite=${inv.code}`;
          return (
            <li
              key={inv.code}
              className="flex items-center justify-between gap-3 rounded-xl border border-neutral-800 bg-neutral-900/40 p-3"
            >
              <div>
                <p className="font-mono text-lg font-bold tracking-wider">{inv.code}</p>
                <p className="text-xs text-neutral-500">
                  {t("invite.used", { used: inv.used_count, max: inv.max_uses })} ·{" "}
                  {inv.is_usable ? t("invite.active") : t("invite.exhausted")}
                </p>
              </div>
              <CopyButton value={link} />
            </li>
          );
        })}
      </ul>
      {data && data.results.length === 0 && (
        <p className="text-sm text-neutral-500">{t("invite.empty")}</p>
      )}
    </main>
  );
}
