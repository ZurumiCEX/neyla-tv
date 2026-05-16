"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

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
  const [accessToken, setAccessToken] = useState<string>("");
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rotating, setRotating] = useState(false);
  const [revealKey, setRevealKey] = useState(false);

  async function fetchChannel(token: string) {
    setError(null);
    try {
      const data = await apiFetch<MyChannel>("/api/channels/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChannel(data);
    } catch (err) {
      const e = err as { status?: number; data?: { detail?: string } };
      setError(
        e.status === 401
          ? "Token expiré ou invalide. Reconnecte-toi via /login."
          : (e.data?.detail ?? "Échec du chargement de la chaîne."),
      );
    }
  }

  useEffect(() => {
    if (!accessToken) return;
    fetchChannel(accessToken);
  }, [accessToken]);

  async function rotate() {
    if (!accessToken) return;
    setRotating(true);
    try {
      const data = await apiFetch<MyChannel>("/api/channels/me/key/rotate", {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de la régénération.");
    } finally {
      setRotating(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Dashboard streamer</h1>

      <section className="mb-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
        <label className="block text-sm">
          <span className="mb-1 block text-neutral-300">Access token (depuis /login)</span>
          <textarea
            value={accessToken}
            onChange={(e) => setAccessToken(e.target.value.trim())}
            rows={3}
            placeholder="Colle ici l'access token retourné par /login"
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 font-mono text-xs text-neutral-100 outline-none focus:border-emerald-500"
          />
        </label>
        <p className="mt-2 text-xs text-neutral-500">
          Phase 1/2 démo : le frontend complet (cookie + auto-refresh) arrive en Phase 3.
        </p>
      </section>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {channel && (
        <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <header className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">@{channel.slug}</h2>
            <span
              className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs ${
                channel.is_live
                  ? "bg-red-500/15 text-red-300"
                  : "bg-neutral-800 text-neutral-400"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  channel.is_live ? "bg-red-400 animate-pulse" : "bg-neutral-500"
                }`}
              />
              {channel.is_live ? "EN DIRECT" : "Hors-ligne"}
            </span>
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
            <code className="break-all text-neutral-300">{channel.hls_playback_url || "—"}</code>
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
