"use client";

import { useEffect, useMemo, useState } from "react";
import { AreaChart, Donut, type DonutSegment, ProgressBar, Sparkline } from "@/components/charts";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Overview = {
  users_total: number;
  dau: number;
  mau: number;
  streamers_total: number;
  live_now: number;
  broadcast_hours: number;
  top_streamers: { username: string; followers: number; is_live: boolean }[];
};
type Totals = {
  purchases_xof: number;
  tips_aura: number;
  subs_aura: number;
  platform_commission_aura: number;
  payouts_aura: number;
};
type Point = Totals & { date: string };
type Growth = {
  new_users_7d: number;
  new_users_30d: number;
  returning_users_7d: number;
  active_7d: number;
};
type Dashboard = {
  overview: Overview;
  growth: Growth;
  revenue: { series: Point[]; totals: Totals };
};

type MetricKey = "purchases_xof" | "tips_aura" | "subs_aura" | "platform_commission_aura";

const DONUT_COLORS = ["#5D1C6A", "#3b82f6", "#d946ef", "#f59e0b", "#06b6d4"];

function fmt(n: number): string {
  return n.toLocaleString("fr-FR");
}
function compact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}
function trendPct(values: number[]): number | null {
  if (values.length < 4) return null;
  const half = Math.floor(values.length / 2);
  const older = values.slice(0, half).reduce((a, b) => a + b, 0);
  const recent = values.slice(half).reduce((a, b) => a + b, 0);
  if (older === 0) return recent > 0 ? 100 : 0;
  return ((recent - older) / older) * 100;
}

export default function AdminDashboardPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metric, setMetric] = useState<MetricKey>("purchases_xof");

  useEffect(() => {
    authFetch<Dashboard>("/api/admin/dashboard?days=30")
      .then(setData)
      .catch(() => setError(t("common.loadError")));
  }, [authFetch, t]);

  const metrics = useMemo(
    () =>
      ({
        purchases_xof: { label: t("admin.metric.revenue"), color: "#5D1C6A", unit: "FCFA" },
        tips_aura: { label: t("admin.metric.tips"), color: "#3b82f6", unit: "Aura" },
        subs_aura: { label: t("admin.metric.subs"), color: "#d946ef", unit: "Aura" },
        platform_commission_aura: {
          label: t("admin.metric.commission"),
          color: "#f59e0b",
          unit: "Aura",
        },
      }) as const,
    [t],
  );

  if (error) return <p className="text-sm text-red-300">{error}</p>;
  if (!data) return <p className="text-neutral-500">{t("common.loading")}</p>;

  const { overview, growth, revenue } = data;
  const series = revenue.series;
  const labels = series.map((p) => p.date.slice(8));

  const cards: { key: MetricKey; value: string }[] = [
    { key: "purchases_xof", value: `${fmt(revenue.totals.purchases_xof)} FCFA` },
    { key: "tips_aura", value: `${fmt(revenue.totals.tips_aura)}` },
    { key: "subs_aura", value: `${fmt(revenue.totals.subs_aura)}` },
    { key: "platform_commission_aura", value: `${fmt(revenue.totals.platform_commission_aura)}` },
  ];

  const kpis: [string, string | number][] = [
    [t("admin.card.users"), fmt(overview.users_total)],
    [t("admin.card.mau"), fmt(overview.mau)],
    [t("admin.card.streamers"), fmt(overview.streamers_total)],
    [t("admin.card.liveNow"), fmt(overview.live_now)],
  ];

  const topStreamers = overview.top_streamers.filter((s) => s.followers > 0).slice(0, 5);
  const donutSegments: DonutSegment[] = topStreamers.map((s, i) => ({
    label: s.username,
    value: s.followers,
    color: DONUT_COLORS[i % DONUT_COLORS.length],
  }));
  const totalFollowers = topStreamers.reduce((a, s) => a + s.followers, 0);

  const ratio = (a: number, b: number) => (b > 0 ? (a / b) * 100 : 0);
  const m = metrics[metric];

  return (
    <div className="space-y-6">
      {/* Cartes principales avec sparkline */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ key, value }) => {
          const info = metrics[key];
          const values = series.map((p) => p[key]);
          const tr = trendPct(values);
          return (
            <div
              key={key}
              className="relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5"
            >
              <p className="text-sm text-neutral-400">{info.label}</p>
              <p className="mt-1 text-2xl font-bold text-neutral-100">{value}</p>
              {tr !== null && (
                <p
                  className={`mt-1 flex items-center gap-1 text-xs ${
                    tr >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  <span>{tr >= 0 ? "▲" : "▼"}</span>
                  {Math.abs(tr).toFixed(1)}% <span className="text-neutral-500">{t("admin.dash.vsPrev")}</span>
                </p>
              )}
              <Sparkline values={values} color={info.color} className="mt-3 h-10 w-full" />
            </div>
          );
        })}
      </div>

      {/* KPIs plateforme compacts */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(([label, value]) => (
          <div key={label} className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* Graphe d'aperçu */}
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold">{t("admin.dash.overview")}</h2>
              <p className="text-sm text-neutral-500">{t("admin.dash.overviewSub")}</p>
            </div>
            <div className="flex rounded-lg bg-neutral-800/60 p-0.5">
              {(Object.keys(metrics) as MetricKey[]).map((k) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setMetric(k)}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                    metric === k
                      ? "bg-neutral-700 text-neutral-100"
                      : "text-neutral-400 hover:text-neutral-200"
                  }`}
                >
                  {metrics[k].label}
                </button>
              ))}
            </div>
          </div>
          <AreaChart
            values={series.map((p) => p[metric])}
            labels={labels}
            color={m.color}
            formatY={compact}
          />
        </section>

        {/* Colonne droite */}
        <div className="space-y-6">
          <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
            <h2 className="text-lg font-bold">{t("admin.dash.topStreamers")}</h2>
            <p className="mb-4 text-sm text-neutral-500">{t("admin.dash.byFollowers")}</p>
            {donutSegments.length === 0 ? (
              <p className="text-sm text-neutral-500">{t("admin.an.noStreamer")}</p>
            ) : (
              <div className="flex items-center gap-4">
                <Donut
                  segments={donutSegments}
                  centerValue={compact(totalFollowers)}
                  centerLabel={t("admin.dash.followers")}
                />
                <ul className="flex-1 space-y-2 text-sm">
                  {topStreamers.map((s, i) => (
                    <li key={s.username} className="flex items-center justify-between gap-2">
                      <span className="flex min-w-0 items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                        />
                        <span className="truncate text-neutral-300">@{s.username}</span>
                      </span>
                      <span className="font-semibold text-neutral-100">{fmt(s.followers)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
            <h2 className="text-lg font-bold">{t("admin.dash.ratios")}</h2>
            <ProgressBar
              label={t("admin.ratio.live")}
              value={ratio(overview.live_now, overview.streamers_total)}
              hint={`${fmt(overview.live_now)} / ${fmt(overview.streamers_total)}`}
              color="#5D1C6A"
            />
            <ProgressBar
              label={t("admin.ratio.stickiness")}
              value={ratio(overview.dau, overview.mau)}
              hint={`DAU ${fmt(overview.dau)} / MAU ${fmt(overview.mau)}`}
              color="#3b82f6"
            />
            <ProgressBar
              label={t("admin.ratio.retention")}
              value={ratio(growth.returning_users_7d, growth.active_7d)}
              hint={`${fmt(growth.returning_users_7d)} / ${fmt(growth.active_7d)}`}
              color="#d946ef"
            />
          </section>
        </div>
      </div>
    </div>
  );
}
