"use client";

import Link from "next/link";
import { GUIDE_ICONS } from "@/lib/guides";
import { useGuides } from "@/lib/use-guides";
import { useI18n, useT } from "@/lib/i18n";
import { useGuideProgress } from "@/lib/use-guide-progress";

export default function GuidesPage() {
  const { locale } = useI18n();
  const t = useT();
  const { completed } = useGuideProgress();
  const guides = useGuides(locale);

  const totalSteps = guides.reduce((n, g) => n + g.steps.length, 0);
  const doneSteps = guides.reduce(
    (n, g) => n + g.steps.filter((s) => completed.has(`${g.slug}:${s.id}`)).length,
    0,
  );
  const globalPct = totalSteps ? Math.round((doneSteps / totalSteps) * 100) : 0;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t("guides.title")}</h1>
          <p className="mt-1 text-sm text-neutral-400">{t("guides.subtitle")}</p>
        </div>
        <div className="min-w-[200px]">
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="text-neutral-400">{t("guides.globalProgress")}</span>
            <span className="font-semibold text-emerald-300">{globalPct}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-800">
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${globalPct}%` }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {guides.map((g) => {
          const total = g.steps.length;
          const done = g.steps.filter((s) => completed.has(`${g.slug}:${s.id}`)).length;
          const pct = total ? Math.round((done / total) * 100) : 0;
          const complete = done === total && total > 0;
          return (
            <Link
              key={g.slug}
              href={`/guides/${g.slug}`}
              className="group rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 transition hover:border-emerald-500/50"
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                    complete ? "bg-emerald-500/20 text-emerald-300" : "bg-neutral-800 text-neutral-300"
                  }`}
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <path d={GUIDE_ICONS[g.icon] ?? GUIDE_ICONS.rocket} />
                  </svg>
                </span>
                <div className="min-w-0 flex-1">
                  <h2 className="font-semibold text-neutral-100 group-hover:text-emerald-300">{g.title}</h2>
                  <p className="mt-0.5 text-sm text-neutral-400">{g.desc}</p>
                </div>
                {complete && <span className="shrink-0 text-emerald-300">✓</span>}
              </div>
              <div className="mt-4 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-neutral-800">
                  <div className="h-full rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs text-neutral-500">
                  {done}/{total}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
