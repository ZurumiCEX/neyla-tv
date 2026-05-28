"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { GameCard, type GameSummary } from "@/components/GameCard";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type MySub = {
  channel: LiveChannel;
  tier_name: string | null;
  status: string;
  current_period_end: string;
};
type Tab = "overview" | "live" | "categories" | "channels" | "subs";

export default function SuivisPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [follows, setFollows] = useState<LiveChannel[] | null>(null);
  const [subs, setSubs] = useState<MySub[] | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    authFetch<{ results: LiveChannel[] }>("/api/follows/me")
      .then((d) => setFollows(d.results))
      .catch(() => setFollows([]));
    authFetch<{ results: MySub[] }>("/api/subscriptions/me")
      .then((d) => setSubs(d.results))
      .catch(() => setSubs([]));
  }, [loading, user, authFetch, router]);

  const live = useMemo(() => (follows ?? []).filter((c) => c.is_live), [follows]);

  const categories = useMemo<GameSummary[]>(() => {
    const map = new Map<string, GameSummary>();
    for (const c of follows ?? []) {
      if (!c.category) continue;
      const existing = map.get(c.category.slug);
      if (existing) {
        existing.live_count = (existing.live_count ?? 0) + (c.is_live ? 1 : 0);
      } else {
        map.set(c.category.slug, {
          slug: c.category.slug,
          name: c.category.name,
          live_count: c.is_live ? 1 : 0,
        });
      }
    }
    return [...map.values()];
  }, [follows]);

  if (loading || follows === null)
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "overview", label: t("suivis.tab.overview") },
    { id: "live", label: t("suivis.tab.live"), count: live.length },
    { id: "categories", label: t("suivis.tab.categories"), count: categories.length },
    { id: "channels", label: t("suivis.tab.channels"), count: follows.length },
    { id: "subs", label: t("suivis.tab.subs"), count: subs?.length },
  ];

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">{t("suivis.title")}</h1>

      <div className="mb-6 flex flex-wrap gap-1 border-b border-neutral-800">
        {tabs.map((tb) => (
          <button
            key={tb.id}
            type="button"
            onClick={() => setTab(tb.id)}
            className={`-mb-px flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === tb.id
                ? "border-emerald-500 text-emerald-300"
                : "border-transparent text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tb.label}
            {typeof tb.count === "number" && (
              <span className="rounded-full bg-neutral-800 px-1.5 py-0.5 text-xs text-neutral-400">
                {tb.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-10">
          <Section title={t("suivis.liveNow")} empty={t("suivis.emptyLive")} items={live}>
            <Grid>
              {live.map((c) => (
                <LiveCard key={c.slug} channel={c} />
              ))}
            </Grid>
          </Section>
          {categories.length > 0 && (
            <section>
              <h2 className="mb-4 text-lg font-bold">{t("suivis.tab.categories")}</h2>
              <CatGrid>
                {categories.map((g) => (
                  <GameCard key={g.slug} game={g} />
                ))}
              </CatGrid>
            </section>
          )}
        </div>
      )}

      {tab === "live" &&
        (live.length === 0 ? (
          <Empty text={t("suivis.emptyLive")} />
        ) : (
          <Grid>
            {live.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </Grid>
        ))}

      {tab === "categories" &&
        (categories.length === 0 ? (
          <Empty text={t("suivis.emptyFollows")} />
        ) : (
          <CatGrid>
            {categories.map((g) => (
              <GameCard key={g.slug} game={g} />
            ))}
          </CatGrid>
        ))}

      {tab === "channels" &&
        (follows.length === 0 ? (
          <Empty text={t("suivis.emptyFollows")} />
        ) : (
          <Grid>
            {follows.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </Grid>
        ))}

      {tab === "subs" &&
        (subs === null ? (
          <Empty text={t("common.loading")} />
        ) : subs.length === 0 ? (
          <Empty text={t("suivis.emptySubs")} />
        ) : (
          <Grid>
            {subs.map((s) => (
              <div key={s.channel.slug}>
                <LiveCard channel={s.channel} />
                {s.tier_name && (
                  <p className="mt-1 text-xs text-fuchsia-300">{s.tier_name}</p>
                )}
              </div>
            ))}
          </Grid>
        ))}
    </main>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {children}
    </div>
  );
}

function CatGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {children}
    </div>
  );
}

function Section({
  title,
  empty,
  items,
  children,
}: {
  title: string;
  empty: string;
  items: unknown[];
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
        {title}
      </h2>
      {items.length === 0 ? <Empty text={empty} /> : children}
    </section>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-neutral-500">{text}</p>;
}
