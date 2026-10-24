"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch, idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { notifyWalletChanged } from "@/lib/wallet-events";
import { Sparkles } from "lucide-react";

type TierResp = { price_aura?: number; perks?: string[] };
type StatusResp = {
  subscribed: boolean;
  current_period_end: string | null;
  will_renew: boolean;
  cancel_at_period_end: boolean;
  price_paid: number | null;
};

export function SubscribeButton({ channelSlug }: { channelSlug: string }) {
  const t = useT();
  const { date } = useFormat();
  const { user, authFetch } = useAuth();
  const [price, setPrice] = useState<number | null>(null);
  const [perks, setPerks] = useState<string[]>([]);
  const [status, setStatus] = useState<StatusResp | null>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const attemptKey = useRef<string | null>(null);

  useEffect(() => {
    apiFetch<TierResp>(`/api/channels/${channelSlug}/tier`)
      .then((d) => {
        if (typeof d.price_aura === "number") {
          setPrice(d.price_aura);
          setPerks(d.perks ?? []);
        }
      })
      .catch(() => undefined);
  }, [channelSlug]);

  const loadStatus = useCallback(() => {
    if (!user) return;
    authFetch<StatusResp>(`/api/subscriptions/${channelSlug}/status`)
      .then(setStatus)
      .catch(() => undefined);
  }, [user, channelSlug, authFetch]);

  useEffect(loadStatus, [loadStatus]);

  const act = useCallback(
    async (fn: () => Promise<unknown>) => {
      if (busy) return;
      setBusy(true);
      setError(null);
      try {
        await fn();
        loadStatus();
        notifyWalletChanged();
        setOpen(false);
      } catch (err) {
        const e = err as { data?: { detail?: string } };
        setError(e.data?.detail ?? t("sub.error"));
      } finally {
        setBusy(false);
      }
    },
    [busy, loadStatus, t],
  );

  const subscribe = () =>
    act(async () => {
      attemptKey.current ??= idempotencyKey();
      await authFetch("/api/subscriptions", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug }),
        headers: { "Idempotency-Key": attemptKey.current },
      });
      attemptKey.current = null;
    });
  const cancel = () =>
    act(() => authFetch(`/api/subscriptions/${channelSlug}`, { method: "DELETE" }));
  const resume = () =>
    act(() => authFetch(`/api/subscriptions/${channelSlug}/resume`, { method: "POST" }));

  if (price === null) return null;

  if (!user) {
    return (
      <Link
        href="/login"
        className="flex h-9 items-center gap-1.5 rounded-md bg-secondary px-4 text-sm font-semibold text-neutral-950 hover:bg-secondary-light"
      >
        <SparkleIcon />
        {t("sub.subscribe", { price })}
      </Link>
    );
  }

  const subscribed = Boolean(status?.subscribed);
  const until = status?.current_period_end ? date(status.current_period_end) : "";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex h-9 items-center gap-1.5 rounded-md px-4 text-sm font-semibold ${
          subscribed
            ? "bg-secondary/20 text-secondary-light hover:bg-secondary/30"
            : "bg-secondary text-neutral-950 hover:bg-secondary-light"
        }`}
      >
        <SparkleIcon />
        {subscribed ? t("sub.subscribed") : t("sub.subscribe", { price })}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          {subscribed ? (
            <>
              <p className="text-xs text-neutral-300">
                {status?.will_renew
                  ? t("sub.renewsOn", { date: until, price: status?.price_paid ?? price })
                  : t("sub.endsOn", { date: until })}
              </p>
              <button
                type="button"
                onClick={subscribe}
                disabled={busy}
                className="w-full rounded-lg bg-secondary px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-secondary-light disabled:opacity-50"
              >
                {t("sub.extend", { price })}
              </button>
              {status?.will_renew ? (
                <button
                  type="button"
                  onClick={cancel}
                  disabled={busy}
                  className="w-full rounded-lg border border-neutral-700 px-3 py-1.5 text-sm text-neutral-300 hover:border-red-400 hover:text-red-300 disabled:opacity-50"
                >
                  {t("sub.cancelRenewal")}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={resume}
                  disabled={busy}
                  className="w-full rounded-lg border border-neutral-700 px-3 py-1.5 text-sm text-neutral-300 hover:border-secondary disabled:opacity-50"
                >
                  {t("sub.resume")}
                </button>
              )}
            </>
          ) : (
            <>
              <p className="text-xs text-neutral-400">{t("sub.perMonth", { price })}</p>
              {perks.length > 0 && (
                <ul className="list-inside list-disc text-xs text-neutral-300">
                  {perks.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              )}
              <p className="text-[11px] text-neutral-500">{t("sub.autoRenewNotice")}</p>
              <button
                type="button"
                onClick={subscribe}
                disabled={busy}
                className="w-full rounded-lg bg-secondary px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-secondary-light disabled:opacity-50"
              >
                {t("sub.confirm")}
              </button>
            </>
          )}
          {error && (
            <p className="text-xs text-red-300">
              {error}{" "}
              <Link href="/wallet" className="underline">
                {t("sub.topup")}
              </Link>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function SparkleIcon() {
  return <Sparkles size={14} aria-hidden />;
}
