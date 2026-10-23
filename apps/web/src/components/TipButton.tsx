"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { notifyWalletChanged } from "@/lib/wallet-events";

const MIN_TIP = 10;
const PRESETS = [10, 50, 100, 500];

export function TipButton({ channelSlug }: { channelSlug: string }) {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState(String(MIN_TIP));
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  // Une clé par TENTATIVE : réutilisée si l'utilisateur re-clique (double clic,
  // réseau lent) → le serveur ne débite qu'une fois. Régénérée après succès.
  const attemptKey = useRef<string | null>(null);

  async function send() {
    const aura = parseInt(amount, 10);
    if (!aura || aura < MIN_TIP) {
      setError(t("tip.min", { n: MIN_TIP }));
      return;
    }
    if (busy) return;
    setBusy(true);
    setError(null);
    attemptKey.current ??= idempotencyKey();
    try {
      await authFetch("/api/payments/tip", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug, aura_amount: aura, message }),
        headers: { "Idempotency-Key": attemptKey.current },
      });
      attemptKey.current = null;
      setSent(true);
      setOpen(false);
      setMessage("");
      notifyWalletChanged();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("tip.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex h-9 items-center rounded-md bg-amber-500 px-3 text-sm font-semibold text-neutral-950 hover:bg-amber-400"
      >
        {t("tip.button")} {sent ? "✓" : ""}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          {!user ? (
            <p className="text-sm text-neutral-300">
              <Link href="/login" className="text-emerald-300 underline">
                {t("tip.login")}
              </Link>{" "}
              {t("tip.loginSuffix")}
            </p>
          ) : (
            <>
              <div className="flex gap-1.5">
                {PRESETS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => {
                      setAmount(String(p));
                      attemptKey.current = null;
                    }}
                    className={`flex-1 rounded-md border px-2 py-1 text-xs font-semibold ${
                      amount === String(p)
                        ? "border-amber-400 bg-amber-500/15 text-amber-300"
                        : "border-neutral-700 text-neutral-300 hover:border-neutral-500"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <input
                type="number"
                min={MIN_TIP}
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  attemptKey.current = null;
                }}
                aria-label={t("tip.amount")}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={t("tip.message")}
                maxLength={200}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              <p className="text-[11px] text-neutral-500">{t("tip.split")}</p>
              {error && <p className="text-xs text-red-300">{error}</p>}
              <button
                type="button"
                onClick={send}
                disabled={busy}
                className="w-full rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-amber-400 disabled:opacity-50"
              >
                {busy ? t("tip.sending") : t("tip.send")}
              </button>
              <Link
                href="/wallet"
                className="block text-center text-xs text-neutral-500 hover:text-neutral-300"
              >
                {t("tip.wallet")}
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  );
}
