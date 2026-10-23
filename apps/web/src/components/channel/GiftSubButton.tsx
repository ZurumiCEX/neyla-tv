"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { apiErrorMessage } from "@/lib/api-errors";
import { notifyWalletChanged } from "@/lib/wallet-events";

/** « Offrir un abonnement » : pseudo du destinataire → POST /api/subscriptions/gift. */
export function GiftSubButton({ channelSlug }: { channelSlug: string }) {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [open, setOpen] = useState(false);
  const [recipient, setRecipient] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  if (user?.username === channelSlug) return null;

  const button = (
    <>
      <GiftIcon />
      <span className="hidden sm:inline">{t("gift.button")}</span>
    </>
  );
  const cls =
    "flex h-9 items-center gap-1.5 rounded-md bg-neutral-800 px-3 text-sm font-semibold text-neutral-100 hover:bg-neutral-700";

  if (!user) {
    return (
      <Link href="/login" className={cls} title={t("gift.button")}>
        {button}
      </Link>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const name = recipient.trim().replace(/^@/, "");
    if (!name || busy) return;
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/subscriptions/gift", {
        method: "POST",
        body: JSON.stringify({ channel_slug: channelSlug, recipient: name }),
      });
      setDone(name);
      setRecipient("");
      notifyWalletChanged();
    } catch (err) {
      setError(apiErrorMessage(err, t, "gift.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          setDone(null);
          setError(null);
        }}
        className={cls}
        title={t("gift.button")}
      >
        {button}
      </button>
      {open && (
        <form
          onSubmit={submit}
          className="absolute right-0 z-50 mt-2 w-72 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl"
        >
          <p className="text-sm font-semibold">{t("gift.title")}</p>
          <p className="text-xs text-neutral-400">{t("gift.hint")}</p>
          <input
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder={t("gift.placeholder")}
            maxLength={40}
            autoFocus
            className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-400"
          />
          {error && <p className="text-xs text-red-300">{error}</p>}
          {done && <p className="text-xs text-green-300">{t("gift.done", { name: done })}</p>}
          <button
            type="submit"
            disabled={busy || !recipient.trim()}
            className="w-full rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-bold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {busy ? "…" : t("gift.submit")}
          </button>
        </form>
      )}
    </div>
  );
}

function GiftIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="3" y="8" width="18" height="4" rx="1" />
      <path d="M12 8v13M19 12v9H5v-9M7.5 8a2.5 2.5 0 010-5C10 3 12 8 12 8s2-5 4.5-5a2.5 2.5 0 010 5" />
    </svg>
  );
}
