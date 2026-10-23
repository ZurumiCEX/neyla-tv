"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function ForgotPasswordPage() {
  const t = useT();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      // Réponse identique que le compte existe ou non (pas de fuite d'emails).
      await apiFetch("/api/auth/password/reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setSent(true);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("auth.forgotError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-2 text-2xl font-bold">{t("auth.forgotTitle")}</h1>
      <p className="mb-6 text-sm text-neutral-400">{t("auth.forgotIntro")}</p>
      {sent ? (
        <p className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          {t("auth.forgotSent")}
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm text-neutral-300">{t("auth.email")}</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-secondary-light"
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {busy ? "..." : t("auth.forgotSubmit")}
          </button>
          {error && <p className="text-sm text-red-300">{error}</p>}
        </form>
      )}
      <p className="mt-6 text-sm text-neutral-400">
        <Link href="/login" className="text-emerald-300 underline">
          {t("auth.backToLogin")}
        </Link>
      </p>
    </main>
  );
}
