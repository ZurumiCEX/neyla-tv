"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

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
  const { user, loading, authFetch } = useAuth();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await authFetch<Overview>("/api/analytics/overview"));
    } catch {
      setError("Accès refusé (réservé aux administrateurs).");
    }
  }, [authFetch]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  if (loading) return <main className="p-8 text-neutral-500">Chargement…</main>;
  if (error) return <main className="p-8 text-sm text-red-300">{error}</main>;
  if (!data) return <main className="p-8 text-neutral-500">Chargement…</main>;

  const cards: [string, string | number][] = [
    ["Utilisateurs", data.users_total],
    ["Actifs (24 h)", data.dau],
    ["Actifs (30 j)", data.mau],
    ["Streamers", data.streamers_total],
    ["En direct", data.live_now],
    ["Streams (total)", data.streams_total],
    ["Streams (7 j)", data.streams_7d],
    ["Heures diffusées", `${data.broadcast_hours} h`],
    ["Pic spectateurs", data.peak_concurrent],
  ];

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Analytics</h1>

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

      <h2 className="mb-3 mt-10 text-lg font-bold">Top streamers</h2>
      {data.top_streamers.length === 0 ? (
        <p className="text-sm text-neutral-500">Aucun streamer.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="pb-2">Streamer</th>
              <th className="pb-2">Followers</th>
              <th className="pb-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {data.top_streamers.map((s) => (
              <tr key={s.username} className="border-t border-neutral-800/60">
                <td className="py-2 text-neutral-200">@{s.username}</td>
                <td className="py-2 text-neutral-300">{s.followers}</td>
                <td className="py-2">
                  {s.is_live ? (
                    <span className="text-red-400">en direct</span>
                  ) : (
                    <span className="text-neutral-500">hors-ligne</span>
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
