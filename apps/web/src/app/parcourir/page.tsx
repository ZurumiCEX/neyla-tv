import type { Metadata } from "next";
import { apiFetchServer } from "@/lib/api";
import type { LiveChannel } from "@/components/LiveCard";
import { getServerT } from "@/lib/i18n-server";
import { BrowseTabs, type Category, type Group } from "./BrowseTabs";

export const metadata: Metadata = { title: "Parcourir — Neyla TV" };

type LiveListResp = { results: LiveChannel[]; total: number };
type CategoryListResp = { results: Category[] };
type GroupListResp = { results: Group[] };

async function safeFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    return await apiFetchServer<T>(path);
  } catch {
    return fallback;
  }
}

export default async function BrowsePage() {
  const [t, [lives, cats, groups]] = await Promise.all([
    getServerT(),
    Promise.all([
      safeFetch<LiveListResp>("/api/discover/live?limit=48", { results: [], total: 0 }),
      safeFetch<CategoryListResp>("/api/discover/categories?limit=48", { results: [] }),
      safeFetch<GroupListResp>("/api/discover/groups", { results: [] }),
    ]),
  ]);

  return (
    <main className="w-full px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">{t("nav.browse")}</h1>
      <BrowseTabs lives={lives.results} categories={cats.results} groups={groups.results} />
    </main>
  );
}
