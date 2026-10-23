"use client";

// Widget OBS « objectif » : barre de progression vers l'objectif du streamer
// (nouveaux abonnés ou Aura reçue), rafraîchie toutes les 15 s.

import { use, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { fmt } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { useTransparentBody, type OverlayInfo } from "@/lib/overlay";

const POLL_MS = 15_000;

export default function GoalWidget({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const t = useT();
  const [goal, setGoal] = useState<OverlayInfo["goal"]>(null);
  useTransparentBody();

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      apiFetch<OverlayInfo>(`/api/overlay/${encodeURIComponent(token)}`)
        .then((d) => !cancelled && setGoal(d.goal))
        .catch(() => undefined);
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token]);

  if (!goal) return null;
  const pct = Math.min(100, Math.round((goal.current / Math.max(goal.target, 1)) * 100));
  const unit = goal.kind === "tips" ? "Aura" : t("overlay.goal.subs");

  return (
    <main className="fixed inset-0 flex items-end bg-transparent p-4">
      <div className="w-full rounded-2xl border border-[#FFC81E]/60 bg-black/75 p-4 shadow-2xl">
        <div className="mb-2 flex items-baseline justify-between gap-4 text-white">
          <p className="truncate text-lg font-bold">{goal.title || t("overlay.goal.default")}</p>
          <p className="shrink-0 font-mono text-lg">
            {fmt(goal.current)} / {fmt(goal.target)} {unit}
          </p>
        </div>
        <div className="h-4 overflow-hidden rounded-full bg-white/15">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#FFC81E] to-[#d946ef] transition-[width] duration-1000 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </main>
  );
}
