"use client";

import { useState } from "react";
import Link from "next/link";
import { idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export function TipButton({ channelSlug }: { channelSlug: string }) {
  const { user, authFetch } = useAuth();
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState("10");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function send() {
    const aura = parseInt(amount, 10);
    if (!aura || aura <= 0) return;
    setError(null);
    try {
      await authFetch("/api/payments/tip", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug, aura_amount: aura, message }),
        headers: { "Idempotency-Key": idempotencyKey() },
      });
      setSent(true);
      setOpen(false);
      setMessage("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec du tip.");
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-md bg-amber-500 px-3 py-1 text-sm font-semibold text-neutral-950 hover:bg-amber-400"
      >
        Aura {sent ? "✓" : ""}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          {!user ? (
            <p className="text-sm text-neutral-300">
              <Link href="/login" className="text-emerald-300 underline">
                Connecte-toi
              </Link>{" "}
              pour envoyer de l&apos;Aura.
            </p>
          ) : (
            <>
              <input
                type="number"
                min={1}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Message (optionnel)"
                maxLength={200}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              {error && <p className="text-xs text-red-300">{error}</p>}
              <button
                type="button"
                onClick={send}
                className="w-full rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-amber-400"
              >
                Envoyer l&apos;Aura
              </button>
              <Link href="/wallet" className="block text-center text-xs text-neutral-500 hover:text-neutral-300">
                Gérer mon portefeuille
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  );
}
