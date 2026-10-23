"use client";

import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

export type LedgerEntry = {
  amount: number;
  kind: string;
  reference: string;
  balance_after: number;
  created_at: string;
};

// Icône (tracé 24x24) et teinte par type d'opération.
const KIND_META: Record<string, { path: string; tone: string }> = {
  purchase: { path: "M12 5v14M5 12h14", tone: "bg-emerald-500/15 text-emerald-300" },
  tip_sent: {
    path: "M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 000-7.8z",
    tone: "bg-pink-500/15 text-pink-300",
  },
  tip_received: {
    path: "M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 000-7.8z",
    tone: "bg-green-500/15 text-green-300",
  },
  sub_paid: {
    path: "M12 2l3 6.5 7 .8-5.2 4.8 1.4 7L12 17.6 5.8 21l1.4-7L2 9.3l7-.8z",
    tone: "bg-violet-500/15 text-violet-300",
  },
  sub_earned: {
    path: "M12 2l3 6.5 7 .8-5.2 4.8 1.4 7L12 17.6 5.8 21l1.4-7L2 9.3l7-.8z",
    tone: "bg-green-500/15 text-green-300",
  },
  payout: { path: "M12 19V5M5 12l7-7 7 7", tone: "bg-sky-500/15 text-sky-300" },
  payout_reversal: {
    path: "M9 14L4 9l5-5M4 9h11a5 5 0 010 10h-3",
    tone: "bg-sky-500/15 text-sky-300",
  },
  refund: {
    path: "M9 14L4 9l5-5M4 9h11a5 5 0 010 10h-3",
    tone: "bg-neutral-500/20 text-neutral-300",
  },
  referral: {
    path: "M16 21v-2a4 4 0 00-8 0v2M12 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M2 21v-2a4 4 0 013-3.9",
    tone: "bg-amber-500/15 text-amber-300",
  },
  charity_donation: {
    path: "M12 21s-7-4.4-9.3-9A5 5 0 0112 6.5 5 5 0 0121.3 12C19 16.6 12 21 12 21z",
    tone: "bg-red-500/15 text-red-300",
  },
};
const DEFAULT_META = { path: "M4 12h16M12 4v16", tone: "bg-neutral-500/20 text-neutral-300" };

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
                      <path d={meta.path} />
                    </svg>
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
