"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AreaChart } from "@/components/charts";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Period = "day" | "week" | "month";

type RevenuePoint = {
  date: string;
  tips: number;
  subs: number;
  referral: number;
  total: number;
};

type RevenueData = {
  period: Period;
  series: RevenuePoint[];
  totals: { tips: number; subs: number; referral: number; total: number };
  summary: { day: number; week: number; month: number };
  withdrawable: number;
};

function fmt(n: number): string {
  return n.toLocaleString("fr-FR").replace(/ /g, " ");
}

export default function RevenusPage() {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [period, setPeriod] = useState<Period>("day");
  const [data, setData] = useState<RevenueData | null>(null);
  const [busy, setBusy] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setBusy(true);
    setErr(null);
    authFetch<RevenueData>(`/api/analytics/me/revenue?period=${period}`)
      .then(setData)
      .catch(() => setErr(t("common.loadError")))
      .finally(() => setBusy(false));
  }, [user, period, authFetch, t]);

  const chartValues = useMemo(() => data?.series.map((p) => p.total) ?? [], [data]);
  const chartLabels = useMemo(() => data?.series.map((p) => p.date) ?? [], [data]);

  if (!user) {
    return (
      <main className="mx-auto max-w-md p-8 text-neutral-300">
        <p>{t("common.loading")}</p>
      </main>
    );
  }
  if (!user.is_streamer) {
    return (
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="mb-2 text-2xl font-bold">{t("revenue.title")}</h1>
        <p className="text-neutral-400">{t("nav.becomeStreamer")}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">{t("revenue.title")}</h1>
        <p className="text-sm text-neutral-400">{t("revenue.subtitle")}</p>
      </header>

      {/* Sélecteur de période */}
      <div className="mb-6 inline-flex rounded-lg border border-neutral-800 bg-neutral-900 p-1">
        {(["day", "week", "month"] as Period[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPeriod(p)}
            className={`rounded-md px-3 py-1.5 text-sm transition ${
              p === period
                ? "bg-emerald-500 font-semibold text-neutral-950"
                : "text-neutral-300 hover:text-neutral-100"
            }`}
          >
            {t(`revenue.period.${p}`)}
          </button>
        ))}
      </div>

      {/* Cartes résumé 24h/7j/30j + retirable */}
      {data && (
        <section className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          {(["day", "week", "month"] as Period[]).map((k) => (
            <SummaryCard
              key={k}
              label={t(`revenue.summary.${k}`)}
              value={fmt(data.summary[k])}
            />
          ))}
          <SummaryCard
            label={t("revenue.withdrawable")}
            value={fmt(data.withdrawable)}
            accent
            cta={
              <Link href="/wallet" className="text-xs text-emerald-300 underline">
                {t("revenue.gotoWallet")}
              </Link>
            }
          />
        </section>
      )}

      {/* Cartes totaux par source */}
      {data && (
        <section className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <SummaryCard label={t("revenue.total")} value={fmt(data.totals.total)} accent />
          <SummaryCard label={t("revenue.tips")} value={fmt(data.totals.tips)} />
          <SummaryCard label={t("revenue.subs")} value={fmt(data.totals.subs)} />
          <SummaryCard label={t("revenue.referral")} value={fmt(data.totals.referral)} />
        </section>
      )}

      {/* Graphique d'évolution */}
      <section className="mb-6 rounded-xl border border-neutral-800 bg-neutral-900 p-4">
        {busy ? (
          <p className="text-sm text-neutral-400">{t("common.loading")}</p>
        ) : err ? (
          <p className="text-sm text-red-300">{err}</p>
        ) : chartValues.length === 0 || data?.totals.total === 0 ? (
          <p className="text-sm text-neutral-400">{t("revenue.empty")}</p>
        ) : (
          <AreaChart values={chartValues} labels={chartLabels} formatY={fmt} />
        )}
      </section>

      {/* Tableau détaillé */}
      {data && data.series.length > 0 && (
        <section className="overflow-hidden rounded-xl border border-neutral-800">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-neutral-300">
              <tr>
                <th className="px-3 py-2 text-left font-medium">{t("revenue.col.date")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("revenue.col.tips")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("revenue.col.subs")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("revenue.col.referral")}</th>
                <th className="px-3 py-2 text-right font-medium">{t("revenue.col.total")}</th>
              </tr>
            </thead>
            <tbody>
              {data.series.map((p) => (
                <tr key={p.date} className="border-t border-neutral-800">
                  <td className="px-3 py-2 text-neutral-300">{p.date}</td>
                  <td className="px-3 py-2 text-right">{fmt(p.tips)}</td>
                  <td className="px-3 py-2 text-right">{fmt(p.subs)}</td>
                  <td className="px-3 py-2 text-right">{fmt(p.referral)}</td>
                  <td className="px-3 py-2 text-right font-semibold">{fmt(p.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}

function SummaryCard({
  label,
  value,
  accent,
  cta,
}: {
  label: string;
  value: string;
  accent?: boolean;
  cta?: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        accent
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-neutral-800 bg-neutral-900"
      }`}
    >
      <p className="text-xs uppercase tracking-wide text-neutral-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-neutral-100">{value}</p>
      {cta && <div className="mt-1">{cta}</div>}
    </div>
  );
}
