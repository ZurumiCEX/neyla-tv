"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AchievementsView } from "@/components/AchievementsView";
import { InboxView } from "@/components/InboxView";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Tab = "overview" | "achievements" | "messages";

export default function MaChainePage() {
  const router = useRouter();
  const t = useT();
  const { user, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: t("mychan.overview") },
    { id: "achievements", label: t("nav.achievements") },
    { id: "messages", label: t("nav.inbox") },
  ];

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-4 text-2xl font-bold">{t("nav.myChannel")}</h1>

      <div className="mb-6 flex flex-wrap gap-1 border-b border-neutral-800">
        {tabs.map((tb) => (
          <button
            key={tb.id}
            type="button"
            onClick={() => setTab(tb.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === tb.id
                ? "border-secondary text-secondary-light"
                : "border-transparent text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-3">
          <p className="text-sm text-neutral-400">{t("mychan.overviewDesc")}</p>
          <div className="flex flex-wrap gap-3">
            <Link
              href={`/c/${user.username}`}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
            >
              {t("mychan.viewPublic")}
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg border border-secondary bg-secondary/10 px-4 py-2 text-sm font-semibold text-secondary-light hover:bg-secondary/20"
            >
              {t("nav.dashboard")}
            </Link>
          </div>
        </div>
      )}

      {tab === "achievements" && <AchievementsView />}
      {tab === "messages" && <InboxView />}
    </main>
  );
}
