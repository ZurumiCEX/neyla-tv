"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Donut, type DonutSegment, ProgressBar } from "@/components/charts";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Overview = {
  users_total: number;
  dau: number;
  mau: number;
  streamers_total: number;
  live_now: number;
  streams_total: number;
  streams_7d: number;
  broadcast_hours: number;
  peak_concurrent: number;
  top_streamers: { username: string; followers: number; is_live: boolean }[];
};

const DONUT_COLORS = ["#10b981", "#3b82f6", "#d946ef", "#f59e0b", "#06b6d4"];

function fmt(n: number): string {
  return n.toLocaleString("fr-FR");
}
function compact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}

export default function AdminAnalyticsPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await authFetch<Overview>("/api/analytics/overview"));
    } catch {
      setError(t("admin.an.accessDenied"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  if (error) return <p className="text-sm text-red-300">{error}</p>;
  if (!data) return <p className="text-neutral-500">{t("common.loading")}</p>;

  const cards: [string, string | number, string][] = [
    [t("admin.card.users"), fmt(data.users_total), "#10b981"],
    [t("admin.card.dau"), fmt(data.dau), "#3b82f6"],
    [t("admin.card.mau"), fmt(data.mau), "#06b6d4"],
    [t("admin.card.streamers"), fmt(data.streamers_total), "#d946ef"],
    [t("admin.card.liveNow"), fmt(data.live_now), "#ef4444"],
    [t("admin.card.streamsTotal"), fmt(data.streams_total), "#f59e0b"],
    [t("admin.card.streams7d"), fmt(data.streams_7d), "#8b5cf6"],
    [t("admin.card.broadcastHours"), `${fmt(data.broadcast_hours)} h`, "#14b8a6"],
  ];

  const top = data.top_streamers.filter((s) => s.followers > 0).slice(0, 5);
  const segments: DonutSegment[] = top.map((s, i) => ({
    label: s.username,
    value: s.followers,
    color: DONUT_COLORS[i % DONUT_COLORS.length],
  }));
  const totalFollowers = top.reduce((a, s) => a + s.followers, 0);
  const ratio = (a: number, b: number) => (b > 0 ? (a / b) * 100 : 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {cards.map(([label, value, color]) => (
          <div
            key={label}
            className="relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4"
          >
            <span
              className="absolute left-0 top-0 h-full w-1"
              style={{ backgroundColor: color }}
            />
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[360px_1fr]">
        <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <h2 className="text-lg font-bold">{t("admin.dash.ratios")}</h2>
          <ProgressBar
            label={t("admin.ratio.live")}
            value={ratio(data.live_now, data.streamers_total)}
            hint={`${fmt(data.live_now)} / ${fmt(data.streamers_total)}`}
            color="#10b981"
          />
          <ProgressBar
            label={t("admin.ratio.stickiness")}
            value={ratio(data.dau, data.mau)}
            hint={`DAU ${fmt(data.dau)} / MAU ${fmt(data.mau)}`}
            color="#3b82f6"
          />
          <div className="rounded-xl border border-neutral-800/60 bg-neutral-900/40 p-3">
            <p className="text-xs uppercase tracking-wider text-neutral-500">
              {t("admin.card.peakViewers")}
            </p>
            <p className="mt-1 text-xl font-bold">{fmt(data.peak_concurrent)}</p>
          </div>
        </section>

        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <h2 className="text-lg font-bold">{t("admin.an.topStreamers")}</h2>
          <p className="mb-4 text-sm text-neutral-500">{t("admin.dash.byFollowers")}</p>
          {segments.length === 0 ? (
            <p className="text-sm text-neutral-500">{t("admin.an.noStreamer")}</p>
          ) : (
            <div className="flex flex-wrap items-center gap-6">
              <Donut
                segments={segments}
                centerValue={compact(totalFollowers)}
                centerLabel={t("admin.dash.followers")}
              />
              <ul className="flex-1 space-y-2 text-sm">
                {top.map((s, i) => (
                  <li key={s.username} className="flex items-center justify-between gap-2">
                    <span className="flex min-w-0 items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                      />
                      <span className="truncate text-neutral-300">@{s.username}</span>
                      {s.is_live && <span className="text-xs text-red-400">{t("admin.an.live")}</span>}
                    </span>
                    <span className="font-semibold text-neutral-100">{fmt(s.followers)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
