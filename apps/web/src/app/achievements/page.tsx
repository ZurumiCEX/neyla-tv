"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AchievementsView } from "@/components/AchievementsView";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export default function AchievementsPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-1 text-2xl font-bold">{t("ach.title")}</h1>
      <AchievementsView />
    </main>
  );
}
