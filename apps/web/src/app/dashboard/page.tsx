"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

type MyChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  rtmps_url: string;
  rtmps_key: string;
  hls_playback_url: string;
  is_live: boolean;
  is_provisioned: boolean;
  last_live_started_at: string | null;
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, authFetch } = useAuth();
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rotating, setRotating] = useState(false);
  const [revealKey, setRevealKey] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me");
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec du chargement de la chaîne.");
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

  async function rotate() {
    setRotating(true);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me/key/rotate", {
        method: "POST",
      });
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de la régénération.");
    } finally {
      setRotating(false);
    }
  }

  if (loading || (!user && !error)) {
    return <main className="p-8 text-neutral-500">Chargement…</main>;
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Dashboard streamer</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {channel && (
        <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <header className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">@{channel.slug}</h2>
            <Link
              href={`/c/${channel.slug}`}
              className="text-sm text-emerald-300 underline"
            >
              Page publique →
            </Link>
          </header>

          <Field label="Statut provisioning">
            {channel.is_provisioned ? (
              <span className="text-emerald-300">✓ Live Input prêt</span>
            ) : (
              <span className="text-amber-300">⏳ Provisioning en cours…</span>
            )}
          </Field>

          <Field label="Serveur RTMPS">
            <code className="break-all text-emerald-300">{channel.rtmps_url || "—"}</code>
          </Field>

          <Field label="Stream key">
            <div className="flex items-center gap-2">
              <code className="break-all text-emerald-300">
                {channel.rtmps_key
                  ? revealKey
                    ? channel.rtmps_key
                    : "•".repeat(Math.min(channel.rtmps_key.length, 40))
                  : "—"}
              </code>
              {channel.rtmps_key && (
                <button
                  type="button"
                  onClick={() => setRevealKey((v) => !v)}
                  className="rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-300 hover:border-neutral-500"
                >
                  {revealKey ? "Masquer" : "Afficher"}
                </button>
              )}
            </div>
          </Field>

          <Field label="URL de lecture HLS">
            <code className="break-all text-neutral-300">
              {channel.hls_playback_url || "—"}
            </code>
          </Field>

          <button
            type="button"
            onClick={rotate}
            disabled={rotating}
            className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {rotating ? "Régénération…" : "Régénérer la stream key"}
          </button>
          <p className="text-xs text-neutral-500">
            Régénérer invalide l&apos;ancienne clé. OBS devra être reconfiguré.
          </p>
        </section>
      )}
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <div className="text-sm">{children}</div>
    </div>
  );
}
