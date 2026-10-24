"use client";

import { useState } from "react";
import { PasswordInput } from "@/components/PasswordInput";
import { PasswordStrength } from "@/components/PasswordStrength";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

/** Changement de mot de passe (ancien requis) : les autres appareils sont déconnectés. */
export function ChangePasswordForm() {
  const t = useT();
  const { authFetch } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await authFetch<{ sessions_revoked: number }>("/api/auth/password/change", {
        method: "POST",
        body: JSON.stringify({ password: current, new_password: next }),
      });
      setMessage(t("security.passwordChanged", { n: res.sessions_revoked }));
      setCurrent("");
      setNext("");
    } catch (err) {
      const ex = err as { data?: { detail?: string } };
      setError(ex.data?.detail ?? t("security.passwordError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <h2 className="mb-1 font-semibold">{t("security.changePassword")}</h2>
      <p className="mb-4 text-sm text-neutral-400">{t("security.changePasswordDesc")}</p>
      <form onSubmit={submit} className="space-y-3">
        <PasswordInput
          label={t("security.currentPassword")}
          value={current}
          onValueChange={setCurrent}
          autoComplete="current-password"
          required
        />
        <PasswordInput
          label={t("security.newPassword")}
          value={next}
          onValueChange={setNext}
          autoComplete="new-password"
          required
        />
        {next && <PasswordStrength password={next} />}
        {error && <p className="text-sm text-red-300">{error}</p>}
        {message && <p className="text-sm text-green-400">{message}</p>}
        <button
          type="submit"
          disabled={busy || !current || next.length < 8}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "…" : t("security.changePasswordSubmit")}
        </button>
      </form>
    </section>
  );
}
