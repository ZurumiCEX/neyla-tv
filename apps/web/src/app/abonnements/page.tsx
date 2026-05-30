"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type ChannelInfo = {
  slug: string;
  title: string;
  thumbnail_url: string;
  is_live: boolean;
  streamer: { username: string; display_name: string; avatar_url: string };
  category: { slug: string; name: string } | null;
};

type ActiveSub = {
  channel: ChannelInfo;
  tier_name: string | null;
  status: string;
  current_period_end: string;
  gifted_by: { username: string; display_name: string } | null;
};

type GiftedSub = {
  channel: ChannelInfo;
  tier_name: string | null;
  recipient: { username: string; display_name: string; avatar_url: string };
  status: string;
  current_period_end: string;
  created_at: string;
};

type Tab = "active" | "gifted";

export default function AbonnementsPage() {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [tab, setTab] = useState<Tab>("active");
  const [active, setActive] = useState<ActiveSub[]>([]);
  const [gifted, setGifted] = useState<GiftedSub[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Formulaire cadeau
  const [channelSlug, setChannelSlug] = useState("");
  const [recipient, setRecipient] = useState("");
  const [giftStatus, setGiftStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [giftBusy, setGiftBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    setBusy(true);
    setErr(null);
    Promise.all([
      authFetch<{ results: ActiveSub[] }>("/api/subscriptions/me"),
      authFetch<{ results: GiftedSub[] }>("/api/subscriptions/gifted"),
    ])
      .then(([a, g]) => {
        setActive(a.results);
        setGifted(g.results);
      })
      .catch(() => setErr(t("common.loadError")))
      .finally(() => setBusy(false));
  }, [user, authFetch, t]);

  async function submitGift(e: React.FormEvent) {
    e.preventDefault();
    setGiftBusy(true);
    setGiftStatus(null);
    try {
      await authFetch("/api/subscriptions/gift", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug.trim(), recipient: recipient.trim() }),
      });
      setGiftStatus({ ok: true, msg: t("subs.giftOk") });
      setChannelSlug("");
      setRecipient("");
      // Recharge la liste « offert »
      const g = await authFetch<{ results: GiftedSub[] }>("/api/subscriptions/gifted");
      setGifted(g.results);
    } catch (e) {
      const err = e as { data?: { detail?: string } };
      setGiftStatus({ ok: false, msg: err.data?.detail ?? t("common.loadError") });
    } finally {
      setGiftBusy(false);
    }
  }

  if (!user) {
    return (
      <main className="mx-auto max-w-md p-8 text-neutral-300">
        <p>{t("common.loading")}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">{t("subs.title")}</h1>
        <p className="text-sm text-neutral-400">{t("subs.subtitle")}</p>
      </header>

      <nav className="mb-4 inline-flex rounded-lg border border-neutral-800 bg-neutral-900 p-1">
        {(["active", "gifted"] as Tab[]).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setTab(k)}
            className={`rounded-md px-3 py-1.5 text-sm transition ${
              k === tab
                ? "bg-emerald-500 font-semibold text-neutral-950"
                : "text-neutral-300 hover:text-neutral-100"
            }`}
          >
            {t(`subs.tab.${k}`)}
          </button>
        ))}
      </nav>

      {busy && <p className="text-sm text-neutral-400">{t("common.loading")}</p>}
      {err && <p className="text-sm text-red-300">{err}</p>}

      {tab === "active" && !busy && (
        <section>
          {active.length === 0 ? (
            <p className="text-sm text-neutral-400">{t("subs.active.none")}</p>
          ) : (
            <ul className="space-y-2">
              {active.map((s) => (
                <li
                  key={s.channel.slug}
                  className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 p-4"
                >
                  <div>
                    <Link
                      href={`/c/${s.channel.slug}`}
                      className="font-semibold text-neutral-100 hover:text-secondary-light"
                    >
                      {s.channel.title || `@${s.channel.streamer.username}`}
                    </Link>
                    <p className="text-xs text-neutral-400">
                      @{s.channel.streamer.username}
                      {s.tier_name && <span> · {s.tier_name}</span>}
                    </p>
                    {s.gifted_by && (
                      <p className="mt-0.5 text-xs text-emerald-300">
                        {t("subs.giftBy", { username: s.gifted_by.username })}
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-neutral-400">
                    {t("subs.endsOn", {
                      date: new Date(s.current_period_end).toLocaleDateString(),
                    })}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "gifted" && !busy && (
        <section className="space-y-6">
          <form
            onSubmit={submitGift}
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-4"
          >
            <h2 className="mb-1 text-base font-semibold">{t("subs.giftFormTitle")}</h2>
            <p className="mb-3 text-xs text-neutral-400">{t("subs.giftFormHint")}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="mb-1 block text-sm text-neutral-300">
                  {t("subs.giftFormChannel")}
                </span>
                <input
                  type="text"
                  value={channelSlug}
                  onChange={(e) => setChannelSlug(e.target.value)}
                  required
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-secondary-light"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm text-neutral-300">
                  {t("subs.giftFormRecipient")}
                </span>
                <input
                  type="text"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  required
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-secondary-light"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={giftBusy}
              className="mt-3 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {giftBusy ? "..." : t("subs.giftFormSubmit")}
            </button>
            {giftStatus && (
              <p
                className={`mt-2 text-sm ${
                  giftStatus.ok ? "text-emerald-300" : "text-red-300"
                }`}
              >
                {giftStatus.msg}
              </p>
            )}
          </form>

          {gifted.length === 0 ? (
            <p className="text-sm text-neutral-400">{t("subs.gifted.none")}</p>
          ) : (
            <ul className="space-y-2">
              {gifted.map((s) => (
                <li
                  key={`${s.channel.slug}-${s.recipient.username}-${s.created_at}`}
                  className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 p-4"
                >
                  <div>
                    <p className="font-semibold text-neutral-100">
                      @{s.recipient.username}
                    </p>
                    <p className="text-xs text-neutral-400">
                      {s.channel.title || s.channel.slug} · @{s.channel.streamer.username}
                      {s.tier_name && <span> · {s.tier_name}</span>}
                    </p>
                  </div>
                  <p className="text-xs text-neutral-400">
                    {t("subs.endsOn", {
                      date: new Date(s.current_period_end).toLocaleDateString(),
                    })}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}
