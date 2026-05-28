import Link from "next/link";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type LiveListResp = { results: LiveChannel[]; total: number };
type Category = { slug: string; name: string; live_count: number };
type CategoryListResp = { results: Category[] };

async function safeFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    return await apiFetchServer<T>(path);
  } catch {
    return fallback;
  }
}

export default async function HomePage() {
  const [t, [lives, cats]] = await Promise.all([
    getServerT(),
    Promise.all([
      safeFetch<LiveListResp>("/api/discover/live?limit=12", {
        results: [],
        total: 0,
      }),
      safeFetch<CategoryListResp>("/api/discover/categories?limit=8", {
        results: [],
      }),
    ]),
  ]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <section className="relative mb-10 overflow-hidden rounded-2xl border border-neutral-800 bg-gradient-to-br from-emerald-500/15 via-neutral-900 to-fuchsia-500/15 px-6 py-10 sm:px-10 sm:py-14">
        <h1 className="max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
          {t("home.heroTitle")}
        </h1>
        <p className="mt-3 max-w-xl text-sm text-neutral-300 sm:text-base">
          {t("home.heroSubtitle")}
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/parcourir"
            className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
          >
            {t("home.heroBrowse")}
          </Link>
          <Link
            href="/become-streamer"
            className="rounded-lg border border-neutral-700 px-5 py-2 text-sm font-semibold text-neutral-200 hover:border-neutral-500"
          >
            {t("home.heroBecome")}
          </Link>
        </div>
      </section>

      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="flex items-center gap-2 text-xl font-bold">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
            {t("home.live")}
          </h2>
          <span className="text-sm text-neutral-400">
            {lives.total === 0
              ? t("home.noLive")
              : t("home.liveCount", { total: lives.total })}
          </span>
        </div>
        {lives.results.length > 0 && (
          <div className="mt-5 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {lives.results.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </div>
        )}
      </section>

      {cats.results.length > 0 && (
        <section className="mt-12">
          <h2 className="text-xl font-bold">{t("home.popularCategories")}</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {cats.results.map((g) => (
              <Link
                key={g.slug}
                href={`/categories/${g.slug}`}
                className="rounded-lg border border-neutral-800 bg-neutral-900/60 px-4 py-3 text-sm transition hover:border-neutral-700"
              >
                <p className="font-semibold">{g.name}</p>
                <p className="mt-1 text-xs text-neutral-500">
                  {t("home.liveShort", { count: g.live_count })}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
