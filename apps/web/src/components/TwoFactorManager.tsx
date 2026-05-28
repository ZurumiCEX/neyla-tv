"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { CopyButton } from "@/components/CopyButton";
import { QrCode } from "@/components/QrCode";

type Setup = { secret: string; otpauth_uri: string };

export function TwoFactorManager() {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [enabled, setEnabled] = useState(Boolean(user?.two_factor_enabled));
  const [setup, setSetup] = useState<Setup | null>(null);
  const [code, setCode] = useState("");
  const [recovery, setRecovery] = useState<string[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startSetup() {
    setBusy(true);
    setError(null);
    try {
      setSetup(await authFetch<Setup>("/api/auth/2fa/setup", { method: "POST" }));
    } catch {
      setError(t("common.loadError"));
    } finally {
      setBusy(false);
    }
  }

  async function confirmEnable() {
    setBusy(true);
    setError(null);
    try {
      const res = await authFetch<{ recovery_codes: string[] }>("/api/auth/2fa/enable", {
        method: "POST",
        body: JSON.stringify({ code: code.trim() }),
      });
      setRecovery(res.recovery_codes);
      setEnabled(true);
      setSetup(null);
      setCode("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("auth.2fa.invalid"));
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/auth/2fa/disable", {
        method: "POST",
        body: JSON.stringify({ code: code.trim() }),
      });
      setEnabled(false);
      setCode("");
      setRecovery(null);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("auth.2fa.invalid"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">{t("twofa.title")}</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            enabled ? "bg-emerald-500/15 text-emerald-300" : "bg-neutral-800 text-neutral-400"
          }`}
        >
          {enabled ? t("twofa.on") : t("twofa.off")}
        </span>
      </div>
      <p className="mb-4 text-sm text-neutral-400">{t("twofa.desc")}</p>

      {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

      {recovery && (
        <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
          <p className="mb-2 text-sm font-semibold text-amber-300">{t("twofa.recoveryTitle")}</p>
          <p className="mb-2 text-xs text-neutral-400">{t("twofa.recoveryDesc")}</p>
          <div className="grid grid-cols-2 gap-1 font-mono text-sm text-neutral-200">
            {recovery.map((c) => (
              <span key={c}>{c}</span>
            ))}
          </div>
        </div>
      )}

      {!enabled && !setup && (
        <button
          type="button"
          onClick={startSetup}
          disabled={busy}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {t("twofa.enable")}
        </button>
      )}

      {!enabled && setup && (
        <div className="space-y-3">
          <p className="text-sm text-neutral-300">{t("twofa.setupHint")}</p>
          <div className="flex flex-wrap items-center gap-4">
            <div className="rounded-xl bg-white p-2">
              <QrCode value={setup.otpauth_uri} />
            </div>
            <div className="min-w-0 flex-1 space-y-2">
              <p className="text-xs text-neutral-500">{t("twofa.manualKey")}</p>
              <div className="flex items-center gap-2 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2">
                <code className="break-all text-sm text-emerald-300">{setup.secret}</code>
                <CopyButton value={setup.secret} />
              </div>
            </div>
          </div>
          <input
            inputMode="numeric"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            className="w-40 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-center tracking-widest text-neutral-100 outline-none focus:border-emerald-500"
          />
          <button
            type="button"
            onClick={confirmEnable}
            disabled={busy}
            className="ml-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {t("twofa.confirm")}
          </button>
        </div>
      )}

      {enabled && (
        <div className="flex items-center gap-2">
          <input
            inputMode="numeric"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={t("twofa.codeOrRecovery")}
            className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-red-500"
          />
          <button
            type="button"
            onClick={disable}
            disabled={busy}
            className="rounded-lg border border-red-500/40 px-4 py-2 text-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
          >
            {t("twofa.disable")}
          </button>
        </div>
      )}
    </section>
  );
}
