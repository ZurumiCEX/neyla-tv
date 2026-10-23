"use client";

import { use, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { PasswordInput } from "@/components/PasswordInput";
import { PASSWORD_MIN_LENGTH, PasswordStrength } from "@/components/PasswordStrength";

export default function ResetPasswordPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const t = useT();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mismatch = confirm.length > 0 && confirm !== password;
  const canSubmit = !busy && password.length >= PASSWORD_MIN_LENGTH && confirm === password;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await apiFetch("/api/auth/password/reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      });
      setDone(true);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("auth.resetError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("auth.resetTitle")}</h1>
      {done ? (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          <p>{t("auth.resetDone")}</p>
          <Link href="/login" className="mt-3 inline-block font-semibold underline">
            {t("nav.login")}
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div>
            <PasswordInput
              label={t("auth.newPassword")}
              value={password}
              onValueChange={setPassword}
              autoComplete="new-password"
              minLength={PASSWORD_MIN_LENGTH}
              describedBy="reset-strength"
              required
            />
            <PasswordStrength password={password} id="reset-strength" />
          </div>
          <div>
            <PasswordInput
              label={t("auth.passwordConfirm")}
              value={confirm}
              onValueChange={setConfirm}
              autoComplete="new-password"
              invalid={mismatch}
              required
            />
            {confirm.length > 0 && (
              <p className={`mt-1 text-xs ${mismatch ? "text-red-300" : "text-emerald-400"}`}>
                {mismatch ? t("auth.passwordMismatch") : t("auth.passwordMatch")}
              </p>
            )}
          </div>
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {busy ? "..." : t("auth.resetSubmit")}
          </button>
          {error && (
            <p className="text-sm text-red-300">
              {error}{" "}
              <Link href="/forgot-password" className="underline">
                {t("auth.resetAgain")}
              </Link>
            </p>
          )}
        </form>
      )}
    </main>
  );
}
