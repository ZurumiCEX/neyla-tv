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
type Tier = { threshold: number; bonus: number; key: string };
type Referral = {
  successful_invites: number;
  aura_earned: number;
  base_reward: number;
  current_tier: string | null;
  next_tier: Tier | null;
  tiers: Tier[];
};
type InvitesResp = { results: Invite[]; successful_invites: number; referral: Referral };

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

  if (loading || !user || !data)
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const ref = data.referral;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-1 text-2xl font-bold">{t("ref.title")}</h1>
      <p className="mb-6 text-sm text-neutral-400">{t("ref.subtitle")}</p>

      <div className="mb-4 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-neutral-500">{t("ref.invited")}</p>
          <p className="mt-1 text-2xl font-bold">{ref.successful_invites}</p>
        </div>
        <div className="rounded-2xl border border-secondary/40 bg-secondary/10 p-4">
          <p className="text-xs uppercase tracking-wider text-neutral-500">{t("ref.earned")}</p>
          <p className="mt-1 text-2xl font-bold text-secondary-light">
            {ref.aura_earned.toLocaleString("fr-FR")} <span className="text-sm">Aura</span>
          </p>
        </div>
      </div>
      <p className="mb-6 text-xs text-neutral-500">{t("ref.perInvite", { n: ref.base_reward })}</p>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">{t("ref.tiers")}</h2>
          {ref.current_tier && (
            <span className="rounded-full bg-secondary/20 px-2.5 py-1 text-xs font-semibold text-secondary-light">
              {t(`ref.tier.${ref.current_tier}`)}
            </span>
          )}
        </div>
        {ref.next_tier && (
          <p className="mb-3 text-xs text-neutral-400">
            {t("ref.nextTier", {
              n: ref.next_tier.threshold - ref.successful_invites,
              tier: t(`ref.tier.${ref.next_tier.key}`),
              bonus: ref.next_tier.bonus,
            })}
          </p>
        )}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {ref.tiers.map((tr) => {
            const reached = ref.successful_invites >= tr.threshold;
            return (
              <div
                key={tr.key}
                className={`rounded-xl border p-3 text-center ${
                  reached
                    ? "border-secondary/50 bg-secondary/10"
                    : "border-neutral-800 bg-neutral-900/40 opacity-70"
                }`}
              >
                <p
                  className={`text-sm font-semibold ${reached ? "text-secondary-light" : "text-neutral-400"}`}
                >
                  {t(`ref.tier.${tr.key}`)}
                </p>
                <p className="text-xs text-neutral-500">{tr.threshold}+</p>
                {tr.bonus > 0 && <p className="mt-1 text-xs text-neutral-400">+{tr.bonus}</p>}
              </div>
            );
          })}
        </div>
      </section>

      <h2 className="mb-3 font-semibold">{t("ref.yourCodes")}</h2>
      <div className="mb-4 flex items-end gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          {t("invite.maxUses")}
          <input
            type="number"
            min={1}
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
            className="w-28 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
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
        {data.results.map((inv) => {
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
      {data.results.length === 0 && (
        <p className="text-sm text-neutral-500">{t("invite.empty")}</p>
      )}
    </main>
  );
}
