"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

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
  const { authFetch } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authFetch<Dashboard>("/api/admin/dashboard?days=14")
      .then(setData)
      .catch(() => setError("Chargement impossible."));
  }, [authFetch]);

  if (error) return <p className="text-sm text-red-300">{error}</p>;
  if (!data) return <p className="text-neutral-500">Chargement…</p>;

  const o = data.overview;
  const t = data.revenue.totals;
  const overviewCards: [string, string | number][] = [
    ["Utilisateurs", o.users_total],
    ["Actifs (24 h)", o.dau],
    ["Actifs (30 j)", o.mau],
    ["Streamers", o.streamers_total],
    ["En direct", o.live_now],
    ["Heures diffusées", `${o.broadcast_hours} h`],
  ];
  const revenueCards: [string, string][] = [
    ["Achats (14 j)", `${t.purchases_xof.toLocaleString("fr-FR")} FCFA`],
    ["Tips", `${t.tips_aura.toLocaleString("fr-FR")} Aura`],
    ["Abonnements", `${t.subs_aura.toLocaleString("fr-FR")} Aura`],
    ["Commission plateforme", `${t.platform_commission_aura.toLocaleString("fr-FR")} Aura`],
    ["Retraits", `${t.payouts_aura.toLocaleString("fr-FR")} Aura`],
  ];

  const maxCommission = Math.max(1, ...data.revenue.series.map((p) => p.platform_commission_aura));

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-3 text-lg font-bold">Activité</h2>
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
        <h2 className="mb-3 text-lg font-bold">Revenus (14 derniers jours)</h2>
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
        <h2 className="mb-3 text-lg font-bold">Commission plateforme / jour</h2>
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
