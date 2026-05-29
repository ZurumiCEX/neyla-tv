"use client";

import { use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getGuide, getGuides } from "@/lib/guides";
import { useI18n, useT } from "@/lib/i18n";
import { useGuideProgress } from "@/lib/use-guide-progress";

export default function GuideDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { locale } = useI18n();
  const t = useT();
  const { completed, toggle, isAuthed } = useGuideProgress();

  const guide = getGuide(locale, slug);
  if (!guide) notFound();

  const all = getGuides(locale);
  const idx = all.findIndex((g) => g.slug === slug);
  const next = all[idx + 1];

  const done = guide.steps.filter((s) => completed.has(`${guide.slug}:${s.id}`)).length;
  const total = guide.steps.length;
  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <Link href="/guides" className="text-sm text-neutral-400 hover:text-emerald-300">
        ← {t("guides.title")}
      </Link>

      <div className="mt-3 mb-6">
        <h1 className="text-2xl font-bold">{guide.title}</h1>
        <p className="mt-1 text-sm text-neutral-400">{guide.desc}</p>
        <div className="mt-4 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-neutral-800">
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-sm font-semibold text-emerald-300">
            {done}/{total}
          </span>
        </div>
      </div>

      {!isAuthed && (
        <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-300">
          {t("guides.loginHint")}
        </p>
      )}

      <ol className="space-y-3">
        {guide.steps.map((s, i) => {
          const key = `${guide.slug}:${s.id}`;
          const checked = completed.has(key);
          return (
            <li
              key={s.id}
              className={`rounded-2xl border p-4 transition ${
                checked
                  ? "border-emerald-500/40 bg-emerald-500/5"
                  : "border-neutral-800 bg-neutral-900/60"
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  disabled={!isAuthed}
                  onClick={() => toggle(key, !checked)}
                  aria-pressed={checked}
                  className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition ${
                    checked
                      ? "border-emerald-500 bg-emerald-500 text-neutral-950"
                      : "border-neutral-600 text-transparent hover:border-emerald-500"
                  } disabled:opacity-50`}
                >
                  ✓
                </button>
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 font-semibold text-neutral-100">
                    <span className="text-xs text-neutral-500">{i + 1}.</span>
                    {s.title}
                  </p>
                  <p className="mt-1 text-sm text-neutral-300">{s.body}</p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      {pct === 100 && (
        <div className="mt-6 rounded-2xl border border-emerald-500/40 bg-emerald-500/5 p-4 text-center">
          <p className="font-semibold text-emerald-300">{t("guides.completed")}</p>
          {next && (
            <Link
              href={`/guides/${next.slug}`}
              className="mt-2 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
            >
              {t("guides.next")}: {next.title}
            </Link>
          )}
        </div>
      )}
    </main>
  );
}
