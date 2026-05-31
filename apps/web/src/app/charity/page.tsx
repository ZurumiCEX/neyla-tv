"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { fmt, fmtAura } from "@/lib/format";

type Charity = {
  slug: string;
  name: string;
  description: string;
  country: string;
  logo_url: string;
  website_url: string;
};

type CharityEvent = {
  slug: string;
  title: string;
  theme: string;
  description_md: string;
  cover_url: string;
  starts_at: string;
  ends_at: string;
  floor_aura: number;
  is_open: boolean;
  beneficiaries: Charity[];
  total_aura_cached: number;
};

type ByCharity = {
  charity__slug: string;
  charity__name: string;
  charity__logo_url: string;
  total: number;
  count: number;
};

type TopDonor = {
  username: string;
  display_name: string;
  is_streamer: boolean;
  aura_amount: number;
  created_at: string;
};

type CurrentResp = {
  event: CharityEvent | null;
  total?: number;
  donor_count?: number;
  by_charity?: ByCharity[];
  top_donors?: TopDonor[];
};

export default function CharityPage() {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [data, setData] = useState<CurrentResp | null>(null);
  const [busy, setBusy] = useState(true);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      setData(await apiFetch<CurrentResp>("/api/charity/events/current"));
    } catch {
      setData({ event: null });
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="w-full p-4 sm:p-6">
      <header className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight">{t("charity.title")}</h1>
        <p className="mt-1 text-sm text-neutral-400">{t("charity.subtitle")}</p>
      </header>

      {busy && <p className="text-neutral-500">{t("common.loading")}</p>}

      {!busy && (!data || !data.event) && (
        <p className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6 text-neutral-300">
          {t("charity.noEvent")}
        </p>
      )}

      {!busy && data?.event && (
        <CharityEventView
          event={data.event}
          total={data.total ?? 0}
          donorCount={data.donor_count ?? 0}
          byCharity={data.by_charity ?? []}
          topDonors={data.top_donors ?? []}
          onDonated={load}
          authFetch={authFetch}
          isAuthed={!!user}
        />
      )}
    </main>
  );
}

