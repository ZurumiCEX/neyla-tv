"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type SearchResp = {
  channels: LiveChannel[];
  games: { slug: string; name: string }[];
};

export function SearchView() {
  const t = useT();
  const params = useSearchParams();
  const router = useRouter();
  const initial = params.get("q") ?? "";
  const [q, setQ] = useState(initial);
  const [result, setResult] = useState<SearchResp | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const trimmed = q.trim();
    if (trimmed.length < 2) {
      setResult({ channels: [], games: [] });
      return;
    }
    setBusy(true);
    const id = setTimeout(() => {
      apiFetch<SearchResp>(`/api/discover/search?q=${encodeURIComponent(trimmed)}`)
        .then(setResult)
        .catch(() => setResult({ channels: [], games: [] }))
        .finally(() => setBusy(false));
    }, 300);
    return () => clearTimeout(id);
  }, [q]);

  useEffect(() => {
    const trimmed = q.trim();
    const url = trimmed ? `/search?q=${encodeURIComponent(trimmed)}` : "/search";
    router.replace(url);
  }, [q, router]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-2xl font-bold">{t("search.title")}</h1>
      <input
        autoFocus
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("search.placeholder")}
        className="mt-4 w-full rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-neutral-100 outline-none focus:border-secondary-light"
      />

      {busy && <p className="mt-4 text-xs text-neutral-500">{t("search.searching")}</p>}

      {result && q.trim().length >= 2 && (
        <>
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">{t("search.channels")}</h2>
            {result.channels.length === 0 ? (
              <p className="text-sm text-neutral-500">{t("search.noResult")}</p>
            ) : (
              <div className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {result.channels.map((c) => (
                  <LiveCard key={c.slug} channel={c} />
                ))}
              </div>
            )}
          </section>

          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold">{t("search.games")}</h2>
            {result.games.length === 0 ? (
              <p className="text-sm text-neutral-500">{t("search.noResult")}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {result.games.map((g) => (
                  <Link
                    key={g.slug}
                    href={`/categories/${g.slug}`}
                    className="rounded-full border border-neutral-700 px-3 py-1 text-sm hover:border-emerald-500"
                  >
                    {g.name}
                  </Link>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}
