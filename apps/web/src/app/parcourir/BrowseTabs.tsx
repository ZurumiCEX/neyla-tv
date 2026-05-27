"use client";

import { useState } from "react";
import Link from "next/link";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";

export type Category = { slug: string; name: string; live_count: number };

export function BrowseTabs({
  lives,
  categories,
}: {
  lives: LiveChannel[];
  categories: Category[];
}) {
  const [tab, setTab] = useState<"live" | "categories">("live");

  return (
    <>
      <div className="mb-6 flex gap-1 border-b border-neutral-800">
        <TabButton active={tab === "live"} onClick={() => setTab("live")}>
          Diffusions en direct
        </TabButton>
        <TabButton active={tab === "categories"} onClick={() => setTab("categories")}>
          Catégories
        </TabButton>
      </div>

      {tab === "live" ? (
        lives.length === 0 ? (
          <p className="text-sm text-neutral-500">Aucun stream en direct pour le moment.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {lives.map((c) => (
              <LiveCard key={c.slug} channel={c} />
            ))}
          </div>
        )
      ) : categories.length === 0 ? (
        <p className="text-sm text-neutral-500">Aucune catégorie.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {categories.map((g) => (
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
