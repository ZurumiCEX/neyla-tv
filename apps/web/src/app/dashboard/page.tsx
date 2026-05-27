"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

type Category = { slug: string; name: string };

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
  category: Category | null;
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, authFetch } = useAuth();
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [rotating, setRotating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [revealKey, setRevealKey] = useState(false);

  // Form state mirror.
  const [title, setTitle] = useState("");
  const [categorySlug, setCategorySlug] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me");
      setChannel(data);
      setTitle(data.title);
      setCategorySlug(data.category?.slug ?? "");
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
    apiFetch<{ results: Category[] }>("/api/discover/categories?limit=100")
      .then((d) => setCategories(d.results))
      .catch(() => undefined);
  }, [loading, user, load, router]);

  async function save() {
    setSaving(true);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me", {
        method: "PATCH",
        body: JSON.stringify({
          title,
          category_slug: categorySlug || null,
        }),
      });
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  }

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
        <section className="space-y-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <header className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">@{channel.slug}</h2>
            <Link
              href={`/c/${channel.slug}`}
              className="text-sm text-emerald-300 underline"
            >
              Page publique →
            </Link>
          </header>

          <div className="space-y-3 border-b border-neutral-800 pb-6">
            <Field label="Titre du stream">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={140}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
              />
            </Field>
            <Field label="Catégorie">
              <select
                value={categorySlug}
                onChange={(e) => setCategorySlug(e.target.value)}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
              >
                <option value="">— aucune —</option>
                {categories.map((c) => (
                  <option key={c.slug} value={c.slug}>
                    {c.name}
                  </option>
                ))}
              </select>
            </Field>
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
          </div>

          {channel.is_provisioned ? (
            <>
              <Field label="Statut">
                <span className="text-emerald-300">✓ Streamer approuvé — Live Input prêt</span>
              </Field>

              <Field label="Serveur RTMPS">
                <code className="break-all text-emerald-300">
                  {channel.rtmps_url || "—"}
                </code>
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
            </>
          ) : (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="font-semibold text-amber-300">Accès streamer requis</p>
              <p className="mt-1 text-sm text-neutral-300">
                Le streaming nécessite une validation par l&apos;équipe. Ta clé RTMPS et
                les outils de diffusion seront débloqués une fois ta candidature approuvée.
              </p>
              <p className="mt-2 text-xs text-neutral-500">
                La candidature en ligne arrive très bientôt.
              </p>
            </div>
          )}
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
