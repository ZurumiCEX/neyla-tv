"use client";

import { AURA_TIERS, AuraBadge, auraTier, nextAuraTier } from "@/components/AuraBadge";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

/** Les 5 paliers Aura (1 → 10 000) : palier actuel mis en avant, progression vers le suivant. */
export function AuraTierLadder({ balance, masked = false }: { balance: number; masked?: boolean }) {
  const t = useT();
  const { num } = useFormat();
  const current = auraTier(balance);
  const next = nextAuraTier(balance);
  const from = current?.min ?? 0;
  const pct = next ? Math.min(100, Math.round(((balance - from) / (next.min - from)) * 100)) : 100;

  return (
    <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 sm:p-5">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-bold uppercase tracking-wider text-neutral-300">
          {t("aura.ladder.title")}
        </h2>
        <p className="text-xs text-neutral-400">
          {next
            ? t("aura.ladder.toNext", {
                n: masked ? "•••" : num(next.min - balance),
                tier: t(`aura.tier.${next.key}`),
              })
            : t("aura.ladder.max")}
        </p>
      </div>

      <ol className="grid grid-cols-5 gap-2 sm:gap-3">
        {AURA_TIERS.map((tier) => {
          const reached = balance >= tier.min;
          const isCurrent = current?.key === tier.key;
          return (
            <li
              key={tier.key}
              aria-current={isCurrent ? "step" : undefined}
              className={`flex flex-col items-center rounded-xl border px-1 py-3 text-center transition sm:px-2 ${
                isCurrent ? "bg-neutral-950" : "border-transparent"
              }`}
              style={
                isCurrent
                  ? { borderColor: tier.color, boxShadow: `0 0 18px -6px ${tier.glow}` }
                  : undefined
              }
            >
              <span className="flex h-12 items-center sm:h-16">
                <AuraBadge tier={tier} size={44} locked={!reached} animated={isCurrent} />
              </span>
              <span
                className="mt-2 text-xs font-bold tabular-nums sm:text-sm"
                style={{ color: reached ? tier.color : undefined }}
              >
                {num(tier.min)}
                <span className="hidden sm:inline"> Aura</span>
              </span>
              <span className="mt-0.5 hidden text-[11px] text-neutral-500 sm:block">
                {t(`aura.tier.${tier.key}`)}
              </span>
            </li>
          );
        })}
      </ol>

      {next && (
        <div className="mt-4">
          <div
            className="h-2 overflow-hidden rounded-full bg-neutral-800"
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-full rounded-full transition-[width] duration-700"
              style={{
                width: `${pct}%`,
                background: `linear-gradient(90deg, ${current?.color ?? "#525252"}, ${next.color})`,
              }}
            />
          </div>
        </div>
      )}
    </section>
  );
}
