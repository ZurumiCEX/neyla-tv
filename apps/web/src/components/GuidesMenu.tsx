"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useI18n, useT } from "@/lib/i18n";
import { getGuides } from "@/lib/guides";
import { useGuideProgress } from "@/lib/use-guide-progress";

export function GuidesMenu() {
  const { locale } = useI18n();
  const t = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const { completed } = useGuideProgress();
  const guides = getGuides(locale);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const totalSteps = guides.reduce((n, g) => n + g.steps.length, 0);
  const doneSteps = guides.reduce(
    (n, g) => n + g.steps.filter((s) => completed.has(`${g.slug}:${s.id}`)).length,
    0,
  );
  const globalPct = totalSteps ? Math.round((doneSteps / totalSteps) * 100) : 0;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={t("guides.menu")}
        title={t("guides.menu")}
        className="flex h-9 w-9 items-center justify-center rounded-full text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M4 5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2H6a2 2 0 01-2-2z" />
          <path d="M13 3v5h5M8 13h6M8 17h6" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <div className="border-b border-neutral-800 px-4 py-3">
            <p className="text-sm font-semibold text-neutral-100">{t("guides.title")}</p>
            <p className="mt-0.5 text-xs text-neutral-500">{t("guides.subtitle")}</p>
            <div className="mt-2 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-neutral-800">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${globalPct}%` }} />
              </div>
              <span className="text-xs font-semibold text-emerald-300">{globalPct}%</span>
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto py-1">
            {guides.map((g) => {
              const total = g.steps.length;
              const done = g.steps.filter((s) => completed.has(`${g.slug}:${s.id}`)).length;
              return (
                <Link
                  key={g.slug}
                  href={`/guides/${g.slug}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center justify-between gap-3 px-4 py-2.5 hover:bg-neutral-800"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm text-neutral-100">{g.title}</span>
                    <span className="block truncate text-xs text-neutral-500">
                      {done}/{total} {t("guides.steps")}
                    </span>
                  </span>
                  {done === total && total > 0 ? (
                    <span className="shrink-0 text-xs font-semibold text-emerald-300">100%</span>
                  ) : (
                    <span className="shrink-0 text-xs text-neutral-500">
                      {total ? Math.round((done / total) * 100) : 0}%
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
          <Link
            href="/guides"
            onClick={() => setOpen(false)}
            className="block border-t border-neutral-800 px-4 py-2.5 text-center text-sm font-semibold text-emerald-300 hover:bg-neutral-800"
          >
            {t("guides.seeAll")}
          </Link>
        </div>
      )}
    </div>
  );
}
