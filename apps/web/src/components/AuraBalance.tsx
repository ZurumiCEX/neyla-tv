"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export function AuraBalance() {
  const { user, loading, authFetch } = useAuth();
  const t = useT();
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    if (loading || !user) return;
    authFetch<{ aura_balance: number }>("/api/payments/wallet")
      .then((d) => setBalance(d.aura_balance))
      .catch(() => setBalance(null));
  }, [loading, user, authFetch]);

  return (
    <Link
      href="/wallet"
      aria-label={t("nav.aura")}
      title={t("nav.aura")}
      className="flex h-9 items-center gap-1.5 rounded-full bg-neutral-900 px-2.5 text-amber-300 hover:bg-neutral-800"
    >
      <AuraIcon />
      <span className="text-xs font-semibold tabular-nums">
        {balance === null ? t("nav.aura") : balance.toLocaleString("fr-FR")}
      </span>
    </Link>
  );
}

function AuraIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
    </svg>
  );
}
