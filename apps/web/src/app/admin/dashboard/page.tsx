"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Overview = {
  users_total: number;
  dau: number;
  mau: number;
  streamers_total: number;
  live_now: number;
  broadcast_hours: number;
};

type Totals = {
  purchases_xof: number;
  tips_aura: number;
  subs_aura: number;
  platform_commission_aura: number;
  payouts_aura: number;
};

type Point = Totals & { date: string };

type Dashboard = {
  overview: Overview;
  revenue: { series: Point[]; totals: Totals };
};

export default function AdminDashboardPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authFetch<Dashboard>("/api/admin/dashboard?days=14")
      .then(setData)
      .catch(() => setError(t("common.loadError")));
  }, [authFetch, t]);

  if (error) return <p className="text-sm text-red-300">{error}</p>;
  if (!data) return <p className="text-neutral-500">{t("common.loading")}</p>;

  const o = data.overview;
  const tot = data.revenue.totals;
  const overviewCards: [string, string | number][] = [
    [t("admin.card.users"), o.users_total],
    [t("admin.card.dau"), o.dau],
    [t("admin.card.mau"), o.mau],
    [t("admin.card.streamers"), o.streamers_total],
    [t("admin.card.liveNow"), o.live_now],
    [t("admin.card.broadcastHours"), `${o.broadcast_hours} h`],
  ];
  const revenueCards: [string, string][] = [
    [t("admin.card.purchases14"), `${tot.purchases_xof.toLocaleString("fr-FR")} FCFA`],
    [t("admin.card.tips"), `${tot.tips_aura.toLocaleString("fr-FR")} Aura`],
    [t("admin.card.subs"), `${tot.subs_aura.toLocaleString("fr-FR")} Aura`],
    [t("admin.card.platformCommission"), `${tot.platform_commission_aura.toLocaleString("fr-FR")} Aura`],
    [t("admin.card.payouts"), `${tot.payouts_aura.toLocaleString("fr-FR")} Aura`],
  ];

  const maxCommission = Math.max(1, ...data.revenue.series.map((p) => p.platform_commission_aura));

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-3 text-lg font-bold">{t("admin.dash.activity")}</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {overviewCards.map(([label, value]) => (
            <div key={label} className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
              <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
              <p className="mt-1 text-2xl font-bold">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold">{t("admin.dash.revenue14")}</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {revenueCards.map(([label, value]) => (
            <div key={label} className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
              <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
              <p className="mt-1 text-lg font-bold">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold">{t("admin.dash.commissionPerDay")}</h2>
        <div className="flex h-40 items-end gap-1 rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
          {data.revenue.series.map((p) => (
            <div key={p.date} className="flex flex-1 flex-col items-center justify-end gap-1">
              <div
                className="w-full rounded-t bg-fuchsia-500/70"
                style={{
                  height: `${(p.platform_commission_aura / maxCommission) * 100}%`,
                  minHeight: p.platform_commission_aura > 0 ? "4px" : "0",
                }}
                title={`${p.date}: ${p.platform_commission_aura} Aura`}
              />
              <span className="text-[10px] text-neutral-600">{p.date.slice(8)}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
