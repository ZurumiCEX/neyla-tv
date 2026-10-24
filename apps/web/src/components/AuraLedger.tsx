"use client";

import {
  ArrowUpRight,
  Circle,
  Heart,
  HeartHandshake,
  Plus,
  Star,
  Undo2,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

export type LedgerEntry = {
  amount: number;
  kind: string;
  reference: string;
  balance_after: number;
  created_at: string;
};

// Icône et teinte par type d'opération.
const KIND_META: Record<string, { Icon: LucideIcon; tone: string }> = {
  purchase: { Icon: Plus, tone: "bg-emerald-500/15 text-emerald-300" },
  tip_sent: { Icon: Heart, tone: "bg-pink-500/15 text-pink-300" },
  tip_received: { Icon: Heart, tone: "bg-green-500/15 text-green-300" },
  sub_paid: { Icon: Star, tone: "bg-violet-500/15 text-violet-300" },
  sub_earned: { Icon: Star, tone: "bg-green-500/15 text-green-300" },
  payout: { Icon: ArrowUpRight, tone: "bg-sky-500/15 text-sky-300" },
  payout_reversal: { Icon: Undo2, tone: "bg-sky-500/15 text-sky-300" },
  refund: { Icon: Undo2, tone: "bg-neutral-500/20 text-neutral-300" },
  referral: { Icon: Users, tone: "bg-amber-500/15 text-amber-300" },
  charity_donation: { Icon: HeartHandshake, tone: "bg-red-500/15 text-red-300" },
};
const DEFAULT_META = { Icon: Circle, tone: "bg-neutral-500/20 text-neutral-300" };

/** Historique Aura regroupé par jour : icône par type, montants colorés. */
export function AuraLedger({ entries }: { entries: LedgerEntry[] }) {
  const t = useT();
  const { num, date, time } = useFormat();

  const dayKey = (iso: string) => new Date(iso).toDateString();
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86_400_000).toDateString();
  const groups: { key: string; label: string; items: LedgerEntry[] }[] = [];
  for (const e of entries) {
    const key = dayKey(e.created_at);
    let group = groups[groups.length - 1];
    if (!group || group.key !== key) {
      const label =
        key === today
          ? t("wallet.history.today")
          : key === yesterday
            ? t("wallet.history.yesterday")
            : date(e.created_at, { weekday: "long", day: "numeric", month: "long" });
      group = { key, label, items: [] };
      groups.push(group);
    }
    group.items.push(e);
  }

  return (
    <div className="space-y-5">
      {groups.map((g) => (
        <section key={g.key}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            {g.label}
          </h3>
          <ul className="divide-y divide-neutral-800 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/60">
            {g.items.map((l, i) => {
              const meta = KIND_META[l.kind] ?? DEFAULT_META;
              const credit = l.amount >= 0;
              return (
                <li key={`${l.created_at}-${i}`} className="flex items-center gap-3 px-3 py-2.5">
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${meta.tone}`}
                  >
                    <meta.Icon size={16} aria-hidden />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-neutral-100">
                      {t(`wallet.kind.${l.kind}`)}
                    </p>
                    <p className="text-xs text-neutral-500">{time(l.created_at)}</p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-sm font-bold tabular-nums ${
                        credit ? "text-green-400" : "text-red-300"
                      }`}
                    >
                      {credit ? "+" : "−"}
                      {num(Math.abs(l.amount))}
                    </p>
                    <p className="text-[11px] tabular-nums text-neutral-500">
                      {t("wallet.history.balance", { n: num(l.balance_after) })}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
