"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";

export type GameSummary = {
  slug: string;
  name: string;
  box_art_url?: string;
  live_count?: number;
  viewers?: number;
};

export function GameCard({ game }: { game: GameSummary }) {
  const t = useT();
  const subtitle =
    typeof game.viewers === "number" && game.viewers > 0
      ? t("card.viewers", { n: game.viewers.toLocaleString("fr-FR") })
      : t("home.liveShort", { count: game.live_count ?? 0 });

  return (
    <Link href={`/categories/${game.slug}`} className="group block">
      <div className="aspect-[3/4] overflow-hidden rounded-lg bg-neutral-800 ring-emerald-500/0 transition group-hover:ring-2 group-hover:ring-emerald-500/60">
        {game.box_art_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={game.box_art_url} alt={game.name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center px-2 text-center text-xs text-neutral-500">
            {game.name}
          </div>
        )}
      </div>
      <p className="mt-2 line-clamp-1 text-sm font-semibold text-neutral-100 group-hover:text-emerald-300">
        {game.name}
      </p>
      <p className="text-xs text-neutral-400">{subtitle}</p>
    </Link>
  );
}
