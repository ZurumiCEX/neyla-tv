"use client";

// Héros de l'accueil : met en avant les lives les plus regardés de la plateforme
// (lecture HLS Bunny, sans son), avec une liste pour changer de chaîne.
// Sans live en cours : bannière d'accueil statique.

import { useEffect, useState } from "react";
import Link from "next/link";
import { HlsPlayer } from "@/components/HlsPlayer";
import type { LiveChannel } from "@/components/LiveCard";
import { useFormat } from "@/lib/use-format";
import { useT } from "@/lib/i18n";

const ROTATE_MS = 45_000;

export function FeaturedLiveHero({ lives }: { lives: LiveChannel[] }) {
  const t = useT();
  const { num } = useFormat();
  const featured = lives.filter((c) => c.is_live && c.playback_url).slice(0, 5);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const count = featured.length;

  useEffect(() => {
    if (paused || count <= 1) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % count), ROTATE_MS);
    return () => clearInterval(id);
  }, [paused, count]);

  if (count === 0) {
    return (
      <section className="mb-10 overflow-hidden rounded-2xl border border-secondary/30 bg-gradient-to-br from-secondary/15 via-neutral-900 to-neutral-950 p-8 sm:p-12">
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">{t("home.heroTitle")}</h1>
        <p className="mt-3 max-w-xl text-neutral-300">{t("home.heroSubtitle")}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/parcourir"
            className="rounded-lg bg-secondary px-4 py-2 font-semibold text-neutral-950 hover:bg-secondary-light"
          >
            {t("home.heroBrowse")}
          </Link>
          <Link
            href="/become-streamer"
            className="rounded-lg border border-neutral-700 px-4 py-2 font-semibold text-neutral-200 hover:border-secondary"
          >
            {t("home.heroBecome")}
          </Link>
        </div>
      </section>
    );
  }

  const current = featured[Math.min(index, count - 1)];
  const name = current.streamer.display_name || `@${current.slug}`;

  return (
    <section
      className="mb-10 grid gap-4 lg:grid-cols-[1fr_300px]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-roledescription="carousel"
    >
      <div className="relative">
        <HlsPlayer
          key={current.slug}
          src={current.playback_url ?? ""}
          poster={current.thumbnail_url}
          controls={false}
        />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 rounded-b-xl bg-gradient-to-t from-black/90 via-black/40 to-transparent p-5">
          <span className="inline-flex items-center gap-1.5 rounded bg-secondary px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-neutral-950">
            {t("live.badge.on")}
          </span>
          <p className="mt-2 line-clamp-1 text-lg font-bold text-white">
            {current.title || t("card.untitled")}
          </p>
          <p className="text-sm text-neutral-300">
            {name}
            {current.category && ` · ${current.category.name}`}
            {typeof current.viewers === "number" &&
              ` · ${t("card.viewers", { n: num(current.viewers) })}`}
          </p>
        </div>
        <Link
          href={`/c/${current.slug}`}
          className="absolute right-4 top-4 rounded-lg bg-secondary px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-secondary-light"
        >
          {t("home.watchLive")}
        </Link>
      </div>

      <ol className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {featured.map((c, i) => (
          <li key={c.slug} className="min-w-[220px] lg:min-w-0">
            <button
              type="button"
              onClick={() => setIndex(i)}
              aria-current={i === index}
              className={`flex w-full items-center gap-3 rounded-xl border p-2 text-left transition ${
                i === index
                  ? "border-secondary bg-secondary/10"
                  : "border-neutral-800 bg-neutral-900/60 hover:border-neutral-700"
              }`}
            >
              {c.thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={c.thumbnail_url} alt="" className="h-12 w-20 shrink-0 rounded object-cover" />
              ) : (
                <span className="h-12 w-20 shrink-0 rounded bg-neutral-800" />
              )}
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-neutral-100">
                  {c.streamer.display_name || `@${c.slug}`}
                </span>
                <span className="block truncate text-xs text-neutral-400">
                  {c.category?.name ?? c.title}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
