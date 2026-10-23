"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { PasswordInput } from "@/components/PasswordInput";
import { PASSWORD_MIN_LENGTH, PasswordStrength } from "@/components/PasswordStrength";
import { TurnstileWidget } from "@/components/TurnstileWidget";
import { isTurnstileEnabled } from "@/lib/turnstile";

const MIN_AGE = 18;

/** Âge révolu à aujourd'hui pour une date AAAA-MM-JJ (null si invalide). */
function ageFrom(iso: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const now = new Date();
  let age = now.getFullYear() - y;
  if (now.getMonth() + 1 < mo || (now.getMonth() + 1 === mo && now.getDate() < d)) age -= 1;
  return age;
}

type ApiErr = { data?: { detail?: string; errors?: Record<string, string[]> } };

export default function RegisterPage() {
  const t = useT();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [birth, setBirth] = useState("");
  const [invite, setInvite] = useState("");
  const [accepted, setAccepted] = useState(false);
  // Honeypot : champ visuellement caché. Rempli ⇒ bot.
  const [website, setWebsite] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("invite");
    if (code) setInvite(code.toUpperCase());
  }, []);

  const onCaptcha = useCallback((token: string) => setCaptchaToken(token), []);

  const age = useMemo(() => ageFrom(birth), [birth]);
  const tooYoung = age !== null && age < MIN_AGE;
  const mismatch = confirm.length > 0 && confirm !== password;
  const maxBirth = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const canSubmit =
    !busy &&
    accepted &&
    password.length >= PASSWORD_MIN_LENGTH &&
    confirm === password &&
    age !== null &&
    !tooYoung &&
    (!isTurnstileEnabled() || Boolean(captchaToken));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setStatus(null);
    setFieldErrors({});
    try {
      await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          username,
          password,
          password_confirm: confirm,
          date_of_birth: birth,
          invite,
          terms_accepted: accepted,
          website, // honeypot, le serveur rejette si non vide
          captcha_token: captchaToken,
        }),
      });
      setStatus({ ok: true, msg: t("auth.registerOk") });
    } catch (err) {
      const e = err as ApiErr;
      const errors = e.data?.errors ?? {};
      setFieldErrors(
        Object.fromEntries(
          Object.entries(errors).map(([k, v]) => [k, Array.isArray(v) ? String(v[0]) : String(v)]),
        ),
      );
      setStatus({ ok: false, msg: e.data?.detail ?? t("auth.registerFail") });
    } finally {
      setBusy(false);
    }
  }

  if (status?.ok) {
    return (
      <main className="mx-auto max-w-md p-8">
        <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-6">
          <h1 className="text-xl font-bold text-emerald-300">{t("auth.registerDoneTitle")}</h1>
          <p className="mt-2 text-sm text-neutral-300">{status.msg}</p>
          <Link
            href="/login"
            className="mt-4 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
          >
            {t("nav.login")}
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("auth.registerTitle")}</h1>
      <form onSubmit={submit} className="space-y-4" noValidate>
        <Field
          label={t("auth.email")}
          type="email"
          value={email}
          onValueChange={setEmail}
          autoComplete="email"
          error={fieldErrors.email}
          required
        />
        <Field
          label={t("auth.username")}
          type="text"
          value={username}
          onValueChange={(v) => setUsername(v.toLowerCase())}
          autoComplete="username"
          pattern="^[a-z0-9_]{3,30}$"
          hint={t("auth.usernameHint")}
          error={fieldErrors.username}
          required
        />

        <div>
          <PasswordInput
            label={t("auth.password")}
            value={password}
            onValueChange={setPassword}
            autoComplete="new-password"
            minLength={PASSWORD_MIN_LENGTH}
            describedBy="pw-strength"
            invalid={Boolean(fieldErrors.password)}
            required
          />
          <PasswordStrength password={password} id="pw-strength" />
          {fieldErrors.password && (
            <p className="mt-1 text-xs text-red-300">{fieldErrors.password}</p>
          )}
        </div>

        <div>
          <PasswordInput
            label={t("auth.passwordConfirm")}
            value={confirm}
            onValueChange={setConfirm}
            autoComplete="new-password"
            invalid={mismatch || Boolean(fieldErrors.password_confirm)}
            required
          />
          {confirm.length > 0 && (
            <p
              className={`mt-1 text-xs transition-colors ${
                mismatch ? "text-red-300" : "text-emerald-400"
              }`}
              aria-live="polite"
            >
              {mismatch ? t("auth.passwordMismatch") : t("auth.passwordMatch")}
            </p>
          )}
        </div>

        <Field
          label={t("auth.birthDate")}
          type="date"
          value={birth}
          onValueChange={setBirth}
          autoComplete="bday"
          max={maxBirth}
          hint={t("auth.birthHint", { n: MIN_AGE })}
          error={tooYoung ? t("auth.tooYoung", { n: MIN_AGE }) : fieldErrors.date_of_birth}
          required
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
            {t("auth.honeypot")}
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
            {t("auth.ageTerms", { n: MIN_AGE })}{" "}
            <Link href="/terms" target="_blank" className="text-emerald-300 underline">
              {t("auth.termsLink")}
            </Link>{" "}
            ·{" "}
            <Link href="/privacy" target="_blank" className="text-emerald-300 underline">
              {t("auth.privacyLink")}
            </Link>
          </span>
        </label>

        <TurnstileWidget onVerify={onCaptcha} />

        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 transition hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "..." : t("auth.signup")}
        </button>
      </form>

      {status && !status.ok && (
        <p className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {status.msg}
        </p>
      )}
      <p className="mt-6 text-sm text-neutral-400">
        {t("auth.haveAccount")}{" "}
        <Link href="/login" className="text-emerald-300 underline">
          {t("nav.login")}
        </Link>
      </p>
    </main>
  );
}

type FieldProps = {
  label: string;
  type: string;
  value: string;
  onValueChange: (v: string) => void;
  hint?: string;
  error?: string;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type">;

function Field({ label, type, value, onValueChange, hint, error, ...rest }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        aria-invalid={error ? true : undefined}
        className={`w-full rounded-lg border bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-secondary-light ${
          error ? "border-red-500/70" : "border-neutral-700"
        }`}
        {...rest}
      />
      {error ? (
        <span className="mt-1 block text-xs text-red-300">{error}</span>
      ) : (
        hint && <span className="mt-1 block text-xs text-neutral-500">{hint}</span>
      )}
    </label>
  );
}
