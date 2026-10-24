"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { LevelBadge } from "@/components/LevelBadge";
import { useMyLevel } from "@/lib/use-level";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { onWalletChanged } from "@/lib/wallet-events";

/** Solde Aura du spectateur sous la saisie du chat (badge du palier + montant). */
export function ChatAuraFooter() {
  const t = useT();
  const { num } = useFormat();
  const { user, loading, authFetch } = useAuth();
  const [balance, setBalance] = useState<number | null>(null);
  const level = useMyLevel();

  const refresh = useCallback(() => {
    authFetch<{ aura_balance: number }>("/api/payments/wallet")
      .then((d) => setBalance(d.aura_balance))
      .catch(() => setBalance(null));
  }, [authFetch]);

  useEffect(() => {
    if (loading || !user) return;
    refresh();
    return onWalletChanged(refresh);
  }, [loading, user, refresh]);

  if (!user) {
    return (
      <Link href="/login" className="text-xs text-neutral-400 hover:text-emerald-300">
        {t("nav.login")}
      </Link>
    );
  }

  return (
    <Link
      href="/wallet"
      title={level ? t("level.title", { level: t(`level.${level.level}`) }) : t("nav.aura")}
      className="flex items-center gap-1.5 rounded-md px-1.5 py-1 text-xs font-semibold text-neutral-200 hover:bg-neutral-800"
    >
      <LevelBadge level={level?.level} size={18} />
      <span className="tabular-nums">{balance === null ? "—" : num(balance)}</span>
      <span className="text-neutral-500">Aura</span>
    </Link>
  );
}
