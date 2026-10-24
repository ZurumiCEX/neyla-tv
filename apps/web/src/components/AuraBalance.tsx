"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { onWalletChanged } from "@/lib/wallet-events";
import { LevelBadge } from "@/components/LevelBadge";
import { useMyLevel } from "@/lib/use-level";
import { Sparkles } from "lucide-react";

export function AuraBalance() {
  const { user, loading, authFetch } = useAuth();
  const t = useT();
  const { num } = useFormat();
  const [balance, setBalance] = useState<number | null>(null);

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

  const level = useMyLevel();

  return (
    <Link
      href="/wallet"
      aria-label={t("nav.aura")}
      title={level ? t("level.title", { level: t(`level.${level.level}`) }) : t("nav.aura")}
      className="flex h-9 items-center gap-1.5 rounded-full bg-neutral-900 px-2.5 text-amber-300 hover:bg-neutral-800"
    >
      {level ? <LevelBadge level={level.level} size={20} /> : <AuraIcon />}
      <span className="text-xs font-semibold tabular-nums">
        {balance === null ? t("nav.aura") : num(balance)}
      </span>
    </Link>
  );
}

function AuraIcon() {
  return <Sparkles size={16} aria-hidden />;
}
