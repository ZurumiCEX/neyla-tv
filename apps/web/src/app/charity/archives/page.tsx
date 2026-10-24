import type { Metadata } from "next";
import Link from "next/link";
import { HeartHandshake } from "lucide-react";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

export const metadata: Metadata = { title: "Archives Charity Day — Neyla TV" };

type CharityEvent = {
  slug: string;
  title: string;
  theme: string;
  cover_url: string;
  starts_at: string;
  ends_at: string;
  is_open: boolean;
  total_aura_cached: number;
  beneficiaries: { slug: string; name: string }[];
};
type Charity = { slug: string; name: string; description: string; country: string; logo_url: string; website_url: string };

/** Tous les Charity Days publiés + associations partenaires (transparence). */
export default async function CharityArchivesPage() {
  const t = await getServerT();
  const [events, charities] = await Promise.all([
    apiFetchServer<{ results: CharityEvent[] }>("/api/charity/events").catch(() => ({ results: [] })),
    apiFetchServer<{ results: Charity[] }>("/api/charity/charities").catch(() => ({ results: [] })),
  ]);
  const date = (iso: string) =>
    new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  return (
    <main className="mx-auto max-w-5xl space-y-8 p-4 sm:p-8">
      <div>
        <Link href="/charity" className="text-sm text-neutral-400 hover:text-emerald-300">
          ← {t("charity.archives.back")}
        </Link>
        <h1 className="mt-2 text-2xl font-bold">{t("charity.archives.title")}</h1>
        <p className="text-sm text-neutral-400">{t("charity.archives.desc")}</p>
      </div>

      <section>
        {events.results.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("charity.archives.none")}</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {events.results.map((e) => (
              <li key={e.slug}>
                <Link
                  href={`/charity/${e.slug}`}
                  className="block overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/60 hover:border-emerald-500/60"
                >
                  {e.cover_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={e.cover_url} alt="" className="aspect-[3/1] w-full object-cover" />
                  )}
                  <div className="p-4">
                    <p className="text-xs text-neutral-500">
                      {date(e.starts_at)}
                      {e.is_open ? ` · ${t("charity.archives.open")}` : ""}
                    </p>
                    <p className="mt-1 font-bold">{e.title}</p>
                    {e.theme && <p className="text-sm text-neutral-400">{e.theme}</p>}
                    <p className="mt-2 text-sm font-semibold text-emerald-300">
                      {e.total_aura_cached.toLocaleString("fr-FR")} Aura
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
          <HeartHandshake size={20} className="text-emerald-400" aria-hidden />
          {t("charity.archives.partners")}
        </h2>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {charities.results.map((c) => (
            <li key={c.slug} className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
              <p className="font-bold">
                {c.name} <span className="text-xs font-normal text-neutral-500">{c.country}</span>
              </p>
              <p className="mt-1 line-clamp-3 text-sm text-neutral-400">{c.description}</p>
              {c.website_url && (
                <a
                  href={c.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-xs font-semibold text-emerald-300 hover:underline"
                >
                  {t("charity.archives.website")}
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
