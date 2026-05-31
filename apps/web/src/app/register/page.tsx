"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { TurnstileWidget } from "@/components/TurnstileWidget";
import { isTurnstileEnabled } from "@/lib/turnstile";

export default function RegisterPage() {
  const t = useT();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [invite, setInvite] = useState("");
  const [accepted, setAccepted] = useState(false);
  // Honeypot : champ visuellement caché. Rempli ⇒ bot.
  const [website, setWebsite] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("invite");
    if (code) setInvite(code.toUpperCase());
  }, []);

  const onCaptcha = useCallback((token: string) => setCaptchaToken(token), []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          username,
          password,
          invite,
          terms_accepted: accepted,
          website, // honeypot, le serveur rejette si non vide
          captcha_token: captchaToken,
        }),
      });
      setStatus({ ok: true, msg: t("auth.registerOk") });
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setStatus({ ok: false, msg: e.data?.detail ?? t("auth.registerFail") });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("auth.registerTitle")}</h1>
      <form onSubmit={submit} className="space-y-4">
        <Field label={t("auth.email")} type="email" value={email} onValueChange={setEmail} required />
        <Field
          label={t("auth.username")}
          type="text"
          value={username}
          onValueChange={setUsername}
          pattern="^[a-z0-9_]{3,30}$"
          required
        />
        <Field
          label={t("auth.passwordHint")}
          type="password"
          value={password}
          onValueChange={setPassword}
          required
          minLength={10}
        />
        <Field
          label={t("auth.referralOptional")}
          type="text"
          value={invite}
          onValueChange={(v) => setInvite(v.toUpperCase())}
          maxLength={16}
        />
        {/* Honeypot anti-bot : caché aux humains via aria/tabindex/css. */}
        <div aria-hidden className="hidden">
          <label>
            Ne pas remplir
            <input
              type="text"
              tabIndex={-1}
              autoComplete="off"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
            />
          </label>
        </div>
        <label className="flex items-start gap-2 text-sm text-neutral-300">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            required
            className="mt-0.5 h-4 w-4 cursor-pointer accent-emerald-500"
          />
          <span>
            {t("auth.ageTerms")}{" "}
            <a href="/terms" className="text-emerald-300 underline">
              {t("auth.termsLink")}
            </a>
          </span>
        </label>
        <TurnstileWidget onVerify={onCaptcha} />
        <button
          type="submit"
          disabled={busy || !accepted || (isTurnstileEnabled() && !captchaToken)}
          className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "..." : t("auth.signup")}
        </button>
      </form>
      {status && (
        <p className={`mt-4 text-sm ${status.ok ? "text-emerald-300" : "text-red-300"}`}>
          {status.msg}
        </p>
      )}
      <p className="mt-6 text-sm text-neutral-400">
        {t("auth.haveAccount")}{" "}
        <a href="/login" className="text-emerald-300 underline">
          {t("nav.login")}
        </a>
      </p>
    </main>
  );
}

type FieldProps = {
  label: string;
  type: string;
  value: string;
  onValueChange: (v: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type">;

function Field({ label, type, value, onValueChange, ...rest }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-secondary-light"
        {...rest}
      />
    </label>
  );
}
