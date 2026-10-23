"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { LEGAL, LEGAL_NAV, LEGAL_UPDATED_AT, type LegalSlug } from "@/lib/legal-content";
import { useFormat } from "@/lib/use-format";

// Lien automatique des adresses e-mail présentes dans le texte.
const EMAIL_SPLIT = /([a-z0-9._-]+@neyla\.tv)/gi;
const IS_EMAIL = /^[a-z0-9._-]+@neyla\.tv$/i;

function withMailto(text: string) {
  return text.split(EMAIL_SPLIT).map((part, i) =>
    IS_EMAIL.test(part) ? (
      <a key={i} href={`mailto:${part}`} className="text-emerald-300 underline">
        {part}
      </a>
    ) : (
      part
    ),
  );
}

export function LegalDocument({ slug }: { slug: LegalSlug }) {
  const { locale, t } = useI18n();
  const { date } = useFormat();
  const doc = (LEGAL[locale] ?? LEGAL.fr)[slug];
  const nav = LEGAL[locale] ?? LEGAL.fr;

  return (
    <main className="w-full px-4 py-8">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[220px_1fr]">
        <nav aria-label={t("legal.nav")} className="lg:sticky lg:top-6 lg:self-start">
          <ul className="flex flex-wrap gap-2 lg:flex-col lg:gap-1">
            {LEGAL_NAV.map((s) => (
              <li key={s}>
                <Link
                  href={`/${s}`}
                  aria-current={s === slug ? "page" : undefined}
                  className={`block rounded-lg px-3 py-1.5 text-sm ${
                    s === slug
                      ? "bg-emerald-500/10 text-emerald-300"
                      : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
                  }`}
                >
                  {nav[s].title}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <article className="max-w-3xl">
          <h1 className="text-3xl font-extrabold tracking-tight">{doc.title}</h1>
          <p className="mt-2 text-xs text-neutral-500">
            {t("legal.updated", { date: date(LEGAL_UPDATED_AT) })}
          </p>
          {doc.intro && <p className="mt-4 text-neutral-300">{withMailto(doc.intro)}</p>}
          <div className="mt-8 space-y-8">
            {doc.sections.map((s) => (
              <section key={s.h} id={s.id} className="scroll-mt-20">
                <h2 className="text-lg font-semibold text-neutral-100">{s.h}</h2>
                <div className="mt-2 space-y-2 text-sm leading-relaxed text-neutral-300">
                  {s.p.map((para, i) => (
                    <p key={i}>{withMailto(para)}</p>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </article>
      </div>
    </main>
  );
}
