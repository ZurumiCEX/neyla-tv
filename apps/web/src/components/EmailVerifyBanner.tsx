"use client";

// Bandeau « vérifie ton e-mail » pour un compte connecté non vérifié, avec renvoi.

import { useEffect, useState } from "react";
import { apiErrorMessage } from "@/lib/api-errors";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

const DISMISS_KEY = "neyla:verify-banner-dismissed";

export function EmailVerifyBanner() {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);
  const [welcome, setWelcome] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setWelcome(new URLSearchParams(window.location.search).get("welcome") === "1");
    try {
      setDismissed(sessionStorage.getItem(DISMISS_KEY) === "1");
    } catch {
      /* stockage indisponible */
    }
  }, []);

  if (!user || user.is_email_verified || dismissed) return null;

  async function resend() {
    setState("sending");
    setError(null);
    try {
      await authFetch("/api/auth/email/resend", { method: "POST" });
      setState("sent");
    } catch (err) {
      setError(apiErrorMessage(err, t, "verify.resendError"));
      setState("idle");
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
      <span className="font-semibold">
        {welcome ? t("verify.welcome", { name: user.display_name || user.username }) : ""}
      </span>
      <span>{t("verify.prompt", { email: user.email })}</span>
      {state === "sent" ? (
        <span className="text-emerald-300">{t("verify.sent")}</span>
      ) : (
        <button
          type="button"
          onClick={resend}
          disabled={state === "sending"}
          className="rounded-md border border-amber-400/60 px-2 py-0.5 text-xs font-semibold hover:bg-amber-500/20 disabled:opacity-50"
        >
          {t("verify.resend")}
        </button>
      )}
      {error && <span className="text-red-300">{error}</span>}
      <button
        type="button"
        onClick={() => {
          setDismissed(true);
          try {
            sessionStorage.setItem(DISMISS_KEY, "1");
          } catch {
            /* stockage indisponible */
          }
        }}
        aria-label={t("verify.dismiss")}
        className="ml-auto text-amber-300 hover:text-amber-100"
      >
        ×
      </button>
    </div>
  );
}
