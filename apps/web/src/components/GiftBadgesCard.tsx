"use client";

import Link from "next/link";
import { GIFT_TIERS, GiftBadge } from "@/components/GiftBadge";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

/** Les 5 badges de don : ce qu'un follower a offert au total à une même chaîne. */
export function GiftBadgesCard() {
  const t = useT();
  const { num } = useFormat();
  const { user } = useAuth();
  return (
    <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 sm:p-5">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-neutral-300">
            {t("gift.badges.title")}
          </h2>
          <p className="text-xs text-neutral-500">{t("gift.badges.desc")}</p>
        </div>
        {user && (
          <Link
            href={`/u/${user.username}`}
            className="text-xs font-semibold text-emerald-300 hover:underline"
          >
            {t("gift.badges.mine")}
          </Link>
        )}
      </div>
      <ol className="grid grid-cols-5 gap-2 sm:gap-3">
        {GIFT_TIERS.map((tier) => (
          <li key={tier.key} className="flex flex-col items-center text-center">
            <span className="flex h-12 items-center sm:h-14">
              <GiftBadge tier={tier} size={44} />
            </span>
            <span
              className="mt-2 text-xs font-bold tabular-nums sm:text-sm"
              style={{ color: tier.color }}
            >
              {num(tier.min)}
              <span className="hidden sm:inline"> Aura</span>
            </span>
            <span className="mt-0.5 hidden text-[11px] text-neutral-500 sm:block">
              {t(`gift.tier.${tier.key}`)}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
