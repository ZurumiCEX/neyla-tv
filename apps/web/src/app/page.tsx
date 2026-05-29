import Link from "next/link";
import { GameCard, type GameSummary } from "@/components/GameCard";
import { HomeCarousel, type CarouselSlide } from "@/components/HomeCarousel";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type LiveListResp = { results: LiveChannel[]; total: number };
type CategoryListResp = { results: GameSummary[] };

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

  // Slideshow « mix auto » : on alterne lives en vedette et jeux populaires.
  const liveSlides: CarouselSlide[] = lives.results.slice(0, 6).map((c) => ({
    kind: "live",
    href: `/c/${c.slug}`,
    title: c.title || t("card.untitled"),
    subtitle: c.streamer.display_name || `@${c.slug}`,
    image: c.thumbnail_url,
    viewers: c.viewers,
    accent: "#ef4444",
  }));
  const catSlides: CarouselSlide[] = cats.results.slice(0, 6).map((g) => ({
    kind: "category",
    href: `/categories/${g.slug}`,
    title: g.name,
    subtitle: t("home.liveShort", { count: g.live_count ?? 0 }),
    image: g.box_art_url ?? "",
    viewers: g.viewers,
    accent: "#10b981",
  }));
  const slides: CarouselSlide[] = [];
  for (let i = 0; i < Math.max(liveSlides.length, catSlides.length); i++) {
    if (liveSlides[i]) slides.push(liveSlides[i]);
    if (catSlides[i]) slides.push(catSlides[i]);
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      {slides.length > 0 ? (
        <HomeCarousel slides={slides} />
      ) : (
        <section className="relative mb-10 overflow-hidden rounded-2xl border border-neutral-800 bg-gradient-to-br from-emerald-500/20 via-neutral-900 to-secondary/40 px-6 py-10 sm:px-10 sm:py-14">
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
              className="rounded-lg border border-secondary bg-secondary/10 px-5 py-2 text-sm font-semibold text-secondary-light hover:bg-secondary/20"
            >
              {t("home.heroBecome")}
            </Link>
          </div>
        </section>
      )}

      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="flex items-center gap-2 text-xl font-bold">
            <span className="inline-block h-2.5 w-2.5 rounded-[2px] bg-secondary" />
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
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {cats.results.map((g) => (
              <GameCard key={g.slug} game={g} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
