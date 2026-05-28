"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Monitoring = {
  checked_at: string;
  online_users: number;
  live_now: number;
  active_subscriptions: number;
  pending_payouts: number;
  services: { database: boolean; redis: boolean };
  live_channels: { slug: string; username: string; started_at: string | null }[];
};

export default function AdminMonitoringPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [data, setData] = useState<Monitoring | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const fetchData = () =>
      authFetch<Monitoring>("/api/admin/monitoring")
        .then((d) => active && setData(d))
        .catch(() => active && setError(t("common.loadError")));
    fetchData();
    const id = setInterval(fetchData, 15000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [authFetch, t]);

  if (error) return <p className="text-sm text-red-300">{error}</p>;
  if (!data) return <p className="text-neutral-500">{t("common.loading")}</p>;

  const cards: [string, string | number][] = [
    [t("admin.mon.online"), data.online_users],
    [t("admin.mon.live"), data.live_now],
    [t("admin.mon.subs"), data.active_subscriptions],
    [t("admin.mon.payouts"), data.pending_payouts],
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {cards.map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4"
          >
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-wider text-neutral-500">
          {t("admin.mon.services")}
        </h2>
        <div className="flex gap-3">
          <ServicePill label="Database" ok={data.services.database} />
          <ServicePill label="Redis" ok={data.services.redis} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-wider text-neutral-500">
          {t("admin.mon.liveChannels")}
        </h2>
        {data.live_channels.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("admin.mon.noLive")}</p>
        ) : (
          <table className="w-full text-left text-sm">
            <tbody>
              {data.live_channels.map((c) => (
                <tr key={c.slug} className="border-t border-neutral-800/60">
                  <td className="py-2 text-neutral-200">@{c.username}</td>
                  <td className="py-2 text-right text-neutral-500">
                    {c.started_at
                      ? new Date(c.started_at).toLocaleString("fr-FR", {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p className="text-xs text-neutral-600">
        {t("admin.mon.checkedAt", {
          time: new Date(data.checked_at).toLocaleTimeString("fr-FR"),
        })}
      </p>
    </div>
  );
}

function ServicePill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span
      className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${
        ok
          ? "border-emerald-500/40 text-emerald-300"
          : "border-red-500/40 text-red-300"
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
      {label}
    </span>
  );
}
