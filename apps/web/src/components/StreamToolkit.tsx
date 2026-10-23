"use client";

// Outils de diffusion du dashboard : test de connexion Bunny, réglages OBS
// recommandés selon la connexion, widgets OBS (alertes, chat, objectif) et
// configuration de l'objectif.

import { useState } from "react";
import { CopyButton } from "@/components/CopyButton";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type Health = {
  provider: string;
  mode: "fake" | "live";
  is_live: boolean;
  reachable: boolean;
  checked_at: string | null;
};

type Goal = { goal_title: string; goal_kind: "subs" | "tips"; goal_target: number };

// Réglages OBS (sortie « Avancé ») adaptés aux connexions courantes en Afrique de l'Ouest.
const PRESETS = [
  { key: "mobile", resolution: "854×480", fps: 30, video: 1200, audio: 96 },
  { key: "adsl", resolution: "1280×720", fps: 30, video: 2500, audio: 128 },
  { key: "fiber", resolution: "1920×1080", fps: 60, video: 6000, audio: 160 },
] as const;

export function StreamToolkit({
  overlayToken,
  origin,
  goal,
  onGoalSaved,
}: {
  overlayToken: string;
  origin: string;
  goal: Goal;
  onGoalSaved: () => void;
}) {
  const t = useT();
  const { time } = useFormat();
  const { authFetch } = useAuth();
  const [health, setHealth] = useState<Health | null>(null);
  const [testing, setTesting] = useState(false);
  const [title, setTitle] = useState(goal.goal_title);
  const [kind, setKind] = useState(goal.goal_kind);
  const [target, setTarget] = useState(String(goal.goal_target || ""));
  const [goalState, setGoalState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  async function testConnection() {
    setTesting(true);
    try {
      setHealth(await authFetch<Health>("/api/channels/me/stream-health"));
    } catch {
      setHealth(null);
    } finally {
      setTesting(false);
    }
  }

  async function saveGoal() {
    setGoalState("saving");
    try {
      await authFetch("/api/channels/me", {
        method: "PATCH",
        body: JSON.stringify({
          goal_title: title.trim(),
          goal_kind: kind,
          goal_target: Math.max(0, parseInt(target, 10) || 0),
        }),
      });
      setGoalState("saved");
      onGoalSaved();
    } catch {
      setGoalState("error");
    }
  }

  const widgets = [
    { key: "alerts", path: "" },
    { key: "chat", path: "/chat" },
    { key: "goal", path: "/goal" },
  ];

  return (
    <div className="space-y-6 border-t border-neutral-800 pt-5">
      {/* Santé du flux */}
      <section>
        <div className="flex flex-wrap items-center gap-3">
          <p className="font-semibold text-neutral-100">{t("tool.healthTitle")}</p>
          <button
            type="button"
            onClick={testConnection}
            disabled={testing}
            className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-secondary disabled:opacity-50"
          >
            {testing ? t("tool.testing") : t("tool.test")}
          </button>
        </div>
        {health && (
          <ul className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <HealthCell
              label={t("tool.provider")}
              value={health.mode === "fake" ? t("tool.modeFake") : "Bunny Stream"}
              ok={health.mode === "live"}
            />
            <HealthCell
              label={t("tool.api")}
              value={health.reachable ? t("tool.reachable") : t("tool.unreachable")}
              ok={health.reachable}
            />
            <HealthCell
              label={t("tool.signal")}
              value={health.is_live ? t("live.badge.on") : t("tool.noSignal")}
              ok={health.is_live}
            />
            <HealthCell
              label={t("tool.checked")}
              value={health.checked_at ? time(health.checked_at) : "—"}
              ok
            />
          </ul>
        )}
        <p className="mt-2 text-xs text-neutral-500">{t("tool.healthHint")}</p>
      </section>

      {/* Réglages OBS recommandés */}
      <section>
        <p className="font-semibold text-neutral-100">{t("tool.presetsTitle")}</p>
        <p className="text-xs text-neutral-400">{t("tool.presetsDesc")}</p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {PRESETS.map((p) => (
            <div
              key={p.key}
              className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3 text-sm"
            >
              <p className="font-semibold text-neutral-100">{t(`tool.preset.${p.key}`)}</p>
              <dl className="mt-2 grid grid-cols-2 gap-y-1 text-xs">
                <dt className="text-neutral-500">{t("tool.resolution")}</dt>
                <dd className="text-neutral-200">
                  {p.resolution} · {p.fps} fps
                </dd>
                <dt className="text-neutral-500">{t("tool.videoBitrate")}</dt>
                <dd className="text-neutral-200">{p.video} kbps</dd>
                <dt className="text-neutral-500">{t("tool.audioBitrate")}</dt>
                <dd className="text-neutral-200">{p.audio} kbps</dd>
                <dt className="text-neutral-500">{t("tool.keyframe")}</dt>
                <dd className="text-neutral-200">2 s</dd>
              </dl>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-neutral-500">{t("tool.latencyNote")}</p>
      </section>

      {/* Widgets OBS */}
      <section>
        <p className="font-semibold text-neutral-100">{t("tool.widgetsTitle")}</p>
        <p className="text-xs text-neutral-400">{t("tool.widgetsDesc")}</p>
        <ul className="mt-3 space-y-2">
          {widgets.map((w) => {
            const url = origin && overlayToken ? `${origin}/overlay/${overlayToken}${w.path}` : "";
            return (
              <li
                key={w.key}
                className="flex flex-wrap items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-900/40 p-2 text-sm"
              >
                <span className="w-28 shrink-0 font-semibold text-neutral-200">
                  {t(`tool.widget.${w.key}`)}
                </span>
                <code className="min-w-0 flex-1 truncate text-xs text-emerald-300">
                  {url || "…"}
                </code>
                {url && (
                  <>
                    <CopyButton value={url} />
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-300 hover:border-secondary"
                    >
                      {t("tool.preview")}
                    </a>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      {/* Objectif */}
      <section className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
        <p className="font-semibold text-neutral-100">{t("tool.goalTitle")}</p>
        <p className="text-xs text-neutral-400">{t("tool.goalDesc")}</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={80}
            placeholder={t("tool.goalPlaceholder")}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-secondary-light"
          />
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as Goal["goal_kind"])}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-secondary-light"
          >
            <option value="subs">{t("tool.goalSubs")}</option>
            <option value="tips">{t("tool.goalTips")}</option>
          </select>
          <input
            type="number"
            min={0}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="100"
            aria-label={t("tool.goalTarget")}
            className="w-28 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-secondary-light"
          />
          <button
            type="button"
            onClick={saveGoal}
            disabled={goalState === "saving"}
            className="rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-secondary-light disabled:opacity-50"
          >
            {t("tool.goalSave")}
          </button>
        </div>
        {goalState === "saved" && (
          <p className="mt-2 text-xs text-emerald-400">{t("tool.goalSaved")}</p>
        )}
        {goalState === "error" && (
          <p className="mt-2 text-xs text-red-300">{t("tool.goalError")}</p>
        )}
      </section>
    </div>
  );
}

function HealthCell({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <li className="rounded-lg border border-neutral-800 bg-neutral-900/40 p-2">
      <p className="text-[10px] uppercase tracking-wider text-neutral-500">{label}</p>
      <p className={`mt-0.5 font-semibold ${ok ? "text-emerald-300" : "text-amber-300"}`}>
        {value}
      </p>
    </li>
  );
}
