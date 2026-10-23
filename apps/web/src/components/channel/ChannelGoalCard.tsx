"use client";

import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

export type ChannelGoal = { title: string; kind: "subs" | "tips"; target: number; current: number };

const FOLLOWER_MILESTONES = [10, 50, 100, 500, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000];

/** Objectif du streamer, ou à défaut le prochain palier d'abonnés (followers). */
export function ChannelGoalCard({
  goal,
  followers,
}: {
  goal: ChannelGoal | null;
  followers: number;
}) {
  const t = useT();
  const { num } = useFormat();

  let label: string;
  let current: number;
  let target: number;
  let unit: string;
  if (goal && goal.target > 0) {
    label = goal.title || t(goal.kind === "tips" ? "channel.goal.tips" : "channel.goal.subs");
    current = goal.current;
    target = goal.target;
    unit = goal.kind === "tips" ? "Aura" : t("channel.goal.subsUnit");
  } else {
    target =
      FOLLOWER_MILESTONES.find((m) => m > followers) ??
      Math.ceil((followers + 1) / 100_000) * 100_000;
    current = followers;
    label = t("channel.goal.followersLeft", { n: num(target - followers) });
    unit = t("channel.followers");
  }
  const pct = Math.min(100, Math.round((current / Math.max(target, 1)) * 100));

  return (
    <section className="rounded-xl bg-neutral-900 p-4 sm:p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-bold">{label}</h2>
        <span className="shrink-0 text-sm tabular-nums text-neutral-300">
          <span className="font-semibold text-neutral-100">{num(current)}</span> / {num(target)}{" "}
          <span className="text-neutral-500">{unit}</span>
        </span>
      </div>
      <div
        className="mt-3 h-3 overflow-hidden rounded-full bg-neutral-800"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="goal-stripes h-full rounded-full bg-emerald-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-neutral-500">{pct} %</p>
    </section>
  );
}
