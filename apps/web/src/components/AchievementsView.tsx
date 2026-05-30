"use client";

import { useEffect, useState } from "react";
import { AchievementIcon } from "@/components/AchievementIcon";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Achievement = {
  key: string;
  name: string;
  description: string;
  criteria?: string;
  icon: string;
  icon_url?: string;
  unlocked: boolean;
  awarded_at: string | null;
};

type Resp = { results: Achievement[]; unlocked: number; total: number };

export function AchievementsView() {
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [data, setData] = useState<Resp | null>(null);

  useEffect(() => {
    if (loading || !user) return;
    authFetch<Resp>("/api/achievements")
      .then(setData)
      .catch(() => undefined);
  }, [loading, user, authFetch]);

  return (
    <div>
      <p className="mb-6 text-sm text-neutral-400">
        {data
          ? t("ach.progress", { unlocked: data.unlocked, total: data.total })
          : t("common.loading")}
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {data?.results.map((a) => (
          <div
            key={a.key}
            className={`flex items-center gap-3 rounded-xl border p-4 ${
              a.unlocked
                ? "border-emerald-500/40 bg-emerald-500/5"
                : "border-neutral-800 bg-neutral-900/40 opacity-60"
            }`}
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center">
              {a.unlocked ? (
                <AchievementIcon achievement={a} size={32} />
              ) : (
                <span className="text-3xl">🔒</span>
              )}
            </span>
            <div className="min-w-0">
              <p className="font-semibold">{a.name}</p>
              {a.description && <p className="text-xs text-neutral-400">{a.description}</p>}
              {a.criteria && <p className="mt-0.5 text-xs text-neutral-500">🎯 {a.criteria}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
