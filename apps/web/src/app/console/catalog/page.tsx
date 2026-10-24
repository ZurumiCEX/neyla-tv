"use client";

import { useEffect, useState } from "react";
import { ImageUpload } from "@/components/ImageUpload";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type Game = { slug: string; name: string; box_art_url: string; group: string };

/** Catalogue : jaquettes des catégories (POST /api/uploads/game/<slug>, admin). */
export default function AdminCatalogPage() {
  const t = useT();
  const [games, setGames] = useState<Game[] | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    apiFetch<{ results: Game[] }>("/api/discover/categories?limit=100")
      .then((d) => setGames(d.results))
      .catch(() => setGames([]));
  }, []);

  if (!games) return <p className="text-neutral-500">{t("common.loading")}</p>;
  const shown = games.filter((g) => g.name.toLowerCase().includes(filter.toLowerCase()));
  return (
    <div className="space-y-4">
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder={t("admin.catalog.search")}
        className="w-full max-w-sm rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-400"
      />
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((g) => (
          <li key={g.slug} className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
            <p className="font-semibold">{g.name}</p>
            <p className="mb-2 text-xs text-neutral-500">
              {g.slug} · {t(`browse.groups.${g.group}`)}
            </p>
            <ImageUpload
              label={t("admin.catalog.boxArt")}
              currentUrl={g.box_art_url}
              uploadPath={`/api/uploads/game/${g.slug}`}
              onUploaded={(url) =>
                setGames((list) => list?.map((x) => (x.slug === g.slug ? { ...x, box_art_url: url } : x)) ?? null)
              }
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
