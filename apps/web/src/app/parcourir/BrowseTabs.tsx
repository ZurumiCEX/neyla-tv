"use client";

import { useMemo, useState } from "react";
import { Emoji } from "@/components/Emoji";
import { GameCard, type GameSummary } from "@/components/GameCard";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { useT } from "@/lib/i18n";

export type Category = GameSummary;
/** Macro-catégorie avec compteurs (GET /api/discover/groups). */
export type Group = { slug: string; name: string; category_count: number; live_count: number };

const GROUPS: { slug: string; key: string; emoji: string }[] = [
  { slug: "", key: "browse.groups.all", emoji: "✨" },
  { slug: "games", key: "browse.groups.games", emoji: "🎮" },
  { slug: "irl", key: "browse.groups.irl", emoji: "🌍" },
  { slug: "chatting", key: "browse.groups.chatting", emoji: "💬" },
  { slug: "music", key: "browse.groups.music", emoji: "🎧" },
  { slug: "creative", key: "browse.groups.creative", emoji: "🎨" },
];

export function BrowseTabs({
  lives,
  categories,
  groups = [],
}: {
  lives: LiveChannel[];
  categories: Category[];
  groups?: Group[];
}) {
  const t = useT();
  const [tab, setTab] = useState<"live" | "categories">("live");
  const [group, setGroup] = useState<string>("");

  const filteredCategories = useMemo(
    () => (group ? categories.filter((c) => c.group === group) : categories),
    [categories, group],
  );
  const filteredLives = useMemo(
    () => (group ? lives.filter((c) => c.category?.group === group) : lives),
    [lives, group],
  );
  const counts = useMemo(() => {
    const byGroup = Object.fromEntries(groups.map((g) => [g.slug, g]));
    const total = groups.reduce(
      (acc, g) => ({ live: acc.live + g.live_count, cats: acc.cats + g.category_count }),
      { live: 0, cats: 0 },
    );
    return (slug: string) => {
      if (!groups.length) return null;
      if (!slug) return tab === "live" ? total.live : total.cats;
      const g = byGroup[slug];
      return g ? (tab === "live" ? g.live_count : g.category_count) : 0;
    };
  }, [groups, tab]);

  return (
    <>
      <div className="mb-6 flex gap-1 border-b border-neutral-800">
        <TabButton active={tab === "live"} onClick={() => setTab("live")}>
          {t("browse.liveTab")}
        </TabButton>
        <TabButton active={tab === "categories"} onClick={() => setTab("categories")}>
          {t("browse.categoriesTab")}
        </TabButton>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        {GROUPS.map((g) => (
          <button
            key={g.slug || "all"}
            type="button"
            onClick={() => setGroup(g.slug)}
            className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition ${
              group === g.slug
                ? "border-secondary bg-secondary/15 text-secondary-light"
                : "border-neutral-800 bg-neutral-900 text-neutral-300 hover:border-neutral-700 hover:text-neutral-100"
            }`}
          >
            <Emoji emoji={g.emoji} size={18} />
            {t(g.key)}
            {counts(g.slug) !== null && (
              <span className="rounded-full bg-neutral-800 px-1.5 text-xs tabular-nums text-neutral-400">
                {counts(g.slug)}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === "live" ? (
        filteredLives.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("browse.noLive")}</p>
        ) : (
          <div className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredLives.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </div>
        )
      ) : filteredCategories.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("browse.noCategory")}</p>
      ) : (
        <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {filteredCategories.map((g) => (
            <GameCard key={g.slug} game={g} />
          ))}
        </div>
      )}
    </>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${
        active
          ? "border-emerald-500 text-emerald-300"
          : "border-transparent text-neutral-400 hover:text-neutral-200"
      }`}
    >
      {children}
    </button>
  );
}
