"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

  if (loading) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
  if (error) return <main className="p-8 text-sm text-red-300">{error}</main>;
  if (!data) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const cards: [string, string | number][] = [
    [t("admin.card.users"), data.users_total],
    [t("admin.card.dau"), data.dau],
    [t("admin.card.mau"), data.mau],
    [t("admin.card.streamers"), data.streamers_total],
    [t("admin.card.liveNow"), data.live_now],
    [t("admin.card.streamsTotal"), data.streams_total],
    [t("admin.card.streams7d"), data.streams_7d],
    [t("admin.card.broadcastHours"), `${data.broadcast_hours} h`],
    [t("admin.card.peakViewers"), data.peak_concurrent],
  ];

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("admin.an.title")}</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4"
          >
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <h2 className="mb-3 mt-10 text-lg font-bold">{t("admin.an.topStreamers")}</h2>
      {data.top_streamers.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("admin.an.noStreamer")}</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="pb-2">{t("admin.an.colStreamer")}</th>
              <th className="pb-2">{t("admin.an.colFollowers")}</th>
              <th className="pb-2">{t("admin.an.colStatus")}</th>
            </tr>
          </thead>
          <tbody>
            {data.top_streamers.map((s) => (
              <tr key={s.username} className="border-t border-neutral-800/60">
                <td className="py-2 text-neutral-200">@{s.username}</td>
                <td className="py-2 text-neutral-300">{s.followers}</td>
                <td className="py-2">
                  {s.is_live ? (
                    <span className="text-red-400">{t("admin.an.live")}</span>
                  ) : (
                    <span className="text-neutral-500">{t("admin.an.offline")}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
