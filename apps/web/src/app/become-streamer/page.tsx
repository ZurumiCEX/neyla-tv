"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

type Application = {
  status: "none" | "pending" | "approved" | "rejected";
  motivation?: string;
  rejection_reason?: string;
};

export default function BecomeStreamerPage() {
  const router = useRouter();
  const { user, loading, authFetch } = useAuth();
  const [application, setApplication] = useState<Application | null>(null);
  const [motivation, setMotivation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await authFetch<Application>("/api/streamer/application");
      setApplication(data);
    } catch {
      setApplication({ status: "none" });
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

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const data = await authFetch<Application>("/api/streamer/apply", {
        method: "POST",
        body: JSON.stringify({ motivation }),
      });
      setApplication(data);
      setMotivation("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de l'envoi de la candidature.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !application) {
    return <main className="p-8 text-neutral-500">Chargement…</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Devenir streamer</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {application.status === "approved" ? (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6">
          <p className="font-semibold text-emerald-300">✓ Tu es streamer !</p>
          <p className="mt-1 text-sm text-neutral-300">
            Ta chaîne est provisionnée. Récupère ta clé RTMPS dans le dashboard.
          </p>
          <Link
            href="/dashboard"
            className="mt-3 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
          >
            Ouvrir le dashboard
          </Link>
        </div>
      ) : application.status === "pending" ? (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6">
          <p className="font-semibold text-amber-300">⏳ Candidature en attente</p>
          <p className="mt-1 text-sm text-neutral-300">
            Ta demande est en cours d&apos;examen par l&apos;équipe. Tu seras notifié
            une fois la décision prise.
          </p>
        </div>
      ) : (
        <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          {application.status === "rejected" && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
              Candidature précédente refusée
              {application.rejection_reason
                ? ` : ${application.rejection_reason}`
                : "."}{" "}
              Tu peux retenter.
            </p>
          )}
          <p className="text-sm text-neutral-300">
            L&apos;inscription est ouverte à tous, mais le streaming est validé
            manuellement pour démarrer avec un nombre limité de créateurs. Dis-nous
            pourquoi tu veux streamer (optionnel).
          </p>
          <textarea
            value={motivation}
            onChange={(e) => setMotivation(e.target.value)}
            maxLength={1000}
            rows={4}
            placeholder="Ta motivation (optionnel)…"
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          />
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {submitting ? "Envoi…" : "Envoyer ma candidature"}
          </button>
        </section>
      )}
    </main>
  );
}
