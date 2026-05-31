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
    <main className={tab === "overview" ? "" : "mx-auto max-w-3xl p-8"}>
      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-8">
        <h1 className="mb-4 text-2xl font-bold">{t("nav.myChannel")}</h1>
        <div className="mb-4 flex flex-wrap items-center gap-3 border-b border-neutral-800">
          <div className="flex flex-wrap gap-1">
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
            <Link
              href={`/c/${user.username}`}
              className="ml-auto mb-2 text-xs text-neutral-400 hover:text-secondary-light"
            >
              {t("mychan.openInNewTab")} ↗
            </Link>
          )}
        </div>
      </div>

      {tab === "overview" && (
        /* Affiche directement la page publique de la chaîne, embarquée. */
        <iframe
          src={`/c/${user.username}`}
          title={t("nav.myChannel")}
          className="block h-[calc(100vh-180px)] w-full border-0 bg-neutral-950"
        />
      )}

      {tab === "achievements" && <AchievementsView />}
      {tab === "messages" && <InboxView />}
    </main>
  );
}
