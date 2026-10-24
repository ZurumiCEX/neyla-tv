"use client";

import { useEffect, useState } from "react";
import { ChartLine, History } from "lucide-react";
import { AreaChart } from "@/components/charts";
import { Panel, Stat } from "@/components/dashboard/kit";
import { ActivityFeedPanel } from "@/components/dashboard/widgets";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type MyStats = {
  sessions_total: number;
  broadcast_hours: number;
  peak_viewers: number;
  follower_count: number;
};
type StreamSession = {
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  peak_viewers: number;
  category: string | null;
};

export default function DashboardAnalyticsPage() {
  const t = useT();
  const { num, date, time } = useFormat();
  const { authFetch } = useAuth();
  const [stats, setStats] = useState<MyStats | null>(null);
  const [sessions, setSessions] = useState<StreamSession[]>([]);

  useEffect(() => {
    authFetch<MyStats>("/api/analytics/me")
      .then(setStats)
      .catch(() => undefined);
    authFetch<{ results: StreamSession[] }>("/api/channels/me/sessions?limit=30")
      .then((d) => setSessions(d.results))
      .catch(() => undefined);
  }, [authFetch]);

  const duration = (s: number | null) => {
    if (s === null) return t("dash.durationOngoing");
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h} h ${String(m).padStart(2, "0")}` : t("dash.durationMin", { m });
  };
  const chronological = [...sessions].reverse();

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label={t("dash.statsStreams")} value={stats ? num(stats.sessions_total) : "—"} />
        <Stat
          label={t("dash.statsHours")}
          value={stats ? `${num(stats.broadcast_hours)} h` : "—"}
        />
        <Stat label={t("dash.statsPeak")} value={stats ? num(stats.peak_viewers) : "—"} />
        <Stat label={t("dash.followers")} value={stats ? num(stats.follower_count) : "—"} />
      </div>
      <Panel title={t("dash2.peakChart")} icon={ChartLine}>
        {chronological.length < 2 ? (
          <p className="text-sm text-neutral-500">{t("dash.noBroadcast")}</p>
        ) : (
          <AreaChart
            values={chronological.map((s) => s.peak_viewers)}
            labels={chronological.map((s) =>
              date(s.started_at, { day: "2-digit", month: "short" }),
            )}
            formatY={(v) => num(v)}
          />
        )}
      </Panel>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel title={t("dash.historyTitle")} icon={History} bodyClassName="p-0">
          {sessions.length === 0 ? (
            <p className="p-4 text-sm text-neutral-500">{t("dash.noBroadcast")}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-neutral-500">
                <tr>
                  <th className="px-4 py-2">{t("dash.colDate")}</th>
                  <th className="px-4 py-2">{t("dash.colDuration")}</th>
                  <th className="px-4 py-2">{t("dash.colPeak")}</th>
                  <th className="px-4 py-2">{t("dash.colCategory")}</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.started_at} className="border-t border-neutral-800/60">
                    <td className="px-4 py-2 text-neutral-300">
                      {date(s.started_at, { day: "2-digit", month: "short" })} {time(s.started_at)}
                    </td>
                    <td className="px-4 py-2 text-neutral-300">{duration(s.duration_seconds)}</td>
                    <td className="px-4 py-2 tabular-nums text-neutral-300">
                      {num(s.peak_viewers)}
                    </td>
                    <td className="px-4 py-2 text-neutral-400">{s.category ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
        <ActivityFeedPanel className="h-[420px]" />
      </div>
    </div>
  );
}
