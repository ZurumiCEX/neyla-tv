import { GameCard, type GameSummary } from "@/components/GameCard";
import { HomeVideoCarousel, type HeroVideo } from "@/components/HomeVideoCarousel";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type LiveListResp = { results: LiveChannel[]; total: number };
type CategoryListResp = { results: GameSummary[] };

// Vidéos du diaporama d'accueil (lecture auto, son bas, rotation 5 min).
const HERO_VIDEOS: HeroVideo[] = [
  { id: "ySxy5BRVl48", start: 98 },
  { id: "gwIpCbZH494" },
];

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
    <main className="w-full px-4 py-6">
      <HomeVideoCarousel videos={HERO_VIDEOS} />

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
