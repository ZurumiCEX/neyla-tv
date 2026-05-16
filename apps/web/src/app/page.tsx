import Link from "next/link";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";

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
  const [lives, cats] = await Promise.all([
    safeFetch<LiveListResp>("/api/discover/live?limit=12", {
      results: [],
      total: 0,
    }),
    safeFetch<CategoryListResp>("/api/discover/categories?limit=8", {
      results: [],
    }),
  ]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <section>
        <h1 className="text-2xl font-bold">En direct</h1>
        <p className="mt-1 text-sm text-neutral-400">
          {lives.total === 0
            ? "Aucun stream en cours pour le moment."
            : `${lives.total} chaîne(s) en live.`}
        </p>
        {lives.results.length > 0 && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {lives.results.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </div>
        )}
      </section>

      {cats.results.length > 0 && (
        <section className="mt-12">
          <h2 className="text-xl font-bold">Catégories populaires</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {cats.results.map((g) => (
              <Link
                key={g.slug}
                href={`/categories/${g.slug}`}
                className="rounded-lg border border-neutral-800 bg-neutral-900/60 px-4 py-3 text-sm transition hover:border-neutral-700"
              >
                <p className="font-semibold">{g.name}</p>
                <p className="mt-1 text-xs text-neutral-500">
                  {g.live_count} live{g.live_count > 1 ? "s" : ""}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
