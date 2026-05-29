"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type TierResp = { price_aura?: number; perks?: string[] };

export function SubscribeButton({ channelSlug }: { channelSlug: string }) {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [price, setPrice] = useState<number | null>(null);
  const [perks, setPerks] = useState<string[]>([]);
  const [subscribed, setSubscribed] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!user) return;
    authFetch<{ subscribed: boolean }>(`/api/subscriptions/${channelSlug}/status`)
      .then((d) => setSubscribed(d.subscribed))
      .catch(() => undefined);
  }, [user, channelSlug, authFetch]);

  const subscribe = useCallback(async () => {
    setError(null);
    try {
      await authFetch("/api/subscriptions", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug }),
      });
      setSubscribed(true);
      setOpen(false);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("sub.error"));
    }
  }, [authFetch, channelSlug, t]);

  if (price === null) return null;

  if (subscribed) {
    return (
      <span className="rounded-md bg-secondary/20 px-3 py-1 text-sm font-semibold text-secondary-light">
        {t("sub.subscribed")}
      </span>
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="flex items-center gap-1.5 rounded-md bg-secondary px-4 py-1.5 text-sm font-semibold text-white hover:bg-secondary-light"
      >
        <SparkleIcon />
        {t("sub.subscribe", { price })}
      </Link>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 rounded-md bg-secondary px-4 py-1.5 text-sm font-semibold text-white hover:bg-secondary-light"
      >
        <SparkleIcon />
        {t("sub.subscribe", { price })}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          <p className="text-xs text-neutral-400">{t("sub.perMonth", { price })}</p>
          {perks.length > 0 && (
            <ul className="list-inside list-disc text-xs text-neutral-300">
              {perks.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          )}
          {error && (
            <p className="text-xs text-red-300">
              {error}{" "}
              <Link href="/wallet" className="underline">
                {t("sub.topup")}
              </Link>
            </p>
          )}
          <button
            type="button"
            onClick={subscribe}
            className="w-full rounded-lg bg-secondary px-3 py-1.5 text-sm font-semibold text-white hover:bg-secondary-light"
          >
            {t("sub.confirm")}
          </button>
        </div>
      )}
    </div>
  );
}

function SparkleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8L12 2z" />
      <path d="M19 14l.9 2.6L22 17.5l-2.1.9L19 21l-.9-2.6L16 17.5l2.1-.9L19 14z" />
    </svg>
  );
}
