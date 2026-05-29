"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Achievement = {
  key: string;
  name: string;
  description: string;
  icon: string;
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
            <span className="text-3xl">{a.unlocked ? a.icon : "🔒"}</span>
            <div>
              <p className="font-semibold">{a.name}</p>
              <p className="text-xs text-neutral-400">{a.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
