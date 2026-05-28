"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

type TierResp = { price_aura?: number; perks?: string[] };

export function SubscribeButton({ channelSlug }: { channelSlug: string }) {
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
      setError(e.data?.detail ?? "Échec de l'abonnement.");
    }
  }, [authFetch, channelSlug]);

  if (price === null) return null;

  if (subscribed) {
    return (
      <span className="rounded-md bg-fuchsia-500/20 px-3 py-1 text-sm font-semibold text-fuchsia-300">
        Abonné ✓
      </span>
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="rounded-md bg-fuchsia-500 px-3 py-1 text-sm font-semibold text-neutral-950 hover:bg-fuchsia-400"
      >
        S&apos;abonner · {price} Aura
      </Link>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-md bg-fuchsia-500 px-3 py-1 text-sm font-semibold text-neutral-950 hover:bg-fuchsia-400"
      >
        S&apos;abonner · {price} Aura
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          <p className="text-xs text-neutral-400">{price} Aura / mois</p>
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
                Recharger
              </Link>
            </p>
          )}
          <button
            type="button"
            onClick={subscribe}
            className="w-full rounded-lg bg-fuchsia-500 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-fuchsia-400"
          >
            Confirmer
          </button>
        </div>
      )}
    </div>
  );
}