function CharityEventView({
  event,
  total,
  donorCount,
  byCharity,
  topDonors,
  onDonated,
  authFetch,
  isAuthed,
}: {
  event: CharityEvent;
  total: number;
  donorCount: number;
  byCharity: ByCharity[];
  topDonors: TopDonor[];
  onDonated: () => void;
  authFetch: ReturnType<typeof useAuth>["authFetch"];
  isAuthed: boolean;
}) {
  const t = useT();
  const dateLabel = useMemo(() => {
    return event.is_open
      ? t("charity.endsOn", { date: new Date(event.ends_at).toLocaleDateString("fr-FR") })
      : t("charity.startsOn", { date: new Date(event.starts_at).toLocaleDateString("fr-FR") });
  }, [event, t]);

  return (
    <>
      {/* Hero événement */}
      <section className="mb-6 overflow-hidden rounded-2xl border border-secondary/30 bg-gradient-to-br from-secondary/15 via-neutral-900 to-emerald-500/10">
        {event.cover_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={event.cover_url}
            alt=""
            className="h-44 w-full object-cover opacity-80"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = "none";
            }}
          />
        )}
        <div className="p-6">
          <p className="text-xs font-bold uppercase tracking-widest text-secondary-light">
            {t("charity.currentTitle")} {event.theme && `· ${event.theme}`}
          </p>
          <h2 className="mt-1 text-2xl font-bold">{event.title}</h2>
          <p className="mt-1 text-sm text-neutral-400">{dateLabel}</p>
          <p className="mt-1 text-xs text-neutral-500">
            {t("charity.floor", { n: fmt(event.floor_aura) })}
          </p>
        </div>
      </section>

      {/* Total + donateurs */}
      <section className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Stat label={t("charity.totalCollected")} value={fmtAura(total)} primary />
        <Stat label={t("charity.donors")} value={fmt(donorCount)} />
      </section>

      <div className="grid gap-6 md:grid-cols-[1fr_360px]">
        {/* Colonne gauche : description, répartition par cause */}
        <div className="space-y-6">
          {event.description_md && (
            <article className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
              <p className="whitespace-pre-line text-sm text-neutral-200">
                {event.description_md}
              </p>
            </article>
          )}

          {byCharity.length > 0 && (
            <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-neutral-400">
                {t("charity.byCharity")}
              </h3>
              <ul className="space-y-3">
                {byCharity.map((c) => {
                  const pct = total > 0 ? Math.round((c.total / total) * 100) : 0;
                  return (
                    <li key={c.charity__slug}>
                      <div className="mb-1 flex items-center gap-2 text-sm">
                        {c.charity__logo_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={c.charity__logo_url}
                            alt=""
                            className="h-6 w-6 rounded object-cover"
                          />
                        ) : (
                          <span className="h-6 w-6 rounded bg-neutral-800" />
                        )}
                        <span className="flex-1 truncate text-neutral-200">{c.charity__name}</span>
                        <span className="font-mono text-neutral-100">{fmtAura(c.total)}</span>
                        <span className="w-10 text-right text-xs text-neutral-500">{pct}%</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-800">
                        <div
                          className="h-full bg-secondary"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          )}

          {/* Leaderboard top donateurs */}
          {topDonors.length > 0 && (
            <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-neutral-400">
                {t("charity.topDonors")}
              </h3>
              <ol className="space-y-2">
                {topDonors.map((d, i) => (
                  <li
                    key={`${d.username}-${i}`}
                    className="flex items-center gap-3 rounded-lg bg-neutral-900/60 px-3 py-2"
                  >
                    <span className="w-5 text-right font-mono text-xs text-neutral-500">
                      {i + 1}
                    </span>
                    <span className="flex-1 truncate text-sm text-neutral-100">
                      {d.display_name}
                      {d.is_streamer && (
                        <span className="ml-2 rounded bg-secondary/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-secondary-light">
                          {t("charity.streamerBadge")}
                        </span>
                      )}
                    </span>
                    <span className="font-mono font-semibold text-emerald-300">
                      {fmtAura(d.aura_amount)}
                    </span>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>

        {/* Colonne droite : formulaire de don */}
        <aside className="space-y-4">
          {isAuthed ? (
            <DonateForm event={event} authFetch={authFetch} onDonated={onDonated} />
          ) : (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
              <p className="text-sm text-neutral-300">
                <Link href="/login" className="font-semibold text-emerald-300 underline">
                  {t("nav.login")}
                </Link>{" "}
                {t("charity.giveCta").toLowerCase()}
              </p>
            </div>
          )}
        </aside>
      </div>
    </>
  );
}

function Stat({ label, value, primary }: { label: string; value: string; primary?: boolean }) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        primary
          ? "border-secondary/40 bg-secondary/10"
          : "border-neutral-800 bg-neutral-900/60"
      }`}
    >
      <p className="text-xs uppercase tracking-wider text-neutral-400">{label}</p>
      <p
        className={`mt-1 text-3xl font-extrabold ${
          primary ? "text-secondary-light" : "text-neutral-100"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function DonateForm({
  event,
  authFetch,
  onDonated,
}: {
  event: CharityEvent;
  authFetch: ReturnType<typeof useAuth>["authFetch"];
  onDonated: () => void;
}) {
  const t = useT();
  const [charity, setCharity] = useState(event.beneficiaries[0]?.slug ?? "");
  const [amount, setAmount] = useState(String(event.floor_aura));
  const [message, setMessage] = useState("");
  const [anonymous, setAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      const n = Number(amount);
      await authFetch("/api/charity/donate", {
        method: "POST",
        body: JSON.stringify({
          event_slug: event.slug,
          charity_slug: charity,
          aura_amount: n,
          message,
          anonymous,
        }),
      });
      setStatus({ ok: true, msg: t("charity.thanksDesc", { n: fmt(n) }) });
      setMessage("");
      onDonated();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setStatus({ ok: false, msg: e.data?.detail ?? "Erreur" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="space-y-3 rounded-2xl border border-secondary/40 bg-secondary/5 p-5"
    >
      <h3 className="text-base font-semibold text-secondary-light">{t("charity.giveTitle")}</h3>
      <label className="block">
        <span className="mb-1 block text-xs uppercase tracking-wider text-neutral-400">
          {t("charity.chooseCause")}
        </span>
        <select
          value={charity}
          onChange={(e) => setCharity(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        >
          {event.beneficiaries.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="mb-1 block text-xs uppercase tracking-wider text-neutral-400">
          {t("charity.amountLabel", { floor: fmt(event.floor_aura) })}
        </span>
        <input
          type="number"
          min={event.floor_aura}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs uppercase tracking-wider text-neutral-400">
          {t("charity.messageLabel")}
        </span>
        <input
          type="text"
          maxLength={140}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
      </label>
      <label className="flex items-center gap-2 text-sm text-neutral-300">
        <input
          type="checkbox"
          checked={anonymous}
          onChange={(e) => setAnonymous(e.target.checked)}
          className="h-4 w-4 accent-[#FFC81E]"
        />
        {t("charity.anonymous")}
      </label>
      <button
        type="submit"
        disabled={submitting || !event.is_open}
        className="w-full rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-white hover:bg-secondary-light disabled:opacity-50"
      >
        {submitting ? t("charity.sending") : t("charity.submit")}
      </button>
      {status && (
        <p className={`text-sm ${status.ok ? "text-emerald-300" : "text-red-300"}`}>{status.msg}</p>
      )}
    </form>
  );
}
