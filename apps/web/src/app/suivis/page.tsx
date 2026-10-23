"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GameCard, type GameSummary } from "@/components/GameCard";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { useAuth } from "@/lib/auth-context";
import { onFollowsChanged } from "@/lib/follow-events";
import { useT } from "@/lib/i18n";

type FollowedChannel = LiveChannel & { last_live_started_at?: string | null };

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
  const [follows, setFollows] = useState<FollowedChannel[] | null>(null);
  const [subs, setSubs] = useState<MySub[] | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  const loadFollows = useCallback(() => {
    authFetch<{ results: FollowedChannel[] }>("/api/follows/me")
      .then((d) => setFollows(d.results))
      .catch(() => setFollows((prev) => prev ?? []));
  }, [authFetch]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    loadFollows();
    authFetch<{ results: MySub[] }>("/api/subscriptions/me")
      .then((d) => setSubs(d.results))
      .catch(() => setSubs([]));
    // Les chaînes suivies passent live/hors ligne : rafraîchissement régulier.
    const off = onFollowsChanged(loadFollows);
    const id = setInterval(loadFollows, 60_000);
    return () => {
      off();
      clearInterval(id);
    };
  }, [loading, user, authFetch, router, loadFollows]);

  const live = useMemo(() => (follows ?? []).filter((c) => c.is_live), [follows]);
  // Toutes les chaînes suivies : en direct d'abord, puis les plus récemment actives.
  const allChannels = useMemo(
    () =>
      [...(follows ?? [])].sort((a, b) => {
        if (a.is_live !== b.is_live) return Number(b.is_live) - Number(a.is_live);
        return (b.last_live_started_at ?? "").localeCompare(a.last_live_started_at ?? "");
      }),
    [follows],
  );
  const offline = useMemo(() => allChannels.filter((c) => !c.is_live), [allChannels]);

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
    <main className="w-full px-4 py-6">
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
          {offline.length > 0 && (
            <section>
              <h2 className="mb-4 text-lg font-bold">{t("suivis.offline")}</h2>
              <Grid>
                {offline.map((c) => (
                  <LiveCard key={c.slug} channel={c} />
                ))}
              </Grid>
            </section>
          )}
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
          <Empty text={t("suivis.emptyCategories")} />
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
            {allChannels.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </Grid>
        ))}

      {tab === "subs" && (
        <p className="mb-4 text-sm text-neutral-400">
          <Link href="/abonnements" className="text-emerald-300 underline">
            {t("suivis.manageSubs")}
          </Link>
        </p>
      )}
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
                {s.tier_name && <p className="mt-1 text-xs text-secondary-light">{s.tier_name}</p>}
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
        <span className="inline-block h-2.5 w-2.5 rounded-[2px] bg-secondary" />
        {title}
      </h2>
      {items.length === 0 ? <Empty text={empty} /> : children}
    </section>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-neutral-500">{text}</p>;
}
