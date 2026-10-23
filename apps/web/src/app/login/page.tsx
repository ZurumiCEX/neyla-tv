"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PasswordInput } from "@/components/PasswordInput";
import { apiErrorMessage } from "@/lib/api-errors";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginTwoFactor } = useAuth();
  const t = useT();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [twoFactorToken, setTwoFactorToken] = useState<string | null>(null);
  const [code, setCode] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await login(email, password);
      if (result.twoFactorRequired) {
        setTwoFactorToken(result.token);
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(apiErrorMessage(err, t, "auth.loginFail"));
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(e: React.FormEvent) {
    e.preventDefault();
    if (!twoFactorToken) return;
    setBusy(true);
    setError(null);
    try {
      await loginTwoFactor(twoFactorToken, code.trim());
      router.push("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err, t, "auth.2fa.invalid"));
    } finally {
      setBusy(false);
    }
  }

  if (twoFactorToken) {
    return (
      <main className="mx-auto max-w-md p-8">
        <h1 className="mb-2 text-2xl font-bold">{t("auth.2fa.title")}</h1>
        <p className="mb-6 text-sm text-neutral-400">{t("auth.2fa.prompt")}</p>
        <form onSubmit={submitCode} className="space-y-4">
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            required
            autoFocus
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-center text-lg tracking-widest text-neutral-100 outline-none focus:border-secondary-light"
          />
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {busy ? "..." : t("auth.2fa.verify")}
          </button>
        </form>
        {error && <p className="mt-4 text-sm text-red-300">{error}</p>}
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("auth.loginTitle")}</h1>
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
        <div>
          <PasswordInput
            label={t("auth.password")}
            value={password}
            onValueChange={setPassword}
            autoComplete="current-password"
            required
          />
          <Link
            href="/forgot-password"
            className="mt-1 inline-block text-xs text-neutral-400 hover:text-emerald-300"
          >
            {t("auth.forgot")}
          </Link>
        </div>
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "..." : t("auth.signin")}
        </button>
      </form>
      {error && (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300"
        >
          {error}{" "}
          <Link href="/forgot-password" className="underline">
            {t("auth.forgot")}
          </Link>
        </p>
      )}
      <p className="mt-6 text-sm text-neutral-400">
        {t("auth.noAccount")}{" "}
        <Link href="/register" className="text-emerald-300 underline">
          {t("nav.register")}
        </Link>
      </p>
    </main>
  );
}
